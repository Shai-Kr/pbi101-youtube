# ---- HELPERS + (on the first run only) 28 days of REAL hourly weather for the 17 cities ----
# Weather data by Open-Meteo.com (CC BY 4.0, free for non-commercial use, no key).
import base64, hashlib, hmac, json, time, urllib.parse, urllib.request
from datetime import datetime, timezone

CITIES = {  # city: (latitude, longitude, region)
    "Vancouver": (49.28, -123.12, "North America"), "Seattle": (47.61, -122.33, "North America"),
    "Denver": (39.74, -104.99, "North America"), "Toronto": (43.65, -79.38, "North America"),
    "New York": (40.71, -74.01, "North America"), "London": (51.51, -0.13, "Europe"),
    "Berlin": (52.52, 13.41, "Europe"), "Oslo": (59.91, 10.75, "Europe"), "Madrid": (40.42, -3.70, "Europe"),
    "Zurich": (47.38, 8.54, "Europe"), "Tokyo": (35.68, 139.69, "Asia Pacific"),
    "Sydney": (-33.87, 151.21, "Asia Pacific"), "Auckland": (-36.85, 174.76, "Asia Pacific"),
    "Singapore": (1.35, 103.82, "Asia Pacific"), "Santiago": (-33.45, -70.67, "Latin America"),
    "Bogota": (4.71, -74.07, "Latin America"), "Sao Paulo": (-23.55, -46.63, "Latin America")}
CONDITIONS = {0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog", 51: "Light drizzle",
              53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow",
              73: "Snow", 75: "Heavy snow", 80: "Light showers", 81: "Showers", 82: "Heavy showers", 95: "Thunderstorm"}


def endpoint(connection_string, name):
    conn = dict(part.split("=", 1) for part in connection_string.strip().split(";") if "=" in part)
    if "Endpoint" not in conn or "EntityPath" not in conn:
        raise ValueError(f"Paste the connection string into {name} (the first cell), then run the cells again.")
    conn["url"] = "https://" + conn["Endpoint"].replace("sb://", "").strip("/") + "/" + conn["EntityPath"]
    return conn


def send(conn, events):
    uri = urllib.parse.quote_plus(conn["url"])
    expiry = str(int(time.time()) + 3600)
    signature = base64.b64encode(hmac.new(conn["SharedAccessKey"].encode(), f"{uri}\n{expiry}".encode(), hashlib.sha256).digest()).decode()
    token = f"SharedAccessSignature sr={uri}&sig={urllib.parse.quote_plus(signature)}&se={expiry}&skn={conn['SharedAccessKeyName']}"
    body = json.dumps([{"Body": json.dumps(e)} for e in events]).encode("utf-8")
    request = urllib.request.Request(conn["url"] + "/messages?timeout=60&api-version=2014-01", data=body, method="POST")
    request.add_header("Authorization", token)
    request.add_header("Content-Type", "application/vnd.microsoft.servicebus.json")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status


def weather_service(parameters):
    latitudes = ",".join(str(c[0]) for c in CITIES.values())
    longitudes = ",".join(str(c[1]) for c in CITIES.values())
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitudes}&longitude={longitudes}&timezone=UTC&{parameters}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fabric-demo"}), timeout=60) as response:
        return json.loads(response.read())


def reading(city, time_text, temp, precipitation, snow, wind, code, minutes):
    latitude, longitude, region = CITIES[city]
    precipitation = precipitation or 0.0
    return {"ReadingTime": time_text + ":00Z", "City": city, "Region": region, "Latitude": latitude, "Longitude": longitude,
            "TempC": temp, "PrecipMm": precipitation, "RainRate": round(precipitation * 60 / minutes, 2),   # millimetres per hour
            "SnowCm": snow or 0.0, "WindKmh": wind, "WeatherCode": code, "Condition": CONDITIONS.get(code, str(code)),
            "IntervalMin": minutes, "Source": "open-meteo.com"}


weather = endpoint(WEATHER_CONNECTION_STRING, "WEATHER_CONNECTION_STRING")
if SEND_WEATHER_HISTORY:
    data = weather_service("hourly=temperature_2m,precipitation,snowfall,weather_code,wind_speed_10m&past_days=28&forecast_days=1")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    history = []
    for city, place in zip(CITIES, data):
        h = place["hourly"]
        for i, t in enumerate(h["time"]):
            if t <= now and h["temperature_2m"][i] is not None:
                history.append(reading(city, t, h["temperature_2m"][i], h["precipitation"][i], h["snowfall"][i],
                                       h["wind_speed_10m"][i], h["weather_code"][i], 60))
    for start in range(0, len(history), 300):
        send(weather, history[start:start + 300])
    rainy = sum(1 for r in history if r["RainRate"] >= 0.4)
    print(f"Sent {len(history)} hourly readings. {rainy} of them are rainy hours.")
    print("Now set SEND_WEATHER_HISTORY = False in the first cell, so the next run does not send the history again.")
else:
    print("Weather history: skipped (SEND_WEATHER_HISTORY is False).")
