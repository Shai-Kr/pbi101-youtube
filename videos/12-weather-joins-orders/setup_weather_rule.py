"""Video 12: a second rule in the Activator "AuroraOrdersWatch": rain started in a city (read-modify-write by REST).

  python -I setup_weather_rule.py test      run the source query once and print the last rows per city
  python -I setup_weather_rule.py apply     add (or rewrite) the weather source, the City object and the rule
  python -I setup_weather_rule.py stop      stop the rain rule (no alerts, nothing deleted); `start` runs it again
  python -I setup_weather_rule.py remove    take the weather entities out again
  python -I setup_weather_rule.py show      entity list

Source (every 60 s): per minute and city, Wet = 1 when any real reading of the last 30 minutes had RainRate >= 0.4 mm/h.
Looking back 30 minutes keeps a drizzle that flickers from firing again and again.
Rule "Rain started in a city": Wet becomes greater than 0. Action: the SAME custom action as video 11's rule
("Tell Aurora Watch"); its one field gets the city name. The flow writes the rain sentence when the key of the
object is not one of the four regions (setup_flow.py).
The video 11 entities are not touched: this script only adds or replaces entities whose names are in NAMES.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ["FABRIC_SKILL"] = "activator-cli"
sys.path.insert(0, str(HERE.parents[1] / "studio"))
import fabric_api as fa  # noqa: E402

RT = json.loads((Path.home() / ".pbi101" / "fabric_env.json").read_text(encoding="utf-8"))["realtime"]
F = fa.FABRIC + f"workspaces/{fa.WS}/reflexes/{RT['activator_id']}"
WORK = HERE / "work" / "activator_def"
KUSTO = "https://kusto.kusto.windows.net"

# fixed keys, so running `apply` twice rewrites the same entities
ID = {"src": "c1a70001-0000-4000-8000-000000000001", "ev": "c1a70001-0000-4000-8000-000000000002",
      "obj": "c1a70001-0000-4000-8000-000000000003", "idattr": "c1a70001-0000-4000-8000-000000000004",
      "split": "c1a70001-0000-4000-8000-000000000005", "wet": "c1a70001-0000-4000-8000-000000000006",
      "rate": "c1a70001-0000-4000-8000-000000000007", "name": "c1a70001-0000-4000-8000-000000000008",
      "rule": "c1a70001-0000-4000-8000-000000000009"}
STEP = "c1a70002-0000-4000-8000-0000000000"            # step ids: STEP + two digits
RULE = "Rain started in a city"

BODY = """let e = bin(endTime, 1m);
let s = bin(startTime, 1m) + 1m;
let r = WeatherLive
    | where IntervalMin == 15 and ReadingTime > s - 31m and ReadingTime <= e
    | project City, ReadingTime, RainRate, TempC;
range Minute from s to e step 1m
| extend k = 1
| join kind=inner (r | extend k = 1) on k
| where ReadingTime <= Minute and ReadingTime > Minute - 30m
| summarize RainMax30 = max(RainRate), arg_max(ReadingTime, RainRate, TempC) by Minute, City
| project Minute, City, Wet = iff(RainMax30 >= 0.4, 1, 0), RainRate, TempC
| order by Minute asc, City asc"""
QUERY = "declare query_parameters(startTime:datetime, endTime:datetime);\n" + BODY


def get() -> tuple[list, list]:
    s, b = fa.call("POST", F + "/getDefinition", {})
    if s >= 300:
        sys.exit(f"getDefinition {s} {json.dumps(b)[:400]}")
    parts = b["definition"]["parts"]
    ents = json.loads(base64.b64decode(next(p for p in parts if p["path"] == "ReflexEntities.json")["payload"]).decode("utf-8"))
    return parts, ents


def put(parts: list, ents: list):
    out = []
    for p in parts:
        if p["path"] == "ReflexEntities.json":
            p = {**p, "payload": base64.b64encode(json.dumps(ents).encode("utf-8")).decode()}
        if p["path"] != ".platform":
            out.append({"path": p["path"], "payload": p["payload"], "payloadType": "InlineBase64"})
    s, b = fa.call("POST", F + "/updateDefinition", {"definition": {"parts": out}})
    print("updateDefinition", s, "" if s < 300 else json.dumps(b)[:700])


def inst(o: dict) -> str:
    return json.dumps(o, separators=(",", ":"))


def ref(kind: str, eid: str, name: str) -> dict:
    return {"kind": kind, "type": "complex", "arguments": [{"name": "entityId", "type": "string", "value": eid}], "name": name}


def attribute(key: str, n: int, name: str, field: str, op: str, cont: str) -> dict:
    return {"uniqueIdentifier": ID[key], "type": "timeSeriesView-v1", "payload": {
        "name": name, "parentObject": {"targetUniqueIdentifier": ID["obj"]}, "parentContainer": {"targetUniqueIdentifier": cont},
        "definition": {"type": "Attribute", "instance": inst({"templateId": "BasicEventAttribute", "templateVersion": "1.2.4", "steps": [
            {"name": "EventSelectStep", "id": f"{STEP}{n:02d}", "rows": [
                {"name": "EventSelector", "kind": "Event", "arguments": [ref("EventReference", ID["split"], "event")]},
                {"name": "EventFieldSelector", "kind": "EventField", "arguments": [{"name": "fieldName", "type": "string", "value": field}]}]},
            {"name": "EventComputeStep", "id": f"{STEP}{n + 1:02d}", "rows": [
                {"name": "TypeAssertion", "kind": "TypeAssertion", "arguments": [{"name": "op", "type": "string", "value": op},
                                                                            {"name": "format", "type": "string", "value": ""}]}]}]})}}}


def entities(cont: str, sink: str, db_item: str) -> list:
    now = datetime.now(timezone.utc)
    fmt = "%m/%d/%Y %H:%M:%S"
    src = {"uniqueIdentifier": ID["src"], "type": "kqlSource-v1", "payload": {
        "name": "Rain per city, last 30 minutes", "runSettings": {"isStopped": False, "executionIntervalInSeconds": 60},
        "query": {"queryString": QUERY},
        "eventhouseItem": {"itemId": db_item, "workspaceId": fa.WS, "itemType": "KustoDatabase"},
        "eventTimeSettings": {"timeZone": "UTC", "ingestionDelayInSeconds": 20, "timeFieldName": "Minute"},
        "queryParameters": [{"name": "startTime", "type": "DURATION_START", "value": (now - timedelta(minutes=10)).strftime(fmt)},
                            {"name": "endTime", "type": "DURATION_END", "value": now.strftime(fmt)}],
        "metadata": {"workspaceId": fa.WS, "measureName": "", "querySetId": "", "queryId": ""},
        "parentContainer": {"targetUniqueIdentifier": cont}}}
    ev = {"uniqueIdentifier": ID["ev"], "type": "timeSeriesView-v1", "payload": {
        "name": "Rain per city events", "parentContainer": {"targetUniqueIdentifier": cont},
        "definition": {"type": "Event", "instance": inst({"templateId": "SourceEvent", "templateVersion": "1.2.4", "steps": [
            {"name": "SourceEventStep", "id": STEP + "01", "rows": [{"name": "SourceSelector", "kind": "SourceReference", "arguments": [
                {"name": "entityId", "type": "string", "value": ID["src"]}]}]}]})}}}
    obj = {"uniqueIdentifier": ID["obj"], "type": "timeSeriesView-v1", "payload": {
        "name": "City", "parentContainer": {"targetUniqueIdentifier": cont}, "definition": {"type": "Object"}}}
    idattr = {"uniqueIdentifier": ID["idattr"], "type": "timeSeriesView-v1", "payload": {
        "name": "City", "parentObject": {"targetUniqueIdentifier": ID["obj"]}, "parentContainer": {"targetUniqueIdentifier": cont},
        "definition": {"type": "Attribute", "instance": inst({"templateId": "IdentityPartAttribute", "templateVersion": "1.2.4", "steps": [
            {"name": "IdPartStep", "id": STEP + "02", "rows": [{"name": "TypeAssertion", "kind": "TypeAssertion", "arguments": [
                {"name": "op", "type": "string", "value": "Text"}, {"name": "format", "type": "string", "value": ""}]}]}]})}}}
    split = {"uniqueIdentifier": ID["split"], "type": "timeSeriesView-v1", "payload": {
        "name": "Weather per city", "parentObject": {"targetUniqueIdentifier": ID["obj"]}, "parentContainer": {"targetUniqueIdentifier": cont},
        "definition": {"type": "Event", "instance": inst({"templateId": "SplitEvent", "templateVersion": "1.2.4", "steps": [
            {"name": "SplitEventStep", "id": STEP + "03", "rows": [
                {"name": "EventSelector", "kind": "Event", "arguments": [ref("EventReference", ID["ev"], "event")]},
                {"name": "FieldIdMapping", "kind": "FieldIdMapping", "arguments": [
                    {"name": "fieldName", "type": "string", "value": "City"}, ref("AttributeReference", ID["idattr"], "idPart")]},
                {"name": "SplitEventOptions", "kind": "EventOptions", "arguments": [{"name": "isAuthoritative", "type": "boolean", "value": True}]}]}]})}}}
    rule = {"uniqueIdentifier": ID["rule"], "type": "timeSeriesView-v1", "payload": {
        "name": RULE, "description": "Created by: skills-for-fabric",
        "parentObject": {"targetUniqueIdentifier": ID["obj"]}, "parentContainer": {"targetUniqueIdentifier": cont},
        "definition": {"type": "Rule", "instance": inst({"templateId": "AttributeTrigger", "templateVersion": "1.3.1", "steps": [
            {"name": "ScalarSelectStep", "id": STEP + "10", "rows": [
                {"name": "AttributeSelector", "kind": "Attribute", "arguments": [ref("AttributeReference", ID["wet"], "attribute")]}]},
            {"name": "ScalarDetectStep", "id": STEP + "11", "rows": [
                {"name": "NumberBecomes", "kind": "NumberBecomes", "arguments": [
                    {"name": "op", "type": "string", "value": "BecomesGreaterThan"}, {"name": "value", "type": "number", "value": 0}]},
                {"arguments": [], "kind": "EachTime", "name": "OccurrenceOption"}]},
            {"name": "ActStep", "id": STEP + "12", "rows": [{"kind": "PowerAutomateFlow", "name": "PowerAutomateBinding", "type": "row", "arguments": [
                {"arguments": [{"name": "sinkId", "type": "string", "value": sink}], "kind": "SinkReference", "name": "sinkName", "type": "complex"},
                {"name": "inputFields", "type": "array", "values": [{"kind": "KeyValuePair", "type": "complex", "arguments": [
                    {"name": "key", "type": "string", "value": "Region"},
                    {"name": "value", "type": "complexArray", "values": [
                        {"name": "string", "type": "string", "value": "\u200b"},
                        {"arguments": [{"name": "entityId", "type": "string", "value": ID["name"]}], "kind": "AttributeReference",
                         "type": "complexReference"},
                        {"name": "string", "type": "string", "value": " "}]}]}]},
                {"name": "additionalInformation", "type": "array", "values": []}]}]}]}),
            "settings": {"shouldRun": True, "shouldApplyRuleOnUpdate": True}}}}
    return [src, ev, obj, idattr, split,
            attribute("wet", 20, "Wet in the last 30 minutes", "Wet", "Number", cont),
            attribute("rate", 30, "Rain rate (mm per hour)", "RainRate", "Number", cont),
            attribute("name", 40, "City name", "City", "Text", cont), rule]


def apply(remove_only=False):
    parts, ents = get()
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f"entities_{time.strftime('%H%M%S')}.json").write_text(json.dumps(ents), encoding="utf-8")
    mine = set(ID.values())
    keep = [e for e in ents if e["uniqueIdentifier"] not in mine]
    if not remove_only:
        cont = next(e for e in keep if e["type"] == "container-v1")["uniqueIdentifier"]
        sink = next(e for e in keep if e["type"] == "powerAutomateFlowAction-v1")["uniqueIdentifier"]
        db_item = next(e for e in keep if e["type"] == "kqlSource-v1")["payload"]["eventhouseItem"]["itemId"]
        keep += entities(cont, sink, db_item)
    put(parts, keep)
    show()


def run_rule(on: bool):
    """Stop or start the rain rule only. Stop it whenever no take is planned: every real rain start in one of the
    17 cities posts in Shai's Teams chat and costs Copilot credits."""
    parts, ents = get()
    rule = next(e for e in ents if e["uniqueIdentifier"] == ID["rule"])
    rule["payload"]["definition"]["settings"]["shouldRun"] = on
    put(parts, ents)
    show()


def show():
    _, ents = get()
    for e in ents:
        p = e["payload"]
        print(f'{e["type"]:28} | {p.get("name", ""):36} | {p.get("definition", {}).get("type", ""):9} | '
              f'{p.get("definition", {}).get("settings", "")}')


def test():
    now = datetime.now(timezone.utc)
    q = (f"let startTime = datetime({now - timedelta(minutes=4):%Y-%m-%dT%H:%M:%SZ});\n"
         f"let endTime = datetime({now:%Y-%m-%dT%H:%M:%SZ});\n" + BODY + "\n| summarize arg_max(Minute, *) by City | order by Wet desc, City asc")
    s, b = fa.call("POST", RT["query_uri"] + "/v1/rest/query", {"db": RT["database"], "csl": q}, resource=KUSTO, poll=False)
    if s >= 300:
        sys.exit(f"query {s} {json.dumps(b)[:500]}")
    t = b["Tables"][0]
    print([c["ColumnName"] for c in t["Columns"]])
    for r in t["Rows"]:
        print(r)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "test":
        test()
    elif cmd == "apply":
        apply()
    elif cmd in ("stop", "start"):
        run_rule(cmd == "start")
    elif cmd == "remove":
        apply(remove_only=True)
    elif cmd == "show":
        show()
    else:
        sys.exit(__doc__)
