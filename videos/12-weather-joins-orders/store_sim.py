"""Video 12: the simulated Aurora store, now with shoppers who react to the real weather in their city.

  python -I store_sim.py run 20 [minutes]     the same steady flow as video 11 (about 20 orders a minute before the
                                              hour-of-day curve) plus weather-driven orders
  python -I store_sim.py effects              what the weather is doing to the store right now (nothing is sent)

It reads weather_state.json, which `weather.py run` rewrites every 5 minutes with the latest real reading per city.
Per city (the same rule as the history, see weather.py): raining -> Storm Shell Jacket x 3 (x 4 in heavy rain),
colder than 5 C -> Thermal Base Layer and Summit Fleece x 1.8, warmer than 26 C -> Glacier Water Bottle x 2.2.
The extra orders are added on top of the normal flow; a state file older than 30 minutes is ignored.
The store is simulated; the weather is real: say both on camera.
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import weather as wx  # noqa: E402  (also puts video 11's folder on the path)

lo = wx.lo
MULT = {tag: (names, mult) for tag, names, mult in wx.EFFECTS}


def state() -> dict:
    try:
        s = json.loads(wx.STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return s["cities"] if time.time() - s.get("at", 0) < 1800 else {}


def poisson(lam: float) -> int:
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= random.random()
        if p <= limit:
            return k
        k += 1


def weather_orders(rate: float, f: float) -> list[dict]:
    """extra orders for one 10-second batch"""
    city_share, prod_share = wx.shares()
    out = []
    for city, w in state().items():
        for tag in w.get("tags", []):
            names, mult = MULT[tag]
            for name in names:
                lam = rate * f / 6 * city_share[city] * prod_share[name] * (mult - 1)
                for _ in range(poisson(lam)):
                    out.append(lo.order(lo.by_name(name), city))
    return out


def run(rate: float, minutes: float | None):
    end = time.time() + minutes * 60 if minutes else None
    sent = extra = 0
    while not end or time.time() < end:
        t0 = time.time()
        now = datetime.now(timezone.utc)
        f = lo.CURVE[now.hour] * (lo.WEEKEND if now.weekday() >= 5 else 1.0)
        n = max(1, round(rate * f / 6 * random.uniform(0.6, 1.4)))
        batch = [lo.order() for _ in range(n)]
        wo = weather_orders(rate, f)
        if lo.post(batch + wo) < 300:
            sent += len(batch)
            extra += len(wo)
        print(f"\r{datetime.now():%H:%M:%S} sent {sent} + {extra} weather-driven", end="", flush=True)
        time.sleep(max(0.0, 10 - (time.time() - t0)))


def effects():
    st = state()
    if not st:
        sys.exit("no fresh weather_state.json (run `weather.py run` first)")
    for city, w in st.items():
        if w["tags"]:
            print(f'{city:10} {w["TempC"]:5.1f} C  rain {w["RainRate"]:4.1f} mm/h  -> '
                  + "; ".join(f'{", ".join(MULT[t][0])} x {MULT[t][1]}' for t in w["tags"]))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "run":
        run(float(a[1]) if len(a) > 1 else 20.0, float(a[2]) if len(a) > 2 else None)
    elif a and a[0] == "effects":
        effects()
    else:
        sys.exit(__doc__)
