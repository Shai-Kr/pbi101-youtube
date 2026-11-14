"""Small Fabric REST helper for the scripts in this repo (stdlib only). The token comes from the Azure CLI: run `az login` first.

Config: a JSON file with your own ids. Default location ~/.pbi101/fabric_env.json, or set FABRIC_ENV_FILE.
See fabric_env.example.json next to this file. Nothing in this repo contains real ids or keys.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENV_FILE = Path(os.environ.get("FABRIC_ENV_FILE", Path.home() / ".pbi101" / "fabric_env.json"))
ENV = json.loads(ENV_FILE.read_text(encoding="utf-8"))
WS = ENV["workspace"]["id"]
FABRIC = "https://api.fabric.microsoft.com/v1/"
_TOK: dict[str, str] = {}


def token(resource: str) -> str:
    """an access token for `resource` from the Azure CLI (optionally for one tenant: "tenant_id" in the config)"""
    if resource not in _TOK:
        cmd = [shutil.which("az") or "az", "account", "get-access-token", "--resource", resource, "--query", "accessToken",
               "-o", "tsv", "--only-show-errors"]
        if ENV.get("tenant_id"):
            cmd += ["--tenant", ENV["tenant_id"]]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit(r.stderr.strip())
        _TOK[resource] = r.stdout.strip()
    return _TOK[resource]


def call(method: str, url: str, body=None, resource="https://api.fabric.microsoft.com", poll=True):
    """One REST call. Returns (status, parsed body). A 202 from Fabric is polled until the operation ends."""
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method.upper())
    req.add_header("Authorization", "Bearer " + token(resource))
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status, headers, raw = r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw.decode("utf-8", "replace")
    out = json.loads(raw) if raw.strip() else None
    if status == 202 and poll and "fabric.microsoft.com" in url:
        op = headers.get("x-ms-operation-id") or headers.get("X-Ms-Operation-Id")
        loc = headers.get("Location")
        for _ in range(240):
            time.sleep(int(headers.get("Retry-After", "3") or 3))
            s, st = call("GET", f"{FABRIC}operations/{op}" if op else loc, poll=False)
            if isinstance(st, dict) and st.get("status") in ("Succeeded", "Failed", "Undefined"):
                if st["status"] == "Succeeded":
                    s2, res = call("GET", f"{FABRIC}operations/{op}/result", poll=False) if op else (200, st)
                    return 200, res if s2 == 200 else st
                return 500, st
        return 504, {"error": "LRO timeout"}
    return status, out
