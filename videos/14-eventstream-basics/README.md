# Microsoft Fabric Eventstream for Beginners: Step by Step

Video: coming soon on the PBI101 channel.

A beginner's walk through **Eventstream**, the front door for real-time data in Microsoft Fabric. Everything is built by
clicking; the only code is a small notebook that plays an online store and sends the orders.

## What you need
- A Fabric workspace on a capacity (a trial works), with Contributor rights or more.
- An **Eventhouse** in that workspace (New item, Eventhouse, any name). It can be empty.

## The steps of the video
1. **Create the Eventstream.** New item, Eventstream, name it `AuroraOrders`. Leave the schema checkbox empty.
2. **Add a source.** On the first screen click **Use custom endpoint**, name it `StoreOrders`, click **Add**, then **Publish**.
3. **Send orders.** Import `Aurora_Store.ipynb` into the same workspace (Import, Notebook, From this computer), open it and
   click **Run all**. If your Eventstream has another name, change `EVENTSTREAM_NAME` in the first cell.
   The notebook asks Fabric for the endpoint's address and key by itself: nothing to paste.
4. **Watch them arrive.** In the Eventstream click the stream box in the middle, then **Refresh** in *Data preview*.
5. **Add a destination.** **Edit**, click the **+** after the stream, **Add destination**, **Eventhouse**. Keep
   *Event processing before ingestion*, name it `AllOrders`, pick your Eventhouse and database, **Create new** table
   (`OrdersLive`), **Save**, **Publish**.
6. **Add a filter.** **Edit**, **Transform events**, **Filter**. Drag a line from the stream to the filter. Name it `BigOrders`,
   field `SalesAmount`, *greater than or equal*, `500`, **Save**. Select the filter and click **Refresh** under *Test result*.
7. **A second destination.** The **+** after the filter, **Add destination**, **Eventhouse**, a new table `BigOrders`,
   **Save**, **Publish**.

## Files
| File | What it is |
|---|---|
| `Aurora_Store.ipynb` | The store: a Fabric Python notebook, two cells. Sends about 20 orders a minute for two hours (both are settings). |
| `store_cell1_settings.py`, `store_cell2_run.py` | The same two cells as plain text, if you prefer to paste them into a new notebook. |

## Good to know
- Edit mode is a draft. Nothing is real until you click **Publish**.
- The connection string of a custom endpoint is a password. Do not put it in a chat or a screenshot.
- A table created from the Eventstream gets the event's columns; `OrderTime` arrives as text. Change the type with a
  **Manage fields** operator, or later in the database.
- An Eventstream uses your capacity while events flow. Stop the notebook (**Interrupt kernel**) and use **Deactivate all**
  when you are done.
- The store is simulated: the products, cities and amounts are made up by the notebook.

MIT license, like the rest of this repository.
