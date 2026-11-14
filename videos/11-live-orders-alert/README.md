# Real-Time Orders in Fabric: Teams Alert + AI Agent

Video: [Real-Time Orders in Fabric: Teams Alert + AI Agent](https://youtu.be/X25d1Z-HTrw)
Part 2: [Real Weather in Fabric: Rain Alert + AI Agent in Teams](https://youtu.be/1_e6TUSKjxs) (materials in `../12-weather-joins-orders`)
**The full build guide, step by step, with screenshots:** https://shai-kr.github.io/data-ninja-ai-lab/blog/2026-11-13-fabric-real-time-alert-agent-guide.html

Orders reach Microsoft Fabric the moment they happen, a rule keeps watching, and when a whole region stops ordering, an AI
agent in Teams says whether it is real. The store is simulated; the stream, the alert and the answers are real.

```
store / phone page --> Eventstream --> Eventhouse (KQL table OrdersLive) --> Real-Time Dashboard
                                              |
                               Activator rule (orders per region, last 5 minutes)
                                              |
                       Power Automate flow --> a Teams chat with a Copilot Studio agent
                                              |
                              tool: a Fabric data agent that queries OrdersLive
```

## What is in this folder

| File | What it does |
|---|---|
| `setup_fabric.py` | Creates the workspace folder, the Eventhouse + KQL table `OrdersLive`, and the Eventstream (custom endpoint to Eventhouse). `endpoint` saves the endpoint's connection to a local file; `kql "<query>"` runs a query |
| `live_orders.py` | The simulated store. `send N`, `one "<Product>" <City>`, `run RATE` (a steady flow, with `--mute-region` to stage an outage), `backfill DAYS` (history generated inside the Eventhouse) |
| `aurora_dims.json` | The store's products and regions |
| `phone/index.html` + `phone_server.py` | A phone-shaped store page. A tap on Buy sends one real event through a small local relay, and shows how long it took to be queryable |
| `setup_dashboard.py` | The Real-Time Dashboard as code: live orders, orders per minute by region, the taps from the phone, and (part 2) a weather page with a map |
| `setup_activator.py` | The Activator item: a KQL source every 60 s, the object Region, and the rule "Region stopped ordering" (orders in the last 5 minutes becomes less than 1) |

They need `../../studio/fabric_api.py` (a small REST helper) and a config file with your own ids: see
`../../studio/fabric_env.example.json`. Python 3.10+, standard library only, plus the Azure CLI (`az login`).

## Order of work (the blog article has every step with screenshots)

1. `python setup_fabric.py items` then `python setup_fabric.py endpoint`.
2. `python live_orders.py backfill 28` for history, then `python live_orders.py run 20` to keep orders coming.
3. `python setup_dashboard.py`, and open the dashboard with Live refresh on.
4. `python phone_server.py`, open http://127.0.0.1:8711/ and tap Buy.
5. In Fabric: a data agent with the table `OrdersLive` ticked; publish it.
6. `python setup_activator.py deploy` for the rule.
7. In Copilot Studio: an agent with one tool (Fabric IQ Data MCP, pointing at the data agent), channel Teams, publish.
   Its instructions:
   > You are Aurora Watch, the operations assistant for Aurora Outdoor's online store (a simulated demo store). Answer questions about live orders by calling the Aurora Live Agent tool. Never guess a number: every number in your answer must come from the tool. All times in the data are UTC. Keep answers short: the answer first, then the numbers it is based on. When the user asks about an alert, check the most recent data for that region and compare it with the same hour on earlier days.
8. In the Activator rule: Action, Create custom action, and build the two-step flow (when the rule fires, post a message in
   the chat with the agent). The article explains why the flow posts in your name.
9. Stage an outage: stop the store and start `python live_orders.py run 20 --mute-region "North America"`.

## Good to know

- The endpoint's keys are written to `~/.pbi101/eventstream_orders.json` on your machine. Never commit that file.
- Stop the rules before you stop the store, or every region "stops ordering" at once and the rule fires for all of them.
- Costs: a Fabric capacity while it is on, plus Copilot Studio pay as you go (about 1 cent per credit when recorded).
