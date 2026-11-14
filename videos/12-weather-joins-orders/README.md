# Real Weather in Fabric: Rain Alert + AI Agent in Teams

Video: [Real Weather in Fabric: Rain Alert + AI Agent in Teams](https://youtu.be/1_e6TUSKjxs)
Part 1: [Real-Time Orders in Fabric: Teams Alert + AI Agent](https://youtu.be/X25d1Z-HTrw) (materials in `../11-live-orders-alert`; build that first)
**The full build guide for both parts, step by step, with screenshots:** https://shai-kr.github.io/data-ninja-ai-lab/blog/2026-11-13-fabric-real-time-alert-agent-guide.html

Real weather for the store's 17 cities flows into the same Eventhouse as the orders. A rule fires when rain starts in a
city, and the agent in Teams says what rain usually does to sales there. The weather is real; the shoppers are simulated
and built to react to weather, so the pattern the agent finds is planted. The plumbing is the point.

Weather data by [Open-Meteo.com](https://open-meteo.com) (CC BY 4.0; free for non-commercial use, no key).

## What is in this folder

| File | What it does |
|---|---|
| `weather.py` | `setup` (table `WeatherLive` + a second Eventstream), `endpoint`, `now`, `send`, `run` (the feed: fetch every 5 minutes, send what changed), `forecast` (when rain is expected to start), `history 28` (real hourly history), `extras 28` (weather-driven orders for the history) |
| `store_sim.py` | The store from part 1, with shoppers who react to the real weather in their city (rain: rain jackets x 3) |
| `setup_agent.py` | Adds `WeatherLive` and instructions to the Fabric data agent by REST (draft and published) |
| `setup_weather_rule.py` | Adds the second Activator rule, "Rain started in a city", next to the first one; `stop` / `start` |
| `setup_flow.py` | Makes the Power Automate flow write a rain sentence for a city and the outage sentence for a region (Dataverse Web API) |

## Order of work

1. `python weather.py setup`, `python weather.py endpoint`, `python weather.py history 28`, `python weather.py extras 28`.
2. `python weather.py run` (the feed) and `python store_sim.py run 20` (instead of part 1's `live_orders.py run`).
3. `python setup_agent.py apply`. Wait about ten minutes before testing: the agent's query generator picks the change up late.
4. In Copilot Studio, add this to the agent's instructions and publish again (it does not learn about the tool's new data
   by itself):
   > The Aurora Live Agent tool also has real weather readings for the store's 17 cities (temperature and rain, right now and for the last 28 days). For any question about weather, rain or temperature, call the tool; never say you have no weather data. When an alert says rain started in a city, use the tool to report what rain usually does to orders in that city (orders per hour in rainy hours against dry hours, by product), what the last hour shows, and what to expect in the next hour.
5. `python setup_flow.py apply`, then `python setup_weather_rule.py apply`.
6. `python ../11-live-orders-alert/setup_dashboard.py` adds the Weather page (map, readings, rain jacket share).
7. `python weather.py forecast` tells you when a real rain start is expected. Then wait.

## Good to know

- `python setup_weather_rule.py stop` when you are not testing: every real rain start posts in your Teams chat and uses credits.
- The agent compares orders per hour in rainy and dry hours. Its dry-hour averages ran a little high in the video (it
  dropped the hours with no order at all): check numbers that matter.
