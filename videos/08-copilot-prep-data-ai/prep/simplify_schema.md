# Simplify the data schema (Prep data for AI, tab 1)

Power BI service > the semantic model > Editing > **Prep data for AI** > **Simplify the data schema**.

| Field | AI schema | Why |
|---|---|---|
| Hidden fields (Order ID, Product ID, Region ID, Quantity, Unit Cost, Sales Amount, Cost Amount) | off (default) | Hidden fields are left out automatically the first time. |
| Sales[Order Date] | **unticked** | Dates should go through the Date table (the relationship), not the raw order date. |
| Sales[Unit Price] | **unticked** | A raw price per order line: averaging it is not the average selling price. |
| Everything else (the 9 measures, Products, Regions, the Date table) | on | |

Notes (Microsoft Learn): the schema applies to Copilot's data questions. Report summaries, page creation and DAX
query features still use the whole model. Consumers can't see it or turn it off.
