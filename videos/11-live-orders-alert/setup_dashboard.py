"""Video 11: the Real-Time Dashboard "Aurora Live Orders" (create or update by REST).

  python -I setup_dashboard.py      -> creates the dashboard in the "Real-Time" folder, or rewrites its definition

Page "Live", five tiles: the taps from the phone page on their own tile, orders in the last minute, sales in the
last hour, orders per minute by region (zeros included, so a region that stops drops to 0 instead of leaving a
gap), and the latest orders. Page "Phone demo" (for the take with the phone page beside it): orders arriving in
10-second steps with the phone's taps as their own series, and the phone tile. Open it with Live refresh on.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import uuid
from pathlib import Path

os.environ.setdefault("FABRIC_SKILL", "eventhouse-cli")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio"))
import fabric_api as fa  # noqa: E402

ENV_FILE = Path.home() / ".pbi101" / "fabric_env.json"
NAME = "Aurora Live Orders"

Q_LINE = """OrdersLive
| where OrderTime >= bin(ago(30m), 1m) and OrderTime < bin(now(), 1m)
| make-series Orders = count() default = 0 on OrderTime from bin(ago(30m), 1m) to bin(now(), 1m) step 1m by Region
| mv-expand OrderTime to typeof(datetime), Orders to typeof(long)
| project OrderTime, Region, Orders
| order by OrderTime asc"""
Q_MIN = "OrdersLive\n| where OrderTime > ago(1m)\n| summarize ['Orders in the last minute'] = count()"
Q_SALES = "OrdersLive\n| where OrderTime > ago(1h)\n| summarize ['Sales in the last hour'] = round(sum(SalesAmount))"
Q_LAST = ("OrdersLive\n| top 8 by OrderTime desc\n"
          "| project OrderTime, Product, City, Region, SalesAmount, PaymentMethod, Channel")
Q_PHONE = ("OrdersLive\n| where OrderTime > ago(30m) and Channel == 'Phone (this demo)'\n| top 6 by OrderTime desc\n"
           "| project OrderTime, Product, City, SalesAmount, ['Arrived after (s)'] = round((ingestion_time() - OrderTime) / 1s, 1)")


Q_ARRIVE = """OrdersLive
| where OrderTime >= bin(ago(3m), 10s)
| make-series ['My phone'] = countif(Channel == 'Phone (this demo)') default = 0,
              ['Other orders'] = countif(Channel != 'Phone (this demo)') default = 0
              on OrderTime from bin(ago(3m), 10s) to now() step 10s
| mv-expand OrderTime to typeof(datetime), ['My phone'] to typeof(long), ['Other orders'] to typeof(long)
| project OrderTime, ['My phone'], ['Other orders']
| order by OrderTime asc"""


# ---- video 12: the page "Weather" (real weather next to the orders)
Q_WNOW = """WeatherLive
| where IntervalMin == 15 and ReadingTime > ago(1h)
| summarize arg_max(ReadingTime, *) by City
| project City, ['Temp (C)'] = TempC, ['Rain (mm/h)'] = RainRate, Condition, ['As of'] = ReadingTime
| order by ['Rain (mm/h)'] desc, City asc"""
Q_WMAP = """WeatherLive
| where IntervalMin == 15 and ReadingTime > ago(1h)
| summarize arg_max(ReadingTime, *) by City
| project Longitude, Latitude, Weather = iff(RainRate >= 0.4, 'Raining now', iff(TempC < 5, 'Cold', iff(TempC > 26, 'Hot', 'Mild'))),
          Size = iff(RainRate >= 0.4, 3.0, 1.0)"""
Q_WSHARE = """let w = WeatherLive
    | where IntervalMin == 15 and ReadingTime > ago(1h)
    | summarize arg_max(ReadingTime, RainRate) by City;
OrdersLive
| where OrderTime > ago(1h)
| summarize Orders = count(), Jackets = countif(Product == 'Storm Shell Jacket') by City
| join kind=inner w on City
| extend Weather = iff(RainRate >= 0.4, 'Raining now', 'Dry'), Share = round(100.0 * Jackets / Orders, 1)
| project City, Weather, ['Jacket share of orders (%)'] = Share
| order by ['Jacket share of orders (%)'] desc"""


def g() -> str:
    return str(uuid.uuid4())


def definition(rt: dict) -> dict:
    ds, live, phone, weather = g(), g(), g(), g()
    qs = []

    def tile(page, title, visual, text, x, y, w, h):
        qs.append({"id": g(), "dataSource": {"kind": "inline", "dataSourceId": ds}, "text": text, "usedVariables": []})
        return {"id": g(), "title": title, "visualType": visual, "pageId": page,
                "layout": {"x": x, "y": y, "width": w, "height": h},
                "queryRef": {"kind": "query", "queryId": qs[-1]["id"]}, "visualOptions": {}}

    tiles = [tile(live, "Orders in the last minute", "card", Q_MIN, 0, 0, 6, 4),
             tile(live, "Sales in the last hour (USD)", "card", Q_SALES, 6, 0, 6, 4),
             tile(live, "Orders per minute, by region (last 30 minutes)", "line", Q_LINE, 0, 4, 12, 10),
             tile(live, "Orders from my phone (this demo)", "table", Q_PHONE, 12, 0, 12, 5),
             tile(live, "Latest orders, all channels", "table", Q_LAST, 12, 5, 12, 9),
             # second page, for the take with the phone page beside it: full width, readable in a narrow window
             tile(phone, "Orders arriving, last 3 minutes (10-second steps)", "stackedcolumn", Q_ARRIVE, 0, 0, 24, 8),
             tile(phone, "Orders from my phone (this demo)", "table", Q_PHONE, 0, 8, 24, 5),
             # third page (video 12): real weather next to the orders
             tile(weather, "Weather right now in the store's 17 cities (real, Open-Meteo)", "table", Q_WNOW, 11, 0, 13, 9),
             tile(weather, "The 17 cities right now: raining, cold, hot or mild", "map", Q_WMAP, 0, 0, 11, 9),
             tile(weather, "Storm Shell Jacket: share of each city's orders, last hour", "bar", Q_WSHARE, 0, 9, 24, 5)]
    return {"$schema": "https://dataexplorer.azure.com/static/d/schema/52/dashboard.json", "schema_version": "52",
            "title": NAME, "autoRefresh": {"enabled": True, "defaultInterval": "10s", "minInterval": "10s"},
            "tiles": tiles, "baseQueries": [], "parameters": [],
            "dataSources": [{"id": ds, "name": rt["database"], "clusterUri": rt["query_uri"], "database": rt["database_id"],
                             "kind": "kusto-trident", "scopeId": "kusto-trident", "workspace": fa.WS}],
            "pages": [{"name": "Live", "id": live}, {"name": "Phone demo", "id": phone}, {"name": "Weather", "id": weather}], "queries": qs}


def main():
    env = json.loads(ENV_FILE.read_text(encoding="utf-8"))
    rt = env["realtime"]
    part = {"path": "RealTimeDashboard.json", "payloadType": "InlineBase64",
            "payload": base64.b64encode(json.dumps(definition(rt)).encode("utf-8")).decode()}
    base = fa.FABRIC + f"workspaces/{fa.WS}/items"
    s, b = fa.call("GET", base + "?type=KQLDashboard")
    it = next((i for i in b.get("value", []) if i["displayName"] == NAME), None)
    if it:
        s, b = fa.call("POST", f"{base}/{it['id']}/updateDefinition", {"definition": {"parts": [part]}})
        print("updateDefinition", s, "" if s < 300 else json.dumps(b)[:500])
    else:
        s, b = fa.call("POST", base, {"displayName": NAME, "type": "KQLDashboard", "folderId": rt["folder_id"],
                                      "description": "Live view of Aurora's online orders (demo, simulated store)",
                                      "definition": {"parts": [part]}})
        print("create", s, "" if s < 300 else json.dumps(b)[:500])
        s, b = fa.call("GET", base + "?type=KQLDashboard")
        it = next(i for i in b["value"] if i["displayName"] == NAME)
    env["realtime"]["dashboard_id"] = it["id"]
    ENV_FILE.write_text(json.dumps(env, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
