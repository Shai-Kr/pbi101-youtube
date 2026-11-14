# ---- SETTINGS: this is the only cell you edit ----

# Paste the connection string of your Eventstream between the quotes.
# Where to find it: open the Eventstream, click the source box (the custom endpoint),
# then in the pane below: Event Hub > SAS Key Authentication > "Connection string-primary key".
CONNECTION_STRING = "PASTE-YOUR-CONNECTION-STRING-HERE"

ORDERS_PER_MINUTE = 20     # about 20 orders a minute
MUTE_REGION = None         # to stage an outage, write a region: "North America", "Europe", "Asia Pacific" or "Latin America"
RUN_MINUTES = 120          # the store stops by itself after this many minutes
