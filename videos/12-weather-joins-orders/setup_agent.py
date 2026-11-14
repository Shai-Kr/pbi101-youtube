"""Video 12: teach the Fabric data agent "Aurora Live Agent" about the weather table (by REST).

  python -I setup_agent.py show            what the agent has now (sources, selected tables, instructions: yes/no)
  python -I setup_agent.py apply           add WeatherLive to the KQL source + agent instructions, draft AND published

The agent's definition has a `draft/` and a `published/` copy of every part; `apply` writes both, so the published agent
(the one the Copilot Studio agent calls) changes at once. A copy of the definition before the change is saved outside
the repo (<work>/agent_def/before_<time>.json).
Video 11 note: until this script ran the agent had NO instructions (aiInstructions was null); it only had its publish
description ("... All times are UTC") and the semantic model's descriptions.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FABRIC_SKILL", "eventhouse-cli")
sys.path.insert(0, str(HERE.parents[1] / "studio"))
sys.path.insert(0, str(HERE))
import fabric_api as fa  # noqa: E402
import weather as wx  # noqa: E402

WORK = HERE / "work" / "agent_def"
TYPES = {"datetime": "System.DateTime", "string": "System.String", "real": "System.Double", "long": "System.Int64"}

INSTRUCTIONS = """You answer questions about Aurora Outdoor's online store (a simulated demo store) from two tables in the AuroraLive KQL database. Every number in an answer must come from a query. Always state the time window you used. All times are UTC.

OrdersLive: one row per order (OrderTime, Product, Category, Region, City, Quantity, SalesAmount, PaymentMethod, Channel). It holds about 28 days of history plus orders arriving right now.

WeatherLive: REAL weather readings for the store's 17 cities (source: Open-Meteo). One row per city per reading.
- IntervalMin == 60: hourly history. ReadingTime is the END of the hour the reading covers.
- IntervalMin == 15: readings arriving now. Each covers the 15 minutes before ReadingTime.
- RainRate is millimetres per hour in both kinds of row. Raining means RainRate >= 0.4. Heavy rain means RainRate >= 2.
- Cold means TempC < 5. Hot means TempC > 26. Condition is the weather in words.

How to work with the weather:
- The weather in a city now: the latest reading, WeatherLive | where ReadingTime > ago(2h) | summarize arg_max(ReadingTime, *) by City.
- Weather and orders in the history: summarize OrdersLive by City and Hour = bin(OrderTime, 1h), and join to WeatherLive | where IntervalMin == 60 | extend Hour = ReadingTime - 1h, on City and Hour. Keep the hours with no orders of a product as 0 (start from the weather rows).
- Compare orders PER HOUR in rainy hours and in dry hours of the same city (or cold and not cold). Never compare totals: dry hours are far more numerous.
- "What does rain usually do in <city>": for the last 28 days give the average orders per hour of each product in rainy and in dry hours of that city, the ratio, and how many rainy hours that is based on. Name the products whose ratio stands out.
- "What to expect": the usual orders per hour in that weather, next to what the last 30 to 60 minutes actually show.
- The store's shoppers are simulated and were built to react to weather, so say what the data shows and do not present it as a discovery about real customers."""

KUSTO_NOTES = ("AuroraLive holds OrdersLive (orders) and WeatherLive (real weather per city). Join them on City and the hour. "
               "WeatherLive.ReadingTime is the end of the period a reading covers; use IntervalMin == 60 for history and the latest "
               "IntervalMin == 15 row per city for the weather now. Raining = RainRate >= 0.4 (mm per hour).")
DESCRIPTION = ("Answers questions about Aurora Outdoor's online orders (simulated store) and the real weather in its 17 cities: "
               "orders and sales by minute, hour, day, region, city, product, payment method and channel for the last minutes up to "
               "the last 28 days, the weather now and in the past (temperature, rain), and how orders differ in rainy, cold or hot "
               "hours. All times are UTC.")
COL_NOTES = {"ReadingTime": "end of the period the reading covers (UTC)", "RainRate": "rain in millimetres per hour; raining = 0.4 or more",
             "IntervalMin": "60 = hourly history, 15 = readings arriving now", "TempC": "air temperature in Celsius",
             "PrecipMm": "millimetres of precipitation in the period", "Condition": "the weather in words"}


def agent_id() -> str:
    return json.loads((Path.home() / ".pbi101" / "fabric_env.json").read_text(encoding="utf-8"))["realtime"]["live_agent_id"]


def get() -> dict:
    s, b = fa.call("POST", fa.FABRIC + f"workspaces/{fa.WS}/items/{agent_id()}/getDefinition", {})
    if s >= 300:
        sys.exit(f"getDefinition {s} {json.dumps(b)[:400]}")
    return b


def dec(p):
    return json.loads(base64.b64decode(p["payload"]).decode("utf-8"))


def enc(o) -> str:
    return base64.b64encode(json.dumps(o, indent=2).encode("utf-8")).decode()


def table_id(name: str) -> str:
    r = wx.sf.kql(".show tables details | project TableName, TableId")
    return next(row[1] for row in r["Tables"][0]["Rows"] if row[0] == name)


def weather_element() -> dict:
    return {"id": table_id(wx.TABLE), "is_selected": True, "display_name": wx.TABLE, "type": "kusto.table",
            "description": "Real weather readings for the store's 17 cities (Open-Meteo); one row per city per reading.",
            "children": [{"id": n, "is_selected": True, "display_name": n, "type": "kusto.column", "data_type": TYPES[t],
                          "description": COL_NOTES.get(n), "children": []} for n, t in wx.COLUMNS]}


def show():
    for p in get()["definition"]["parts"]:
        if p["path"].endswith("stage_config.json"):
            print(p["path"], "| instructions:", "yes, %d chars" % len(dec(p)["aiInstructions"]) if dec(p)["aiInstructions"] else "none")
        elif p["path"].endswith("datasource.json"):
            d = dec(p)
            sel = [c["display_name"] for e in d["elements"] for c in ([e] if e["type"].endswith(".table") else e.get("children") or [])
                   if c.get("is_selected") and c["type"].endswith("table")]
            print(p["path"], "|", d["type"], "| selected tables:", sel, "| source notes:", "yes" if d.get("dataSourceInstructions") else "none")
        elif p["path"].endswith("publish_info.json"):
            print(p["path"], "|", dec(p)["description"][:90] + "...")


def apply():
    b = get()
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f"before_{time.strftime('%Y%m%d_%H%M%S')}.json").write_text(json.dumps(b), encoding="utf-8")
    we = weather_element()
    parts = []
    for p in b["definition"]["parts"]:
        path = p["path"]
        if path.endswith("stage_config.json"):
            d = dec(p)
            d["aiInstructions"] = INSTRUCTIONS
            p = {**p, "payload": enc(d)}
        elif path.endswith("kusto-AuroraLive/datasource.json"):
            d = dec(p)
            d["dataSourceInstructions"] = KUSTO_NOTES
            d["userDescription"] = "Orders of the Aurora store (OrdersLive) and real weather per city (WeatherLive)."
            grp = next(e for e in d["elements"] if e["type"] == "table_grouping")
            grp["children"] = [c for c in grp["children"] if c["display_name"] != wx.TABLE] + [we]
            p = {**p, "payload": enc(d)}
        elif path.endswith("publish_info.json"):
            d = dec(p)
            d["description"] = DESCRIPTION
            p = {**p, "payload": enc(d)}
        if path != ".platform":
            parts.append({"path": path, "payload": p["payload"], "payloadType": "InlineBase64"})
    s, r = fa.call("POST", fa.FABRIC + f"workspaces/{fa.WS}/items/{agent_id()}/updateDefinition", {"definition": {"parts": parts}})
    print("updateDefinition", s, "" if s < 300 else json.dumps(r)[:600])
    show()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "show":
        show()
    elif a and a[0] == "apply":
        apply()
    else:
        sys.exit(__doc__)
