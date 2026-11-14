"""Local relay for the phone page (video 11): serves phone/index.html and sends real orders to the Eventstream.

  python -I phone_server.py            http://127.0.0.1:8711/

  GET  /                 the phone page
  GET  /config           products and cities for the page
  POST /order            {"product": "...", "city": "...", "qty": 1} -> sends ONE order event, returns it
  GET  /seen?id=ORD-...  asks the Eventhouse whether that order has arrived; returns the lag in seconds
  GET  /stats            orders and sales in the last 60 minutes (for the small counter on the page)

Only listens on 127.0.0.1. The Eventstream key stays in ~/.pbi101 (read by live_orders.py); nothing secret is
sent to the page.
"""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import live_orders as lo  # noqa: E402
import setup_fabric as sf  # noqa: E402

PORT = 8711
PHONE_CHANNEL = "Phone (this demo)"      # so the dashboard can show the taps on their own tile
SHOP = ["Storm Shell Jacket", "Arctic Sleeping Bag", "Summit 2P Tent", "Alpine Hiking Boots", "Headlamp Pro",
        "Glacier Water Bottle"]


def rows(q: str):
    return (sf.kql(q).get("Tables") or [{}])[0].get("Rows", [])


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):          # quiet
        pass

    def send(self, obj, status=200, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        try:
            if u.path in ("/", "/index.html"):
                return self.send((HERE / "phone" / "index.html").read_bytes(), ctype="text/html; charset=utf-8")
            if u.path == "/config":
                prods = [{"name": p["name"], "cat": p["cat"], "price": p["price"]} for n in SHOP
                         for p in lo.PRODUCTS if p["name"] == n]
                return self.send({"products": prods, "cities": sorted(lo.CITY_REGION)})
            if u.path == "/seen":
                oid = parse_qs(u.query).get("id", [""])[0]
                if not oid.startswith("ORD-") or not oid.replace("-", "").isalnum():
                    return self.send({"error": "bad id"}, 400)
                r = rows(f"OrdersLive | where OrderTime > ago(15m) and OrderId == '{oid}' "
                         "| project lag = (ingestion_time() - OrderTime) / 1s | take 1")
                return self.send({"seen": bool(r), "lag_s": round(r[0][0], 1) if r else None})
            if u.path == "/stats":
                r = rows("OrdersLive | where OrderTime > ago(60m) | summarize orders = count(), sales = round(sum(SalesAmount))")
                return self.send({"orders": r[0][0], "sales": r[0][1]} if r else {})
            self.send({"error": "not found"}, 404)
        except SystemExit as e:             # setup_fabric exits on an HTTP error
            self.send({"error": str(e)[:200]}, 502)

    def do_POST(self):
        if urlparse(self.path).path != "/order":
            return self.send({"error": "not found"}, 404)
        try:
            d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
            o = lo.order(lo.by_name(d["product"]), d["city"], max(1, min(9, int(d.get("qty", 1)))), d.get("payment"))
            o["Channel"] = PHONE_CHANNEL
            status = lo.post([o])
            self.send({"status": status, "order": o}, 200 if status < 300 else 502)
        except (KeyError, ValueError, SystemExit) as e:
            self.send({"error": str(e)[:200]}, 400)


if __name__ == "__main__":
    print(f"phone page: http://127.0.0.1:{PORT}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
