# ---- SETTINGS: this is the only cell you edit ----

# 1. The connection string of the ORDERS Eventstream (the same one as in part 1).
CONNECTION_STRING = "PASTE-YOUR-CONNECTION-STRING-HERE"

# 2. The connection string of the WEATHER Eventstream (the new one from this part).
#    Where to find it: open the Eventstream, click the source box (the custom endpoint),
#    then in the pane below: Event Hub > SAS Key Authentication > "Connection string-primary key".
WEATHER_CONNECTION_STRING = "PASTE-THE-WEATHER-CONNECTION-STRING-HERE"

ORDERS_PER_MINUTE = 20     # about 20 orders a minute, before the weather adds its own
MUTE_REGION = None         # to stage an outage, write a region: "North America", "Europe", "Asia Pacific" or "Latin America"
RUN_MINUTES = 120          # the store and the weather feed stop by themselves after this many minutes
SEND_WEATHER_HISTORY = True    # the first run sends 28 days of weather history; set this to False after that run
