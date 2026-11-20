# ---- THE STORE: run this cell. It sends orders until RUN_MINUTES pass, or until you press Stop. ----
# A pretend online store (Aurora Outdoor). Every order is one small JSON message, sent to the Eventstream's custom endpoint.
import base64, hashlib, hmac, json, random, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
import notebookutils

PRODUCTS = [  # product number, name, category, price, how popular
    (1, "Summit 2P Tent", "Camping", 331, 94), (2, "Basecamp 6P Tent", "Camping", 667, 50),
    (3, "Arctic Sleeping Bag", "Camping", 217, 70), (4, "Trailhead 45L Pack", "Hiking", 179, 120),
    (5, "Ridge Trekking Poles", "Hiking", 85, 85), (6, "Alpine Hiking Boots", "Hiking", 208, 104),
    (7, "Storm Shell Jacket", "Apparel", 247, 101), (8, "Thermal Base Layer", "Apparel", 75, 133),
    (9, "Summit Fleece", "Apparel", 122, 114), (10, "Glacier Water Bottle", "Accessories", 33, 154),
    (11, "Headlamp Pro", "Accessories", 56, 120), (12, "Trail First-Aid Kit", "Accessories", 43, 92)]
REGIONS = {  # name: (share of orders, cities)
    "North America": (39, ["Vancouver", "Seattle", "Denver", "Toronto", "New York"]),
    "Europe": (27, ["London", "Berlin", "Oslo", "Madrid", "Zurich"]),
    "Asia Pacific": (16, ["Tokyo", "Sydney", "Auckland", "Singapore"]),
    "Latin America": (9, ["Santiago", "Bogota", "Sao Paulo"])}
PAYMENTS = [("Card", 62), ("PayPal", 20), ("Apple Pay", 12), ("Bank transfer", 6)]
QUANTITIES = [(1, 70), (2, 22), (3, 8)]
CHANNELS = [("Web", 64), ("App", 36)]

# ---------------------------------------------------------------- where to send: ask Fabric, nothing to paste
WORKSPACE = notebookutils.runtime.context["currentWorkspaceId"]
FABRIC = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE}/"


def fabric(path):
    """One read from the Fabric REST API, as the person who runs this notebook."""
    request = urllib.request.Request(FABRIC + path)
    request.add_header("Authorization", "Bearer " + notebookutils.credentials.getToken("pbi"))
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def endpoint(name):
    """The address and the key of the Eventstream's custom endpoint."""
    streams = [s for s in fabric("eventstreams").get("value", []) if s["displayName"] == name]
    if not streams:
        raise ValueError(f"There is no Eventstream called {name} in this workspace. Check EVENTSTREAM_NAME in the first cell.")
    for _ in range(20):
        try:
            sources = fabric(f"eventstreams/{streams[0]['id']}/topology").get("sources", [])
            custom = next(s for s in sources if s["type"] == "CustomEndpoint")
            keys = fabric(f"eventstreams/{streams[0]['id']}/sources/{custom['id']}/connection")
            conn = dict(p.split("=", 1) for p in keys["accessKeys"]["primaryConnectionString"].split(";") if "=" in p)
            conn["url"] = "https://" + conn["Endpoint"].replace("sb://", "").strip("/") + "/" + conn["EntityPath"]
            return conn
        except (urllib.error.URLError, StopIteration, KeyError):
            time.sleep(6)                    # a new Eventstream needs a minute after Publish
    raise RuntimeError(f"{name} has no custom endpoint yet. Add one, click Publish, wait a minute and run this cell again.")


CONN = endpoint(EVENTSTREAM_NAME)


def send(events):
    uri = urllib.parse.quote_plus(CONN["url"])
    expiry = str(int(time.time()) + 3600)
    signature = base64.b64encode(hmac.new(CONN["SharedAccessKey"].encode(), f"{uri}\n{expiry}".encode(), hashlib.sha256).digest()).decode()
    token = f"SharedAccessSignature sr={uri}&sig={urllib.parse.quote_plus(signature)}&se={expiry}&skn={CONN['SharedAccessKeyName']}"
    body = json.dumps([{"Body": json.dumps(e)} for e in events]).encode("utf-8")
    for attempt in range(5):
        request = urllib.request.Request(CONN["url"] + "/messages?timeout=60&api-version=2014-01", data=body, method="POST")
        request.add_header("Authorization", token)
        request.add_header("Content-Type", "application/vnd.microsoft.servicebus.json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status
        except (urllib.error.URLError, TimeoutError):
            time.sleep(5)
    raise RuntimeError("The Eventstream did not accept the orders. Wait a minute and run this cell again.")


def pick(pairs):
    return random.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


def order():
    number, product, category, price, _ = random.choices(PRODUCTS, weights=[p[4] for p in PRODUCTS])[0]
    region = random.choices(list(REGIONS), weights=[r[0] for r in REGIONS.values()])[0]
    quantity = pick(QUANTITIES)
    now = datetime.now(timezone.utc)
    return {"OrderNumber": f"ORD-{int(now.timestamp() * 1000)}-{random.randint(100, 999)}",
            "OrderTime": now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "Product": product, "Category": category, "Region": region, "City": random.choice(REGIONS[region][1]),
            "Quantity": quantity, "UnitPrice": price, "SalesAmount": quantity * price,
            "PaymentMethod": pick(PAYMENTS), "Channel": pick(CHANNELS)}


print(f"The store is open. Orders go to the Eventstream {EVENTSTREAM_NAME}.")
sent, started, last_line = 0, time.time(), 0.0
while time.time() - started < RUN_MINUTES * 60:
    tick = time.time()
    count = max(1, round(ORDERS_PER_MINUTE / 12 * random.uniform(0.6, 1.4)))        # one small batch every 5 seconds
    send([order() for _ in range(count)])
    sent += count
    if tick - last_line >= 30:
        print(f"{datetime.now(timezone.utc):%H:%M:%S} UTC  orders sent so far: {sent}")
        last_line = tick
    time.sleep(max(0.0, 5 - (time.time() - tick)))
print("The store is closed. Orders sent:", sent)
