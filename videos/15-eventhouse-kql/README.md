# Fabric Eventhouse and KQL for Beginners: Step by Step

Video: coming soon on the PBI101 channel.

A beginner's walk through the **Eventhouse**, the database for real-time data in Microsoft Fabric, and **KQL**, the language
you query it with. Everything here is plain KQL that you paste into the queryset of your own database.

## What you need
- A Fabric workspace on a capacity (a trial works), with Contributor rights or more.
- An **Eventhouse** (New item, Eventhouse, any name). It comes with one KQL database of the same name.
- A table of orders named `OrdersLive`. In the video it is filled by an Eventstream; the steps and the store notebook are in
  [`../14-eventstream-basics`](../14-eventstream-basics). Run that notebook for a few minutes and the table exists.

## The steps of the video
1. **Open the Eventhouse.** The *System overview* page shows storage (original and compressed), ingestion and activity.
2. **Open the KQL database** (left tree, under *KQL databases*): the tracker, the table cards, the details pane.
3. **Open the queryset** (`<database>_queryset` in the tree). Paste `queries.kql` into it. Put the cursor inside a query and
   click **Run**: only that query runs.
4. **Run the queries in order.** Query 5 fails on purpose (the time column arrived as text); query 6 fixes it with
   `todatetime`; query 7 saves the fix as a function named `Orders`, and every query after that starts from `Orders`.
5. **Charts.** A query that ends with `render timechart` or `render barchart` is drawn under the editor.
6. **Copilot.** Clear the editor, click **Copilot** in the ribbon, ask in plain English, click **Insert**, then **Run**.
7. **Data policies.** On the database page, in the details pane: *OneLake availability*, and the pencil next to
   *Caching policy* / *Retention policy*.

## Want a month of history?
A table that has only a few minutes of orders makes flat charts. `history_one_day.kql` is one command that adds a day of
made-up orders with a daily rhythm. Set `dayBack` to 1, run it, set it to 2, run it again ... up to 28. One day takes about
two seconds. (A whole month in a single command ran out of memory on a small Eventhouse.)

## Files
| File | What it is |
|---|---|
| `queries.kql` | Every query of the video, numbered, with a comment on each. |
| `history_one_day.kql` | One `.set-or-append` command: a day of orders, same columns as the Eventstream's table. |

## Good to know
- Dates in an Eventhouse are in UTC.
- A line that begins with a dot is a command, not a query: it changes the database.
- Retention is how long data is kept; caching is how much of it stays on fast storage. Both are Unlimited by default.
- An Eventhouse charges your capacity for the time it is up and suspends itself when idle. A stream that never stops keeps
  it up: stop the store notebook when you are done.
- The store is simulated: the products, cities and amounts are made up.

MIT license, like the rest of this repository.
