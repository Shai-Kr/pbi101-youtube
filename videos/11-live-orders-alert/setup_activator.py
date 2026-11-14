"""Video 11 ground work: the alert rule. Activator "AuroraOrdersWatch" on the AuroraLive KQL database.

  python -I setup_activator.py test       run the source query once with literal times and print the rows
  python -I setup_activator.py deploy     create the Activator (if missing) and write its definition
  python -I setup_activator.py show       read the definition back (entity types, names, rule state)

Rule "Region stopped ordering": per region, the number of orders in the last 5 minutes becomes 0.
Action for now: a Teams message from Activator to the signed-in pbi101 user (read from ~/.pbi101/fabric_env.json;
the address is never written into the repo). The source query returns ALL minutes and regions; the rule detects.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ["FABRIC_SKILL"] = "activator-cli"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio"))
import fabric_api as fa  # noqa: E402

ENV_FILE = Path.home() / ".pbi101" / "fabric_env.json"
ENV = json.loads(ENV_FILE.read_text(encoding="utf-8"))
RT = ENV["realtime"]
WS = fa.WS
F = fa.FABRIC + f"workspaces/{WS}/"
NAME = "AuroraOrdersWatch"
WINDOW_MIN = 5

BODY = f"""let e = bin(endTime, 1m);
let s = bin(startTime, 1m) + 1m;
let regions = datatable(Region:string)["North America", "Europe", "Asia Pacific", "Latin America"];
let perMin = OrdersLive
    | where OrderTime >= s - {WINDOW_MIN}m and OrderTime < e
    | summarize c = count(), sales = sum(SalesAmount) by Region, M = bin(OrderTime, 1m);
range Minute from s to e step 1m
| extend k = 1
| join kind=inner (regions | extend k = 1) on k
| project Minute, Region
| join kind=leftouter perMin on Region
| summarize Orders5m = sumif(c, M >= Minute - {WINDOW_MIN}m and M < Minute),
            Sales5m = sumif(sales, M >= Minute - {WINDOW_MIN}m and M < Minute) by Minute, Region
| order by Minute asc, Region asc"""
QUERY = "declare query_parameters(startTime:datetime, endTime:datetime);\n" + BODY


def g() -> str:
    return str(uuid.uuid4())


def s(o) -> str:
    return json.dumps(o, separators=(",", ":"))


def arg(name, typ, value):
    return {"name": name, "type": typ, "value": value}


def ref(kind, entity_id, name=None, typ="complex"):
    r = {"kind": kind, "type": typ, "arguments": [arg("entityId", "string", entity_id)]}
    if name:
        r["name"] = name
    return r


def view(uid, name, dtype, container, instance=None, parent=None, settings=None, description=None):
    p = {"name": name, "parentContainer": {"targetUniqueIdentifier": container}, "definition": {"type": dtype}}
    if description:
        p["description"] = description
    if parent:
        p["parentObject"] = {"targetUniqueIdentifier": parent}
    if instance is not None:
        p["definition"]["instance"] = s(instance)
    if settings:
        p["definition"]["settings"] = settings
    return {"uniqueIdentifier": uid, "payload": p, "type": "timeSeriesView-v1"}


def basic_attr(event_id, field, op):
    return {"templateId": "BasicEventAttribute", "templateVersion": "1.2.4", "steps": [
        {"name": "EventSelectStep", "id": g(), "rows": [
            {"name": "EventSelector", "kind": "Event", "arguments": [ref("EventReference", event_id, "event")]},
            {"name": "EventFieldSelector", "kind": "EventField", "arguments": [arg("fieldName", "string", field)]}]},
        {"name": "EventComputeStep", "id": g(), "rows": [
            {"name": "TypeAssertion", "kind": "TypeAssertion", "arguments": [arg("op", "string", op), arg("format", "string", "")]}]}]}


def entities(recipient: str) -> list:
    c, src, ev, obj, ident, split, orders, sales, rname, rule = (g() for _ in range(10))
    now = datetime.now(timezone.utc)
    iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    out = [{"uniqueIdentifier": c, "payload": {"name": "Aurora live orders", "type": "kqlQueries"}, "type": "container-v1"},
           {"uniqueIdentifier": src, "type": "kqlSource-v1", "payload": {
               "name": "Orders per region, last 5 minutes", "runSettings": {"executionIntervalInSeconds": 60},
               "query": {"queryString": QUERY},
               "eventhouseItem": {"itemId": RT["database_id"], "workspaceId": WS, "itemType": "KustoDatabase"},
               "queryParameters": [{"name": "startTime", "type": "DURATION_START", "value": iso(now - timedelta(minutes=10))},
                                   {"name": "endTime", "type": "DURATION_END", "value": iso(now)}],
               "eventTimeSettings": {"timeFieldName": "Minute", "ingestionDelayInSeconds": 20, "timeZone": "UTC"},
               "metadata": {"workspaceId": WS, "measureName": "", "querySetId": "", "queryId": ""},
               "parentContainer": {"targetUniqueIdentifier": c}}},
           view(ev, "Orders per region events", "Event", c, {"templateId": "SourceEvent", "templateVersion": "1.2.4", "steps": [
               {"name": "SourceEventStep", "id": g(), "rows": [
                   {"name": "SourceSelector", "kind": "SourceReference", "arguments": [arg("entityId", "string", src)]}]}]}),
           view(obj, "Region", "Object", c),
           view(ident, "Region", "Attribute", c, {"templateId": "IdentityPartAttribute", "templateVersion": "1.2.4", "steps": [
               {"name": "IdPartStep", "id": g(), "rows": [{"name": "TypeAssertion", "kind": "TypeAssertion", "arguments": [
                   arg("op", "string", "Text"), arg("format", "string", "")]}]}]}, parent=obj),
           view(split, "Orders per region", "Event", c, {"templateId": "SplitEvent", "templateVersion": "1.2.4", "steps": [
               {"name": "SplitEventStep", "id": g(), "rows": [
                   {"name": "EventSelector", "kind": "Event", "arguments": [ref("EventReference", ev, "event")]},
                   {"name": "FieldIdMapping", "kind": "FieldIdMapping", "arguments": [
                       arg("fieldName", "string", "Region"), ref("AttributeReference", ident, "idPart")]},
                   {"name": "SplitEventOptions", "kind": "EventOptions", "arguments": [arg("isAuthoritative", "boolean", True)]}]}]},
                parent=obj),
           view(orders, "Orders in the last 5 minutes", "Attribute", c, basic_attr(split, "Orders5m", "Number"), parent=obj),
           view(sales, "Sales in the last 5 minutes", "Attribute", c, basic_attr(split, "Sales5m", "Number"), parent=obj),
           view(rname, "Region name", "Attribute", c, basic_attr(split, "Region", "Text"), parent=obj)]
    rule_t = {"templateId": "AttributeTrigger", "templateVersion": "1.2.4", "steps": [
        {"name": "ScalarSelectStep", "id": g(), "rows": [
            {"name": "AttributeSelector", "kind": "Attribute", "arguments": [ref("AttributeReference", orders, "attribute")]}]},
        {"name": "ScalarDetectStep", "id": g(), "rows": [
            {"name": "NumberBecomes", "kind": "NumberBecomes", "arguments": [
                arg("op", "string", "BecomesLessThan"), arg("value", "number", 1.0)]}]},
        {"name": "ActStep", "id": g(), "rows": [{"name": "TeamsBinding", "kind": "TeamsMessage", "arguments": [
            arg("messageLocale", "string", ""),
            {"name": "recipients", "type": "array", "values": [{"type": "string", "value": recipient}]},
            {"name": "headline", "type": "array", "values": [
                {"name": "string", "type": "string", "value": "Orders stopped: "},
                ref("AttributeReference", rname),
                {"name": "string", "type": "string", "value": " "}]},
            {"name": "optionalMessage", "type": "array", "values": [
                {"name": "string", "type": "string", "value": "No orders from this region in the last 5 minutes (simulated Aurora store)."}]},
            {"name": "additionalInformation", "type": "array", "values": [
                {"kind": "NameReferencePair", "type": "complex", "arguments": [
                    arg("name", "string", "Orders in the last 5 minutes"),
                    ref("AttributeReference", orders, "reference", "complexReference")]}]}]}]}]}
    out.append(view(rule, "Region stopped ordering", "Rule", c, rule_t, parent=obj,
                    settings={"shouldRun": True, "shouldApplyRuleOnUpdate": False}, description="Created by: skills-for-fabric"))
    ids = {e["uniqueIdentifier"] for e in out}
    blob = json.dumps(out)
    import re
    for m in re.findall(r'targetUniqueIdentifier": "([0-9a-f-]{36})"', blob):
        assert m in ids, m
    for e in out:
        inst = e["payload"].get("definition", {}).get("instance")
        if inst:
            for m in re.findall(r'"entityId","type":"string","value":"([0-9a-f-]{36})"', inst):
                assert m in ids, ("dangling", e["payload"]["name"], m)
    return out


def find():
    st, b = fa.call("GET", F + "reflexes")
    return next((i for i in b.get("value", []) if i["displayName"] == NAME), None)


def test():
    now = datetime.now(timezone.utc)
    q = (f"let startTime = datetime({(now - timedelta(minutes=4)).strftime('%Y-%m-%dT%H:%M:%SZ')});\n"
         f"let endTime = datetime({now.strftime('%Y-%m-%dT%H:%M:%SZ')});\n" + BODY)
    st, b = fa.call("POST", RT["query_uri"] + "/v1/rest/query", {"db": RT["database"], "csl": q},
                    resource="https://kusto.kusto.windows.net", poll=False)
    if st != 200:
        sys.exit(f"query failed {st}: {str(b)[:500]}")
    t = b["Tables"][0]
    print([c["ColumnName"] for c in t["Columns"]])
    for r in t["Rows"]:
        print(r)


def deploy():
    it = find()
    if not it:
        st, b = fa.call("POST", F + "reflexes", {"displayName": NAME, "folderId": RT["folder_id"],
                                                 "description": "Alerts on Aurora's live orders (demo, simulated store)"})
        if st >= 300:
            sys.exit(f"create failed {st}: {str(b)[:400]}")
        it = find()
    ents = entities(ENV["user"])
    payload = base64.b64encode(json.dumps(ents).encode("utf-8")).decode()
    st, b = fa.call("POST", F + f"reflexes/{it['id']}/updateDefinition",
                    {"definition": {"parts": [{"path": "ReflexEntities.json", "payload": payload, "payloadType": "InlineBase64"}]}})
    print("updateDefinition", st, "" if st < 300 else str(b)[:800])
    e = json.loads(ENV_FILE.read_text(encoding="utf-8"))
    e["realtime"]["activator_id"] = it["id"]
    ENV_FILE.write_text(json.dumps(e, indent=2), encoding="utf-8")


def show():
    it = find()
    st, b = fa.call("POST", F + f"reflexes/{it['id']}/getDefinition", {})
    if st >= 300:
        sys.exit(f"getDefinition {st}: {str(b)[:400]}")
    for p in b["definition"]["parts"]:
        if p["path"] == "ReflexEntities.json":
            for e in json.loads(base64.b64decode(p["payload"]).decode("utf-8")):
                d = e["payload"].get("definition", {})
                print(e["type"], "|", e["payload"].get("name"), "|", d.get("type", ""), "|", d.get("settings", ""))


if __name__ == "__main__":
    {"test": test, "deploy": deploy, "show": show}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
