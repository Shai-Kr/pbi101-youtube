# Fabric Real-Time Dashboard for Beginners: Step by Step

Video: https://youtu.be/SFLM0AAo1ks

A beginner's walk through the **Real-Time Dashboard** in Microsoft Fabric: a dashboard that looks straight into an
Eventhouse and refreshes by itself. Everything is built by clicking; the only code is a few short KQL queries, one per tile.

## What you need
- A Fabric workspace on a capacity (a trial works), with Contributor rights or more.
- An **Eventhouse** with a table of orders named `OrdersLive`, and orders arriving. The steps for that are in
  [`../14-eventstream-basics`](../14-eventstream-basics) (the store notebook and the Eventstream).
- The function `Orders` (the table with the time as a real date). It is created in
  [`../15-eventhouse-kql`](../15-eventhouse-kql), and the same command is at the top of `tiles.kql`.

## The steps of the video
1. **Create the dashboard.** In the workspace: **New item**, type `real-time dashboard`, click the card, name it, **Create**.
2. **Add a data source.** A small window offers the workspace's Eventhouse: **Continue**. (Or pick it under *Suggested from
   the Workspace*.)
3. **The first tile.** In *Add visual* click **More**, then **Time chart**. Paste the first query of `tiles.kql` into the
   Query editor and click **Run**. Open **Visual setup**, **General**, type a tile name, then **Apply**.
4. **A KPI.** **Add visual**, **KPI**, paste the second query, **Run**. It opens as a gauge in percent: in **Visual setup**
   choose **Number**, in **Value format** change the unit label to `orders`, and switch **Conditional formatting** off.
5. **A bar chart.** **Add visual**, **Bar chart**, the third query. It uses `_startTime` and `_endTime`, the two ends of the
   dashboard's built-in *Time range*, so this tile follows that filter.
6. **A table.** **Add visual**, **Table**, the fourth query.
7. **Layout.** Drag a tile by its title; resize it from its bottom-right corner. A tile's **...** menu has Rename, Duplicate
   and View query.
8. **A filter.** **Add parameter**: Label `Region`, Variable name `_region`, Source **Query** (`Orders | distinct Region`),
   Value column `Region`, tick *Add "Select all" value*, Default value *Select all*, **Done**. Then edit the first tile and
   add the line `| where isempty(_region) or Region == _region`.
9. **Refresh.** **Manage**, **Refresh settings**: keep *Live refresh*, open **Settings**, set the *Refresh rate limit*
   (the video uses 10 seconds), **Apply**. Save the dashboard and confirm.
10. **Viewing.** Switch **Editing** to **Viewing** and watch it update.

## Files
| File | What it is |
|---|---|
| `tiles.kql` | The query of each tile, the query behind the Region filter, and the first tile again with the filter line. |

## Good to know
- A tile is one query plus one visual. Keep the query small: the last hour, grouped, not a million raw rows.
- Each refresh runs every tile's query again, and that uses capacity. Choose the refresh rate on purpose.
- Sharing a dashboard does not share the data: by default each viewer also needs permission on the database.
- The times on the tiles are in UTC.
- Alerts can be set only on tiles that use a predefined time range.
- The store is simulated: the products, cities and amounts are made up.

MIT license, like the rest of this repository.
