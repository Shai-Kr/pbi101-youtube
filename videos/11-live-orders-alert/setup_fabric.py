"""Video 11 ground work: the live-orders items in the pbi101 workspace, built by REST (idempotent).

  python -I setup_fabric.py items      folder "Real-Time" + Eventhouse AuroraLive (+ its KQL database) + table OrdersLive
                                       + Eventstream AuroraOrders (custom endpoint -> Eventhouse)
  python -I setup_fabric.py endpoint   fetch the custom endpoint's connection and save it OUTSIDE the repo
                                       (~/.pbi101/eventstream_orders.json); prints names only, never the key
  python -I setup_fabric.py kql "<query or .command>"     run KQL on AuroraLive (management commands start with a dot)

Ids go to ~/.pbi101/fabric_env.json under "realtime". Nothing secret is printed or written inside the repo.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("FABRIC_SKILL", "eventstream-cli")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio"))
import fabric_api as fa  # noqa: E402

ENV_FILE = Path.home() / ".pbi101" / "fabric_env.json"
SECRET_FILE = Path.home() / ".pbi101" / "eventstream_orders.json"
WS = fa.WS
F = fa.FABRIC + f"workspaces/{WS}/"
FOLDER, EVENTHOUSE, STREAM, TABLE = "Real-Time", "AuroraLive", "AuroraOrders", "OrdersLive"
KUSTO = "https://kusto.kusto.windows.net"

COLUMNS = [("OrderId", "string"), ("OrderTime", "datetime"), ("ProductId", "long"), ("Product", "string"),
           ("Category", "string"), ("RegionId", "long"), ("Region", "string"), ("City", "string"),
           ("Quantity", "long"), ("UnitPrice", "real"), ("SalesAmount", "real"), ("PaymentMethod", "string"),
           ("Channel", "string")]


def env() -> dict:
    return json.loads(ENV_FILE.read_text(encoding="utf-8"))


def save(rt: dict):
    e = env()
    e.setdefault("realtime", {}).update(rt)
    ENV_FILE.write_text(json.dumps(e, indent=2), encoding="utf-8")


def ok(status, body, what):
    if status >= 300:
        sys.exit(f"{what}: HTTP {status} {json.dumps(body)[:600] if not isinstance(body, str) else body[:600]}")
    return body


def find(kind: str, name: str):
    s, b = fa.call("GET", F + kind)
    for i in ok(s, b, "list " + kind).get("value", []):
        if i["displayName"] == name:
            return i
    return None


def kql(command: str):
    rt = env()["realtime"]
    path = "mgmt" if command.lstrip().startswith(".") else "query"
    s, b = fa.call("POST", rt["query_uri"] + "/v1/rest/" + path, {"db": rt["database"], "csl": command},
                   resource=KUSTO, poll=False)
    return ok(s, b, "kql")


def items():
    folder = find("folders", FOLDER)
    if not folder:
        s, b = fa.call("POST", F + "folders", {"displayName": FOLDER})
        folder = ok(s, b, "create folder")
    print("folder", FOLDER, "ok")

    eh = find("eventhouses", EVENTHOUSE)
    if not eh:
        s, b = fa.call("POST", F + "eventhouses", {"displayName": EVENTHOUSE, "folderId": folder["id"],
                                                    "description": "Aurora live orders (demo, simulated store)"})
        ok(s, b, "create eventhouse")
        eh = find("eventhouses", EVENTHOUSE)
    print("eventhouse", EVENTHOUSE, "ok")

    db = find("kqlDatabases", EVENTHOUSE)
    if not db:
        sys.exit("KQL database not listed yet; run again in a minute")
    save({"folder_id": folder["id"], "eventhouse_id": eh["id"], "database": db["displayName"], "database_id": db["id"],
          "query_uri": db["properties"]["queryServiceUri"], "table": TABLE, "eventstream": STREAM})
    print("kql database", db["displayName"], "ok")

    cols = ", ".join(f"{n}: {t}" for n, t in COLUMNS)
    kql(f".create-merge table {TABLE} ({cols})")
    kql(f".alter table {TABLE} policy streamingingestion enable")
    print("table", TABLE, "ok")

    es = find("eventstreams", STREAM)
    if not es:
        topo = {"compatibilityLevel": "1.0",
                "sources": [{"name": "OrdersApp", "type": "CustomEndpoint", "properties": {}}],
                "streams": [{"name": STREAM + "-stream", "type": "DefaultStream", "properties": {},
                             "inputNodes": [{"name": "OrdersApp"}]}],
                "operators": [],
                "destinations": [{"name": "OrdersToEventhouse", "type": "Eventhouse",
                                  "properties": {"dataIngestionMode": "ProcessedIngestion", "workspaceId": WS,
                                                 "itemId": db["id"], "databaseName": db["displayName"], "tableName": TABLE,
                                                 "inputSerialization": {"type": "Json", "properties": {"encoding": "UTF8"}}},
                                  "inputNodes": [{"name": STREAM + "-stream"}]}]}
        props = {"retentionTimeInDays": 1, "eventThroughputLevel": "Low"}
        b64 = lambda o: base64.b64encode(json.dumps(o).encode("utf-8")).decode()  # noqa: E731
        s, b = fa.call("POST", F + "items", {
            "displayName": STREAM, "type": "Eventstream", "folderId": folder["id"],
            "description": "Aurora live orders: custom endpoint -> Eventhouse",
            "definition": {"parts": [
                {"path": "eventstream.json", "payload": b64(topo), "payloadType": "InlineBase64"},
                {"path": "eventstreamProperties.json", "payload": b64(props), "payloadType": "InlineBase64"}]}})
        ok(s, b, "create eventstream")
        es = find("eventstreams", STREAM)
    save({"eventstream_id": es["id"]})
    print("eventstream", STREAM, "ok")


def endpoint():
    rt = env()["realtime"]
    s, b = fa.call("GET", F + f"eventstreams/{rt['eventstream_id']}/topology")
    topo = ok(s, b, "topology")
    for kind in ("sources", "streams", "destinations"):
        for n in topo.get(kind, []):
            print(kind[:-1], n.get("name"), "|", n.get("type"), "|", n.get("status"), "|",
                  (n.get("error") or {}).get("errorMessage", "") if isinstance(n.get("error"), dict) else "")
    src = [n for n in topo.get("sources", []) if n.get("type") == "CustomEndpoint"]
    if not src:
        sys.exit("no custom endpoint source in the topology")
    s, b = fa.call("GET", F + f"eventstreams/{rt['eventstream_id']}/sources/{src[0]['id']}/connection")
    conn = ok(s, b, "connection")
    SECRET_FILE.write_text(json.dumps(conn), encoding="utf-8")
    print("saved connection (namespace, hub and keys) to the secret file outside the repo; keys present:",
          bool((conn.get("accessKeys") or {}).get("primaryKey")))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "items":
        items()
    elif cmd == "endpoint":
        endpoint()
    elif cmd == "kql":
        r = kql(sys.argv[2])
        t = (r.get("Tables") or [{}])[0]
        print([c["ColumnName"] for c in t.get("Columns", [])])
        for row in t.get("Rows", [])[:40]:
            print(row)
    else:
        sys.exit(__doc__)
