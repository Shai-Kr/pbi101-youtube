"""Simulated Aurora online store: sends order events to the AuroraOrders Eventstream (custom endpoint), stdlib only.

  python -I live_orders.py send 5                         5 orders right now
  python -I live_orders.py one "Storm Shell Jacket" Vancouver [qty]     one chosen order (what the phone page sends)
  python -I live_orders.py run 30 [minutes] [--mute-region Europe] [--mute-payment Card] [--boost "Storm Shell Jacket" Vancouver 4]
                                                          a steady flow of about 30 orders a minute (default: until stopped)

  python -I live_orders.py backfill 28                    history: fill OrdersLive with 28 days of orders up to now, generated
                                                          inside the Eventhouse (clears the table first)

The flow follows an hour-of-day curve (CURVE, UTC) so "now" is comparable with the same hour in the history.
The endpoint's key is read from ~/.pbi101/eventstream_orders.json (outside the repo) and never printed.
Products and regions come from the Aurora Sales model (aurora_dims.json). The store is simulated: say so on camera.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECRET = Path.home() / ".pbi101" / "eventstream_orders.json"
DIMS = json.loads((HERE / "aurora_dims.json").read_text(encoding="utf-8"))
PRODUCTS = [{"id": p["Products[Product ID]"], "name": p["Products[Product]"], "cat": p["Products[Category]"],
             "price": round(p["[Price]"], 0), "w": p["[Units]"]} for p in DIMS["products"]]
REGIONS = {r["Regions[Region]"]: {"id": r["Regions[Region ID]"], "w": r["[Orders]"]} for r in DIMS["regions"]}
CITIES = {"North America": ["Vancouver", "Seattle", "Denver", "Toronto", "New York"],
          "Europe": ["London", "Berlin", "Oslo", "Madrid", "Zurich"],
          "Asia Pacific": ["Tokyo", "Sydney", "Auckland", "Singapore"],
          "Latin America": ["Santiago", "Bogota", "Sao Paulo"]}
CITY_REGION = {c: r for r, cs in CITIES.items() for c in cs}
PAYMENTS = [("Card", 62), ("PayPal", 20), ("Apple Pay", 12), ("Bank transfer", 6)]
QTYS = [(1, 70), (2, 22), (3, 8)]
CHANNELS = [("Web", 64), ("App", 36)]
# Orders per minute = base rate x CURVE[hour, UTC] x weekend factor. One global store, busiest in the European evening.
CURVE = [0.62, 0.55, 0.50, 0.48, 0.50, 0.56, 0.66, 0.78, 0.90, 1.00, 1.08, 1.14,
         1.20, 1.26, 1.32, 1.38, 1.42, 1.45, 1.42, 1.34, 1.20, 1.02, 0.84, 0.70]
WEEKEND = 1.12
BASE_RATE = 20.0
_conn: dict = {}


def conn() -> dict:
    if not _conn:
        c = json.loads(SECRET.read_text(encoding="utf-8"))
        parts = dict(kv.split("=", 1) for kv in c["accessKeys"]["primaryConnectionString"].split(";") if "=" in kv)
        _conn.update(ns=c["fullyQualifiedNamespace"], hub=c["eventHubName"], key_name=parts["SharedAccessKeyName"],
                     key=parts["SharedAccessKey"])
    return _conn


def sas(ttl: int = 3600) -> str:
    c = conn()
    uri = urllib.parse.quote_plus(f"https://{c['ns']}/{c['hub']}")
    exp = str(int(time.time()) + ttl)
    sig = base64.b64encode(hmac.new(c["key"].encode(), f"{uri}\n{exp}".encode(), hashlib.sha256).digest()).decode()
    return f"SharedAccessSignature sr={uri}&sig={urllib.parse.quote_plus(sig)}&se={exp}&skn={c['key_name']}"


_tok = {"v": "", "t": 0.0}


def post(events: list[dict]) -> int:
    c = conn()
    if time.time() - _tok["t"] > 3000:
        _tok.update(v=sas(), t=time.time())
    body = json.dumps([{"Body": json.dumps(e)} for e in events]).encode("utf-8")
    req = urllib.request.Request(f"https://{c['ns']}/{c['hub']}/messages?timeout=60&api-version=2014-01", data=body, method="POST")
    req.add_header("Authorization", _tok["v"])
    req.add_header("Content-Type", "application/vnd.microsoft.servicebus.json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        print("send failed:", e.code, e.read()[:200].decode("utf-8", "replace"))
        return e.code


def pick(pairs):
    return random.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


def order(product: dict | None = None, city: str | None = None, qty: int | None = None, payment: str | None = None) -> dict:
    p = product or random.choices(PRODUCTS, weights=[x["w"] for x in PRODUCTS])[0]
    if not city:
        region = random.choices(list(REGIONS), weights=[REGIONS[r]["w"] for r in REGIONS])[0]
        city = random.choice(CITIES[region])
    region = CITY_REGION[city]
    q = qty or pick(QTYS)
    now = datetime.now(timezone.utc)
    return {"OrderId": f"ORD-{int(now.timestamp() * 1000)}-{random.randint(100, 999)}",
            "OrderTime": now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "ProductId": p["id"], "Product": p["name"], "Category": p["cat"],
            "RegionId": REGIONS[region]["id"], "Region": region, "City": city,
            "Quantity": q, "UnitPrice": p["price"], "SalesAmount": round(q * p["price"], 2),
            "PaymentMethod": payment or pick(PAYMENTS), "Channel": pick(CHANNELS)}


def by_name(name: str) -> dict:
    m = [p for p in PRODUCTS if p["name"].lower() == name.lower()]
    if not m:
        sys.exit("unknown product: " + name)
    return m[0]


def run(rate: float, minutes: float | None, mute_region: str | None, mute_payment: str | None, boost):
    end = time.time() + minutes * 60 if minutes else None
    sent = 0
    while not end or time.time() < end:
        t0 = time.time()
        batch = []
        now = datetime.now(timezone.utc)
        f = CURVE[now.hour] * (WEEKEND if now.weekday() >= 5 else 1.0)
        n = max(1, round(rate * f / 6 * random.uniform(0.6, 1.4)))      # one batch every 10 seconds
        for _ in range(n):
            o = order()
            if mute_region and o["Region"] == mute_region:
                continue
            if mute_payment and o["PaymentMethod"] == mute_payment:
                continue
            batch.append(o)
        if boost:
            for _ in range(int(boost[2])):
                batch.append(order(by_name(boost[0]), boost[1]))
        if batch:
            post(batch)
            sent += len(batch)
        print(f"\r{datetime.now().strftime('%H:%M:%S')} sent {sent}", end="", flush=True)
        time.sleep(max(0.0, 10 - (time.time() - t0)))


def backfill(days: int):
    """History generated inside the Eventhouse with one KQL statement per week (fast, no events sent)."""
    sys.path.insert(0, str(HERE))          # python -I leaves the script folder off the path
    import setup_fabric as sf

    def table(pairs, size=1000):
        tot = sum(w for _, w in pairs)
        out = []
        for v, w in pairs:
            out += [v] * round(size * w / tot)
        return (out + [pairs[0][0]] * size)[:size]

    prod = table([(i, p["w"]) for i, p in enumerate(PRODUCTS)])
    cities = table([(c, REGIONS[r]["w"] / len(cs)) for r, cs in CITIES.items() for c in cs])
    j = json.dumps
    lets = (f"let prod = dynamic({j(prod)});\n"
            f"let pid = dynamic({j([p['id'] for p in PRODUCTS])});\n"
            f"let pname = dynamic({j([p['name'] for p in PRODUCTS])});\n"
            f"let pcat = dynamic({j([p['cat'] for p in PRODUCTS])});\n"
            f"let pprice = dynamic({j([p['price'] for p in PRODUCTS])});\n"
            f"let cities = dynamic({j(cities)});\n"
            f"let cityRegion = dynamic({j(CITY_REGION)});\n"
            f"let regionId = dynamic({j({r: v['id'] for r, v in REGIONS.items()})});\n"
            f"let pay = dynamic({j(table(PAYMENTS, 100))});\n"
            f"let qty = dynamic({j(table(QTYS, 100))});\n"
            f"let chan = dynamic({j(table(CHANNELS, 100))});\n"
            f"let curve = dynamic({j(CURVE)});\n")
    sf.kql(f".clear table {sf.TABLE} data")
    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = end - __import__("datetime").timedelta(days=days)
    step = __import__("datetime").timedelta(days=4)
    t = start
    while t < end:
        t2 = min(t + step, end)
        q = (f".set-or-append {sf.TABLE} <|\n" + lets +
             f"range Minute from datetime({t:%Y-%m-%dT%H:%M:%SZ}) to datetime({t2:%Y-%m-%dT%H:%M:%SZ}) - 1m step 1m\n"
             f"| extend f = todouble(curve[hourofday(Minute)]) * iff(dayofweek(Minute) == 0d or dayofweek(Minute) == 6d, {WEEKEND}, 1.0)\n"
             f"| extend n = toint(round({BASE_RATE} * f * (0.75 + 0.5 * rand())))\n"
             "| where n > 0\n"
             "| mv-expand i = range(1, n) to typeof(long)\n"
             "| extend OrderTime = Minute + totimespan(tolong(rand() * 600000000)), pi = toint(prod[toint(rand() * 1000)]),\n"
             "         City = tostring(cities[toint(rand() * 1000)]), Quantity = tolong(qty[toint(rand() * 100)])\n"
             "| extend Region = tostring(cityRegion[City]), UnitPrice = todouble(pprice[pi])\n"
             "| project OrderId = strcat('ORD-', tolong((OrderTime - datetime(1970-01-01)) / 1ms), '-', toint(rand() * 900) + 100),\n"
             "          OrderTime, ProductId = tolong(pid[pi]), Product = tostring(pname[pi]), Category = tostring(pcat[pi]),\n"
             "          RegionId = tolong(regionId[Region]), Region, City, Quantity, UnitPrice, SalesAmount = round(Quantity * UnitPrice, 2),\n"
             "          PaymentMethod = tostring(pay[toint(rand() * 100)]), Channel = tostring(chan[toint(rand() * 100)])")
        sf.kql(q)
        print(f"{t:%m-%d} .. {t2:%m-%d %H:%M} ok", flush=True)
        t = t2


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "send":
        evs = [order() for _ in range(int(a[1]) if len(a) > 1 else 1)]
        print(post(evs), len(evs), "orders")
        print(json.dumps(evs[0]))
    elif a[0] == "one":
        e = order(by_name(a[1]), a[2], int(a[3]) if len(a) > 3 else 1)
        print(post([e]), json.dumps(e))
    elif a[0] == "backfill":
        backfill(int(a[1]) if len(a) > 1 else 28)
    elif a[0] == "run":
        def opt(flag, n=1):
            if flag in a:
                i = a.index(flag)
                return a[i + 1] if n == 1 else a[i + 1:i + 1 + n]
            return None
        mins = float(a[2]) if len(a) > 2 and not a[2].startswith("--") else None
        run(float(a[1]), mins, opt("--mute-region"), opt("--mute-payment"), opt("--boost", 3))
    else:
        sys.exit(__doc__)
