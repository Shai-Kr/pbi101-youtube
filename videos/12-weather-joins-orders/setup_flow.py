"""Video 12: make the Power Automate flow "Aurora Watch alert" write one of two messages (by the Dataverse Web API).

  python -I setup_flow.py show      the flow's state and its Teams message (the chat key is masked)
  python -I setup_flow.py apply     outage message for a region, rain message for a city
  python -I setup_flow.py restore   put back the definition saved before the first apply

The flow has two steps (video 11): "When an activator rule is triggered" -> "Post message in a chat or channel"
(as User, into the chat with the agent). Its trigger gives the key of the object that fired: a region name for the
orders rule, a city name for the new weather rule. Both rules use the same custom action ("Tell Aurora Watch"), so
the flow picks the sentence from that key. Nothing else in the flow changes.
Auth: az CLI token for the demo environment's Dataverse address (kept in fabric_env.json
under realtime.dataverse_url; a backup of the flow sits outside the repo).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENV_FILE = Path.home() / ".pbi101" / "fabric_env.json"
WORK = Path(__file__).resolve().parent / "work"
BACKUP = WORK / "flow_before.json"
NAME = "Aurora Watch alert"
KEY = "triggerOutputs()?['body/objectInstanceId']"
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]
OUTAGE = ("concat('orders stopped in ', {k}, '. Check this region''s orders in the last 15 minutes against the same hour on "
          "earlier days, and tell me what you see.')")
RAIN = ("concat('rain started in ', {k}, '. Check what rain usually does to our orders in that city, and tell me what to "
        "expect in the next hour.')")


def org() -> str:
    e = json.loads(ENV_FILE.read_text(encoding="utf-8"))
    return e["realtime"]["dataverse_url"].rstrip("/")


def token() -> str:
    import os
    env = dict(os.environ)
    r = subprocess.run(["az", "account", "get-access-token", "--resource", org(), "--query", "accessToken", "-o", "tsv"],
                       capture_output=True, text=True, env=env, shell=True)
    if r.returncode:
        sys.exit("az token failed: " + r.stderr[:300])
    return r.stdout.strip()


def call(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(org() + "/api/data/v9.2/" + path, method=method,
                                 data=json.dumps(body).encode("utf-8") if body is not None else None)
    req.add_header("Authorization", "Bearer " + token())
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read().decode("utf-8")
            return r.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", "replace")[:600]}


def flow() -> dict:
    s, b = call("GET", "workflows?$filter=name%20eq%20'" + NAME.replace(" ", "%20") + "'&$select=name,workflowid,statecode,statuscode,clientdata")
    if s >= 300 or not b.get("value"):
        sys.exit(f"flow not found: {s} {b}")
    return b["value"][0]


def message(f: dict) -> str:
    cd = json.loads(f["clientdata"])
    return cd["properties"]["definition"]["actions"]["Post_message_in_a_chat_or_channel"]["inputs"]["parameters"]["body/messageBody"]


def show():
    f = flow()
    print(f["name"], "| statecode", f["statecode"], "| statuscode", f["statuscode"])
    print(re.sub(r"19:[^\"<@]+@unq\.gbl\.spaces", "<chat key>", message(f)))


def apply():
    f = flow()
    if not BACKUP.exists():
        WORK.mkdir(parents=True, exist_ok=True)
        BACKUP.write_text(json.dumps(f), encoding="utf-8")
    cd = json.loads(f["clientdata"])
    regions = ", ".join("'" + r + "'" for r in REGIONS)
    expr = (f"if(contains(createArray({regions}), {KEY}), " + OUTAGE.format(k=KEY) + ", " + RAIN.format(k=KEY) + ")")
    body = '<p class="editor-paragraph">Alert from Fabric: @{' + expr + "}</p>"
    cd["properties"]["definition"]["actions"]["Post_message_in_a_chat_or_channel"]["inputs"]["parameters"]["body/messageBody"] = body
    s, b = call("PATCH", f"workflows({f['workflowid']})", {"clientdata": json.dumps(cd)})
    print("PATCH", s, b.get("error", ""))
    show()


def restore():
    f = json.loads(BACKUP.read_text(encoding="utf-8"))
    s, b = call("PATCH", f"workflows({f['workflowid']})", {"clientdata": f["clientdata"]})
    print("PATCH", s, b.get("error", ""))
    show()


if __name__ == "__main__":
    {"show": show, "apply": apply, "restore": restore}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
