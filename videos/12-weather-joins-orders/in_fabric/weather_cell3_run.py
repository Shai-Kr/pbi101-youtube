# ---- THE STORE + THE WEATHER FEED: run this cell. It runs until RUN_MINUTES pass, or until you press Stop. ----
# (Run the cell above it first: it defines the cities and the helper functions.)
import math, random

PRODUCTS = [  # id, name, category, price, how popular
    (1, "Summit 2P Tent", "Camping", 331, 94), (2, "Basecamp 6P Tent", "Camping", 667, 50),
    (3, "Arctic Sleeping Bag", "Camping", 217, 70), (4, "Trailhead 45L Pack", "Hiking", 179, 120),
    (5, "Ridge Trekking Poles", "Hiking", 85, 85), (6, "Alpine Hiking Boots", "Hiking", 208, 104),
    (7, "Storm Shell Jacket", "Apparel", 247, 101), (8, "Thermal Base Layer", "Apparel", 75, 133),
    (9, "Summit Fleece", "Apparel", 122, 114), (10, "Glacier Water Bottle", "Accessories", 33, 154),
    (11, "Headlamp Pro", "Accessories", 56, 120), (12, "Trail First-Aid Kit", "Accessories", 43, 92)]
REGIONS = {"North America": (1, 39), "Europe": (2, 27), "Asia Pacific": (3, 16), "Latin America": (4, 9)}   # id, share of orders
PAYMENTS = [("Card", 62), ("PayPal", 20), ("Apple Pay", 12), ("Bank transfer", 6)]
QUANTITIES = [(1, 70), (2, 22), (3, 8)]
CHANNELS = [("Web", 64), ("App", 36)]
CURVE = [0.62, 0.55, 0.50, 0.48, 0.50, 0.56, 0.66, 0.78, 0.90, 1.00, 1.08, 1.14,
         1.20, 1.26, 1.32, 1.38, 1.42, 1.45, 1.42, 1.34, 1.20, 1.02, 0.84, 0.70]
# What the SIMULATED shoppers do with the REAL weather in their city:
RAIN, HEAVY_RAIN, COLD, HOT = 0.4, 2.0, 5.0, 26.0             # mm per hour, mm per hour, degrees C, degrees C
EFFECTS = {"rain": (["Storm Shell Jacket"], 3.0), "heavy rain": (["Storm Shell Jacket"], 4.0),
           "cold": (["Thermal Base Layer", "Summit Fleece"], 1.8), "hot": (["Glacier Water Bottle"], 2.2)}
CITY_NAMES = {region: [c for c, v in CITIES.items() if v[2] == region] for region in REGIONS}
TOTAL_POPULAR = sum(p[4] for p in PRODUCTS)
TOTAL_SHARE = sum(r[1] for r in REGIONS.values())


def pick(pairs):
    return random.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


def order(product=None, city=None):
    pid, name, category, price, _ = product or random.choices(PRODUCTS, weights=[p[4] for p in PRODUCTS])[0]
    if city is None:
        region = random.choices(list(REGIONS), weights=[r[1] for r in REGIONS.values()])[0]
        city = random.choice(CITY_NAMES[region])
    region = CITIES[city][2]
    quantity = pick(QUANTITIES)
    now = datetime.now(timezone.utc)
    return {"OrderId": f"ORD-{int(now.timestamp() * 1000)}-{random.randint(100, 999)}",
            "OrderTime": now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "ProductId": pid, "Product": name, "Category": category, "RegionId": REGIONS[region][0], "Region": region,
            "City": city, "Quantity": quantity, "UnitPrice": price, "SalesAmount": quantity * price,
            "PaymentMethod": pick(PAYMENTS), "Channel": pick(CHANNELS)}


def weather_now():
    data = weather_service("current=temperature_2m,precipitation,snowfall,weather_code,wind_speed_10m")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    readings = []
    for city, place in zip(CITIES, data):
        c = place["current"]
        readings.append(reading(city, stamp, c["temperature_2m"], c["precipitation"], c["snowfall"], c["wind_speed_10m"],
                                c["weather_code"], int(c["interval"] // 60)))
    return readings


def what_weather_does(r):
    tags = ["heavy rain"] if r["RainRate"] >= HEAVY_RAIN else ["rain"] if r["RainRate"] >= RAIN else []
    if r["TempC"] is not None and r["TempC"] < COLD:
        tags.append("cold")
    if r["TempC"] is not None and r["TempC"] > HOT:
        tags.append("hot")
    return tags


def how_many(expected):                     # a random whole number around "expected"
    limit, count, p = math.exp(-expected), 0, 1.0
    while expected > 0:
        p *= random.random()
        if p <= limit:
            break
        count += 1
    return count


orders = endpoint(CONNECTION_STRING, "CONNECTION_STRING")
print("The store is open, and the weather feed is on." + (f" Muted region: {MUTE_REGION}." if MUTE_REGION else ""))
sent = extra = 0
latest, last_sent, last_fetch, started = {}, {}, 0.0, time.time()
while time.time() - started < RUN_MINUTES * 60:
    tick = time.time()
    if tick - last_fetch >= 300:                                    # every 5 minutes: ask the weather service
        try:
            readings = weather_now()
            changed = [r for r in readings
                       if last_sent.get(r["City"], (None, 0))[0] != (r["TempC"], r["PrecipMm"], r["WeatherCode"], r["WindKmh"])
                       or tick - last_sent[r["City"]][1] > 870]     # send when the values changed, or every 15 minutes
            if changed:
                send(weather, changed)
                for r in changed:
                    last_sent[r["City"]] = ((r["TempC"], r["PrecipMm"], r["WeatherCode"], r["WindKmh"]), tick)
            latest = {r["City"]: r for r in readings}
            raining = [c for c, r in latest.items() if r["RainRate"] >= RAIN]
            print(f"{datetime.now(timezone.utc):%H:%M:%S} UTC  orders: {sent} + {extra} because of the weather | "
                  f"weather readings sent: {len(changed)} | raining now: {', '.join(raining) or 'nowhere'}")
        except Exception as problem:                                # a failed call must not stop the store
            print("weather call failed, will try again:", str(problem)[:120])
        last_fetch = tick
    now = datetime.now(timezone.utc)
    busy = CURVE[now.hour] * (1.12 if now.weekday() >= 5 else 1.0)
    per_batch = ORDERS_PER_MINUTE * busy / 6                         # one batch every 10 seconds
    batch = [order() for _ in range(max(1, round(per_batch * random.uniform(0.6, 1.4))))]
    weather_orders = []
    for city, r in latest.items():                                  # the weather-driven extra orders
        city_share = REGIONS[CITIES[city][2]][1] / TOTAL_SHARE / len(CITY_NAMES[CITIES[city][2]])
        for tag in what_weather_does(r):
            names, times = EFFECTS[tag]
            for product in (p for p in PRODUCTS if p[1] in names):
                expected = per_batch * city_share * product[4] / TOTAL_POPULAR * (times - 1)
                weather_orders += [order(product, city) for _ in range(how_many(expected))]
    batch = [o for o in batch if o["Region"] != MUTE_REGION]
    weather_orders = [o for o in weather_orders if o["Region"] != MUTE_REGION]
    if batch or weather_orders:
        send(orders, batch + weather_orders)
        sent += len(batch)
        extra += len(weather_orders)
    time.sleep(max(0.0, 10 - (time.time() - tick)))
print("The store is closed. Orders sent:", sent, "+", extra, "because of the weather")
