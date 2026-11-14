"""Video 12: real weather for the store's 17 cities, into Fabric next to the orders (stdlib only).

  python -I weather.py setup          table WeatherLive + Eventstream AuroraWeather (custom endpoint -> the same Eventhouse)
  python -I weather.py endpoint       save the endpoint's connection to ~/.pbi101/eventstream_weather.json (never printed)
  python -I weather.py now            print the current reading of every city (nothing is sent)
  python -I weather.py send           fetch the current readings and send one event per city
  python -I weather.py run [minutes]  every 5 minutes: fetch, send the readings that changed (or every 15 minutes), write weather_state.json
  python -I weather.py forecast [h]   rain starts expected in the next h hours (15-minute steps), to plan a take
  python -I weather.py history 28     hourly history of the last N days into WeatherLive (inline ingest, no events)
  python -I weather.py extras 28      weather-driven extra orders for the last N days (generated inside the Eventhouse)
  python -I weather.py kql "<query>"

The weather is REAL: Open-Meteo (https://open-meteo.com, CC BY 4.0, no key; say "Weather data by Open-Meteo.com").
A "current" reading covers the 15 minutes before its time; an hourly one covers the hour before its time.
RainRate is millimetres per hour in both, so the two can be compared. Raining = RainRate >= RAIN.

The shoppers are SIMULATED, and they react to the weather (say so on camera). The same rule is used for the history
(`extras`) and for the running store (store_sim.py), per city:
  raining            -> Storm Shell Jacket orders x 3   (x 4 when RainRate >= HEAVY)
  colder than 5 C    -> Thermal Base Layer and Summit Fleece orders x 1.8
  warmer than 26 C   -> Glacier Water Bottle orders x 2.2
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
V11 = HERE.parent / "11-live-orders-alert"
os.environ.setdefault("FABRIC_SKILL", "eventhouse-cli")
sys.path.insert(0, str(HERE.parents[1] / "studio"))
sys.path.insert(0, str(V11))
import fabric_api as fa  # noqa: E402
import live_orders as lo  # noqa: E402
import setup_fabric as sf  # noqa: E402

TABLE, STREAM = "WeatherLive", "AuroraWeather"
SECRET = Path.home() / ".pbi101" / "eventstream_weather.json"
STATE = HERE / "work" / "weather_state.json"
RAIN, HEAVY, COLD, HOT = 0.4, 2.0, 5.0, 26.0
EFFECTS = [("rain", ["Storm Shell Jacket"], 3.0), ("heavy", ["Storm Shell Jacket"], 4.0),
           ("cold", ["Thermal Base Layer", "Summit Fleece"], 1.8), ("hot", ["Glacier Water Bottle"], 2.2)]

CITIES = {"Vancouver": (49.28, -123.12), "Seattle": (47.61, -122.33), "Denver": (39.74, -104.99), "Toronto": (43.65, -79.38),
          "New York": (40.71, -74.01), "London": (51.51, -0.13), "Berlin": (52.52, 13.41), "Oslo": (59.91, 10.75),
          "Madrid": (40.42, -3.70), "Zurich": (47.38, 8.54), "Tokyo": (35.68, 139.69), "Sydney": (-33.87, 151.21),
          "Auckland": (-36.85, 174.76), "Singapore": (1.35, 103.82), "Santiago": (-33.45, -70.67), "Bogota": (4.71, -74.07),
          "Sao Paulo": (-23.55, -46.63)}
COLUMNS = [("ReadingTime", "datetime"), ("City", "string"), ("Region", "string"), ("Latitude", "real"), ("Longitude", "real"),
           ("TempC", "real"), ("PrecipMm", "real"), ("RainRate", "real"), ("SnowCm", "real"), ("WindKmh", "real"),
           ("WeatherCode", "long"), ("Condition", "string"), ("IntervalMin", "long"), ("Source", "string")]
WMO = {0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle",
       55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
       66: "Freezing rain", 67: "Freezing rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
       80: "Light showers", 81: "Showers", 82: "Heavy showers", 85: "Snow showers", 86: "Heavy snow showers",
       95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail"}


def fetch(params: str) -> list:
    lat = ",".join(str(v[0]) for v in CITIES.values())
    lon = ",".join(str(v[1]) for v in CITIES.values())
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&timezone=UTC&{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "demo-client"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def row(city: str, t: str, temp, precip, snow, wind, code, interval: int) -> dict:
    lat, lon = CITIES[city]
    precip = precip or 0.0
    return {"ReadingTime": t + ":00Z", "City": city, "Region": lo.CITY_REGION[city], "Latitude": lat, "Longitude": lon,
            "TempC": temp, "PrecipMm": precip, "RainRate": round(precip * 60 / interval, 2), "SnowCm": snow or 0.0,
            "WindKmh": wind, "WeatherCode": code, "Condition": WMO.get(code, str(code)), "IntervalMin": interval,
            "Source": "open-meteo.com"}


def current() -> list[dict]:
    d = fetch("current=temperature_2m,precipitation,snowfall,weather_code,wind_speed_10m")
    # Open-Meteo keeps "time" on the 15-minute step but updates the values inside it, so a live reading is stamped
    # with the minute it was fetched (it still covers the 15 minutes before it)
    fetched = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    out = []
    for city, loc in zip(CITIES, d):
        c = loc["current"]
        out.append(row(city, fetched, c["temperature_2m"], c["precipitation"], c["snowfall"], c["wind_speed_10m"],
                       c["weather_code"], int(c["interval"] // 60)))
    return out


def tags(r: dict) -> list[str]:
    """which effects are on for a reading"""
    t = []
    if r["RainRate"] >= HEAVY:
        t.append("heavy")
    elif r["RainRate"] >= RAIN:
        t.append("rain")
    if r["TempC"] is not None and r["TempC"] < COLD:
        t.append("cold")
    if r["TempC"] is not None and r["TempC"] > HOT:
        t.append("hot")
    return t


# ---------------------------------------------------------------- Fabric items
def setup():
    rt = sf.env()["realtime"]
    cols = ", ".join(f"{n}: {t}" for n, t in COLUMNS)
    sf.kql(f".create-merge table {TABLE} ({cols})")
    sf.kql(f".alter table {TABLE} policy streamingingestion enable")
    sf.kql(f".alter table {TABLE} docstring 'Real weather readings for the 17 cities of the Aurora store (Open-Meteo). "
           "One row per city per reading. IntervalMin = 15 for live readings, 60 for hourly history. "
           "RainRate is millimetres per hour; raining means RainRate >= 0.4.'")
    print("table", TABLE, "ok")
    es = sf.find("eventstreams", STREAM)
    if not es:
        topo = {"compatibilityLevel": "1.0",
                "sources": [{"name": "WeatherFeed", "type": "CustomEndpoint", "properties": {}}],
                "streams": [{"name": STREAM + "-stream", "type": "DefaultStream", "properties": {},
                             "inputNodes": [{"name": "WeatherFeed"}]}],
                "operators": [],
                "destinations": [{"name": "WeatherToEventhouse", "type": "Eventhouse",
                                  "properties": {"dataIngestionMode": "ProcessedIngestion", "workspaceId": fa.WS,
                                                 "itemId": rt["database_id"], "databaseName": rt["database"], "tableName": TABLE,
                                                 "inputSerialization": {"type": "Json", "properties": {"encoding": "UTF8"}}},
                                  "inputNodes": [{"name": STREAM + "-stream"}]}]}
        props = {"retentionTimeInDays": 1, "eventThroughputLevel": "Low"}
        b64 = lambda o: base64.b64encode(json.dumps(o).encode("utf-8")).decode()  # noqa: E731
        s, b = fa.call("POST", sf.F + "items", {
            "displayName": STREAM, "type": "Eventstream", "folderId": rt["folder_id"],
            "description": "Real weather for the Aurora store's cities: custom endpoint -> Eventhouse",
            "definition": {"parts": [
                {"path": "eventstream.json", "payload": b64(topo), "payloadType": "InlineBase64"},
                {"path": "eventstreamProperties.json", "payload": b64(props), "payloadType": "InlineBase64"}]}})
        sf.ok(s, b, "create eventstream")
        es = sf.find("eventstreams", STREAM)
    sf.save({"weather_table": TABLE, "weather_eventstream": STREAM, "weather_eventstream_id": es["id"]})
    print("eventstream", STREAM, "ok")


def endpoint():
    rt = sf.env()["realtime"]
    s, b = fa.call("GET", sf.F + f"eventstreams/{rt['weather_eventstream_id']}/topology")
    topo = sf.ok(s, b, "topology")
    for kind in ("sources", "streams", "destinations"):
        for n in topo.get(kind, []):
            print(kind[:-1], n.get("name"), "|", n.get("type"), "|", n.get("status"))
    src = [n for n in topo.get("sources", []) if n.get("type") == "CustomEndpoint"]
    if not src:
        sys.exit("no custom endpoint source in the topology")
    s, b = fa.call("GET", sf.F + f"eventstreams/{rt['weather_eventstream_id']}/sources/{src[0]['id']}/connection")
    conn = sf.ok(s, b, "connection")
    SECRET.write_text(json.dumps(conn), encoding="utf-8")
    print("saved the connection to the secret file outside the repo; keys present:",
          bool((conn.get("accessKeys") or {}).get("primaryKey")))


def post(events: list[dict]) -> int:
    """send through the weather Eventstream (live_orders' sender, pointed at the weather endpoint)"""
    lo.SECRET = SECRET
    lo._conn.clear()
    lo._tok.update(v="", t=0.0)
    try:
        return lo.post(events)
    finally:
        lo.SECRET = Path.home() / ".pbi101" / "eventstream_orders.json"
        lo._conn.clear()
        lo._tok.update(v="", t=0.0)


def show(rows: list[dict]):
    for r in rows:
        print(f'{r["City"]:10} {r["ReadingTime"]}  {r["TempC"]:5.1f} C  rain {r["RainRate"]:4.1f} mm/h  {r["Condition"]:16} '
              f'{",".join(tags(r))}')


def run(minutes: float | None):
    end = time.time() + minutes * 60 if minutes else None
    seen: dict[str, tuple] = {}            # city -> (values, time sent): send on a change, or every 15 minutes
    while not end or time.time() < end:
        try:
            rows = current()
            key = lambda r: (r["TempC"], r["PrecipMm"], r["WeatherCode"], r["WindKmh"])  # noqa: E731
            new = [r for r in rows if r["City"] not in seen or seen[r["City"]][0] != key(r) or time.time() - seen[r["City"]][1] > 870]
            if new:
                st = post(new)
                for r in new:
                    seen[r["City"]] = (key(r), time.time())
                print(f"{datetime.now():%H:%M:%S} sent {len(new)} readings (HTTP {st}); raining: "
                      + (", ".join(r["City"] for r in rows if r["RainRate"] >= RAIN) or "nowhere"), flush=True)
            STATE.parent.mkdir(parents=True, exist_ok=True)
            STATE.write_text(json.dumps({"at": time.time(), "cities": {r["City"]: {"TempC": r["TempC"], "RainRate": r["RainRate"],
                             "ReadingTime": r["ReadingTime"], "tags": tags(r)} for r in rows}}), encoding="utf-8")
        except Exception as e:  # noqa: BLE001  (a failed fetch must not stop the feed)
            print("fetch/send failed:", str(e)[:160], flush=True)
        time.sleep(float(os.environ.get('WEATHER_EVERY', 300)))      # seconds between fetches (60 around a take)


def forecast(hours: int = 8):
    """Upcoming rain starts (dry for 30 minutes, then RainRate >= RAIN), from the same model the live readings come from.
    The real reading can still differ: this only says when to be ready."""
    d = fetch(f"minutely_15=precipitation&past_minutely_15=2&forecast_minutely_15={hours * 4}")
    now = datetime.now(timezone.utc)
    out = []
    for city, loc in zip(CITIES, d):
        m = loc["minutely_15"]
        rate = [(v or 0.0) * 4 for v in m["precipitation"]]
        for i in range(2, len(rate)):
            ts = datetime.strptime(m["time"][i], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
            if rate[i] >= RAIN and rate[i - 1] < RAIN and rate[i - 2] < RAIN and ts > now - timedelta(minutes=15):
                out.append((ts, city, rate[i], max(rate[i:i + 4])))
    for ts, city, r0, peak in sorted(out):
        local = ts.astimezone()
        print(f"{ts:%H:%M} UTC ({local:%H:%M} local, in {(ts - now).total_seconds() / 60:5.0f} min)  {city:10} starts at {r0:.1f} mm/h, "
              f"peak in the first hour {peak:.1f} mm/h")
    if not out:
        print("no rain start expected in the next", hours, "hours")


def history(days: int):
    """hourly readings of the last N days (real), ingested inline; live readings keep arriving through the stream"""
    d = fetch(f"hourly=temperature_2m,precipitation,snowfall,weather_code,wind_speed_10m&past_days={days}&forecast_days=1")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    rows = []
    for city, loc in zip(CITIES, d):
        h = loc["hourly"]
        for i, t in enumerate(h["time"]):
            if t > now or h["temperature_2m"][i] is None:
                continue
            rows.append(row(city, t, h["temperature_2m"][i], h["precipitation"][i], h["snowfall"][i], h["wind_speed_10m"][i],
                            h["weather_code"][i], 60))
    sf.kql(f".clear table {TABLE} data")
    names = [n for n, _ in COLUMNS]
    for k in range(0, len(rows), 1500):
        lines = "\n".join(",".join(str(r[n]) for n in names) for r in rows[k:k + 1500])
        sf.kql(f".ingest inline into table {TABLE} <|\n{lines}")
        print(f"ingested {min(k + 1500, len(rows))} / {len(rows)}", flush=True)
    rainy = sum(1 for r in rows if r["RainRate"] >= RAIN)
    print(f"{len(rows)} hourly readings, {rainy} rainy city-hours ({rainy / len(rows):.0%})")


def shares() -> tuple[dict, dict]:
    tot_r = sum(v["w"] for v in lo.REGIONS.values())
    city = {c: lo.REGIONS[r]["w"] / tot_r / len(cs) for r, cs in lo.CITIES.items() for c in cs}
    tot_p = sum(p["w"] for p in lo.PRODUCTS)
    prod = {p["name"]: p["w"] / tot_p for p in lo.PRODUCTS}
    return city, prod


def extras(days: int):
    """Weather-driven extra orders for the hourly history, generated inside the Eventhouse.
    Expected extra orders of a product in a city-hour = base orders of that product there * (multiplier - 1)."""
    city, prod = shares()
    info = {p["name"]: p for p in lo.PRODUCTS}
    j = json.dumps
    eff = []                                  # one row per (tag, product): how many extra orders per base order
    for tag, names, mult in EFFECTS:
        for n in names:
            eff.append({"Tag": tag, "Product": n, "Extra": round(prod[n] * (mult - 1), 5), "ProductId": info[n]["id"],
                        "Category": info[n]["cat"], "UnitPrice": info[n]["price"]})
    q = (f".set-or-append {sf.TABLE} <|\n"
         f"let cityShare = dynamic({j(city)});\n"
         f"let cityRegion = dynamic({j(lo.CITY_REGION)});\n"
         f"let regionId = dynamic({j({r: v['id'] for r, v in lo.REGIONS.items()})});\n"
         f"let curve = dynamic({j(lo.CURVE)});\n"
         f"let pay = dynamic({j(_table(lo.PAYMENTS))});\n"
         f"let qty = dynamic({j(_table(lo.QTYS))});\n"
         f"let chan = dynamic({j(_table(lo.CHANNELS))});\n"
         f"let eff = datatable(Tag: string, Product: string, Extra: real, ProductId: long, Category: string, UnitPrice: real)\n"
         f"  [{', '.join(j(e['Tag']) + ', ' + j(e['Product']) + ', ' + str(e['Extra']) + ', ' + str(e['ProductId']) + ', ' + j(e['Category']) + ', ' + str(e['UnitPrice']) for e in eff)}];\n"
         f"{TABLE}\n"
         f"| where IntervalMin == 60 and ReadingTime > ago({days}d) and ReadingTime <= now()\n"
         "| extend HourStart = ReadingTime - 1h\n"
         f"| extend Tag = pack_array(iff(RainRate >= {HEAVY}, 'heavy', iff(RainRate >= {RAIN}, 'rain', '')),\n"
         f"                          iff(TempC < {COLD}, 'cold', ''), iff(TempC > {HOT}, 'hot', ''))\n"
         "| mv-expand Tag to typeof(string)\n"
         "| where Tag != ''\n"
         "| join kind=inner eff on Tag\n"
         f"| extend base = {lo.BASE_RATE} * 60 * todouble(curve[hourofday(HourStart)])\n"
         f"         * iff(dayofweek(HourStart) == 0d or dayofweek(HourStart) == 6d, {lo.WEEKEND}, 1.0) * todouble(cityShare[City])\n"
         "| extend n = toint(round(base * Extra * (0.75 + 0.5 * rand())))\n"
         "| where n > 0\n"
         "| mv-expand i = range(1, n) to typeof(long)\n"
         "| extend OrderTime = HourStart + totimespan(tolong(rand() * 36000000000)), Quantity = tolong(qty[toint(rand() * 100)])\n"
         "| extend Region = tostring(cityRegion[City])\n"
         "| project OrderId = strcat('ORD-', tolong((OrderTime - datetime(1970-01-01)) / 1ms), '-', toint(rand() * 900) + 100),\n"
         "          OrderTime, ProductId, Product, Category, RegionId = tolong(regionId[Region]), Region, City, Quantity, UnitPrice,\n"
         "          SalesAmount = round(Quantity * UnitPrice, 2), PaymentMethod = tostring(pay[toint(rand() * 100)]),\n"
         "          Channel = tostring(chan[toint(rand() * 100)])")
    sf.kql(q)
    print("weather-driven extra orders appended to", sf.TABLE)


def _table(pairs, size=100):
    tot = sum(w for _, w in pairs)
    out = []
    for v, w in pairs:
        out += [v] * round(size * w / tot)
    return (out + [pairs[0][0]] * size)[:size]


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "setup":
        setup()
    elif cmd == "endpoint":
        endpoint()
    elif cmd == "now":
        show(current())
    elif cmd == "send":
        rows = current()
        print("HTTP", post(rows), len(rows), "readings")
        show(rows)
    elif cmd == "run":
        run(float(a[1]) if len(a) > 1 else None)
    elif cmd == "forecast":
        forecast(int(a[1]) if len(a) > 1 else 8)
    elif cmd == "history":
        history(int(a[1]) if len(a) > 1 else 28)
    elif cmd == "extras":
        extras(int(a[1]) if len(a) > 1 else 28)
    elif cmd == "kql":
        r = sf.kql(a[1])
        t = (r.get("Tables") or [{}])[0]
        print([c["ColumnName"] for c in t.get("Columns", [])])
        for rw in t.get("Rows", [])[:60]:
            print(rw)
    else:
        sys.exit(__doc__)
