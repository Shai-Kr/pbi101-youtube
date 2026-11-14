# ---- THE STORE: run this cell. It keeps sending orders until RUN_MINUTES pass, or until you press Stop. ----
import base64, hashlib, hmac, json, random, time, urllib.parse, urllib.request
from datetime import datetime, timezone

PRODUCTS = [  # id, name, category, price, how popular
    (1, "Summit 2P Tent", "Camping", 331, 94), (2, "Basecamp 6P Tent", "Camping", 667, 50),
    (3, "Arctic Sleeping Bag", "Camping", 217, 70), (4, "Trailhead 45L Pack", "Hiking", 179, 120),
    (5, "Ridge Trekking Poles", "Hiking", 85, 85), (6, "Alpine Hiking Boots", "Hiking", 208, 104),
    (7, "Storm Shell Jacket", "Apparel", 247, 101), (8, "Thermal Base Layer", "Apparel", 75, 133),
    (9, "Summit Fleece", "Apparel", 122, 114), (10, "Glacier Water Bottle", "Accessories", 33, 154),
    (11, "Headlamp Pro", "Accessories", 56, 120), (12, "Trail First-Aid Kit", "Accessories", 43, 92)]
REGIONS = {  # name: (id, share of orders, cities)
    "North America": (1, 39, ["Vancouver", "Seattle", "Denver", "Toronto", "New York"]),
    "Europe": (2, 27, ["London", "Berlin", "Oslo", "Madrid", "Zurich"]),
    "Asia Pacific": (3, 16, ["Tokyo", "Sydney", "Auckland", "Singapore"]),
    "Latin America": (4, 9, ["Santiago", "Bogota", "Sao Paulo"])}
PAYMENTS = [("Card", 62), ("PayPal", 20), ("Apple Pay", 12), ("Bank transfer", 6)]
QUANTITIES = [(1, 70), (2, 22), (3, 8)]
CHANNELS = [("Web", 64), ("App", 36)]
# busier in the European evening, quieter at night (hours are UTC)
CURVE = [0.62, 0.55, 0.50, 0.48, 0.50, 0.56, 0.66, 0.78, 0.90, 1.00, 1.08, 1.14,
         1.20, 1.26, 1.32, 1.38, 1.42, 1.45, 1.42, 1.34, 1.20, 1.02, 0.84, 0.70]

conn = dict(part.split("=", 1) for part in CONNECTION_STRING.strip().split(";") if "=" in part)
if "Endpoint" not in conn or "EntityPath" not in conn:
    raise ValueError("Paste the connection string of your Eventstream into CONNECTION_STRING (the cell above), then run both cells.")
NAMESPACE = conn["Endpoint"].replace("sb://", "").strip("/")
URL = f"https://{NAMESPACE}/{conn['EntityPath']}"


def token():
    uri = urllib.parse.quote_plus(URL)
    expiry = str(int(time.time()) + 3600)
    signature = base64.b64encode(hmac.new(conn["SharedAccessKey"].encode(), f"{uri}\n{expiry}".encode(), hashlib.sha256).digest()).decode()
    return f"SharedAccessSignature sr={uri}&sig={urllib.parse.quote_plus(signature)}&se={expiry}&skn={conn['SharedAccessKeyName']}"


def send(events):
    body = json.dumps([{"Body": json.dumps(e)} for e in events]).encode("utf-8")
    request = urllib.request.Request(URL + "/messages?timeout=60&api-version=2014-01", data=body, method="POST")
    request.add_header("Authorization", token())
    request.add_header("Content-Type", "application/vnd.microsoft.servicebus.json")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status


def pick(pairs):
    return random.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


def order():
    pid, product, category, price, _ = random.choices(PRODUCTS, weights=[p[4] for p in PRODUCTS])[0]
    region = random.choices(list(REGIONS), weights=[r[1] for r in REGIONS.values()])[0]
    quantity = pick(QUANTITIES)
    now = datetime.now(timezone.utc)
    return {"OrderId": f"ORD-{int(now.timestamp() * 1000)}-{random.randint(100, 999)}",
            "OrderTime": now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "ProductId": pid, "Product": product, "Category": category,
            "RegionId": REGIONS[region][0], "Region": region, "City": random.choice(REGIONS[region][2]),
            "Quantity": quantity, "UnitPrice": price, "SalesAmount": quantity * price,
            "PaymentMethod": pick(PAYMENTS), "Channel": pick(CHANNELS)}


print("The store is open." + (f" Muted region: {MUTE_REGION}." if MUTE_REGION else ""))
sent, started = 0, time.time()
while time.time() - started < RUN_MINUTES * 60:
    tick = time.time()
    now = datetime.now(timezone.utc)
    busy = CURVE[now.hour] * (1.12 if now.weekday() >= 5 else 1.0)
    count = max(1, round(ORDERS_PER_MINUTE * busy / 6 * random.uniform(0.6, 1.4)))      # one batch every 10 seconds
    batch = [o for o in (order() for _ in range(count)) if o["Region"] != MUTE_REGION]
    if batch:
        send(batch)
        sent += len(batch)
    if int((tick - started) // 10) % 6 == 0:
        print(f"{now:%H:%M:%S} UTC  orders sent so far: {sent}")
    time.sleep(max(0.0, 10 - (time.time() - tick)))
print("The store is closed. Orders sent:", sent)
