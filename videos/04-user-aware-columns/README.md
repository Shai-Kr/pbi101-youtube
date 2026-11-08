# Power BI columns that adapt to each user (user-aware calculated columns)

🎬 **Watch the video: https://youtu.be/m5PyxkMSYhI**

Materials for the PBI101 video. A calculated column with **Expression Context = User Context** is calculated at
query time, for whoever is looking: it can use `USERPRINCIPALNAME()`, `USERCULTURE()` and friends, and in Import mode
it isn't stored. Everything here is synthetic demo data: **Aurora Outdoor**, a made-up outdoor gear company.

> **Preview feature.** In Power BI Desktop: File > Options and settings > Options > Preview features >
> **User-context-aware calculated columns**, then restart. The model needs compatibility level 1705.

## What's inside
| Path | What |
|---|---|
| `start/` | The report as the video starts. Open `User_Aware_Columns.pbip` in Power BI Desktop and **Refresh** (the tables read the CSVs from this repo; if Desktop asks how to connect to the web source, pick **Anonymous**). |
| `final/` | The same project after every change in the video. |
| `scripts/1_my_region.dax` | Example 1: "mine", without hiding everyone else (`USERPRINCIPALNAME()`). |
| `scripts/2a_month.dax` | Example 2: month names in the viewer's language (set Expression Context first, then paste). |
| `scripts/2b_weekday_user_context.tmdl` | Example 2: the weekday column in TMDL view (no Group By yet: the slicer gotcha). |
| `scripts/2c_group_by_keys.tmdl` | Example 2: the fix. The whole Date table with `groupByColumn` on the stable keys. |
| `scripts/3_cost_columns_and_role.tmdl` | Example 3: redacted, not broken. Two user-context lookup columns + the `Sales Rep` role. |
| `scripts/4_storage_check.dax` | Bonus: how much data a column stores (DAX query view). |
| `data/` | The CSVs. |
| `build_report.py` | Generates the data and both PBIPs (`--stage start|final`; Python, standard library only). |

## Try it with View as
Modeling > View as > **Other user** and type one of the made-up managers (no role needed):
`luc@aurora.example` (Europe, French), `sofia@aurora.example` (Latin America, Spanish),
`kenji@aurora.example` (Asia Pacific), `maya@aurora.example` (North America; see the preview bug below).
For example 3, View as > **Sales Rep**.

## Related
Object-level security (when a field must disappear completely): https://youtu.be/6vz2SXUkJ68
SQLBI's article that introduced the feature: https://www.sqlbi.com/articles/introducing-user-aware-calculated-columns-in-power-bi/

---

# User-aware calculated columns: what was verified (Step 0)

Tested 2026-11-08 in **Power BI Desktop 2.159.1231.0 (Microsoft Store)** on the video's model
(`User_Aware_Columns`, Aurora Outdoor sample data). Nothing below is from memory: each line was run and checked.

## 1. Availability
- **Preview switch needed for the UI.** File → Options and settings → Options → Preview features →
  **"User-context-aware calculated columns"**, then restart Desktop. Without it the column Properties have no
  Expression Context dropdown (the engine still loads such columns from TMDL).
- **Compatibility level 1705.** A PBIP at 1600 fails to open: *"The database compatibility level of 1600 is below the
  minimal compatibility level of 1705 needed for ... [ExpressionContext]"*.
- In TMDL the property is `expressionContext: userContext` on the column. A generated PBIP with it opens and refreshes.
- Where it lives in the UI: **Model view → select the column → Properties → Advanced → Expression Context**
  (Standard / User Context), with the hint "Use for dynamic evaluation of DAX functions with user context".
  User-context columns get their own icon in the field list.
- With Expression Context = Standard, a formula with `USERPRINCIPALNAME()` fails:
  *"CUSTOMDATA, USERNAME, USERCULTURE and USERPRINCIPALNAME functions are not supported in calculated
  tables/columns. These functions may only be used in Measures or in the AllowedRowsExpression."*
  The property stays on User Context when that error is closed.

## 2. Per-user values in Desktop
- **Modeling → View as → Other user** with a made-up UPN (e.g. `luc@aurora.example`) drives `USERPRINCIPALNAME()`
  inside a user-context column. **No role needs to be checked.**
- `My Region = IF ( Regions[Manager UPN] = USERPRINCIPALNAME (), "★ My region", "Other regions" )` as legend,
  slicer and table column: Luc → Europe highlighted, Sofia → Latin America, Kenji → Asia Pacific. Correct.
- **Preview bug found:** viewing as **Maya** (North America = the first row of the Regions table), every region
  showed as "★ My region" in visuals that use Sales. Reproduced without any user function:
  `IF ( Regions[Region ID] = 1, "A", "B" )` (user context) puts every region's sales under "A";
  `IF ( Regions[Region ID] = 2, "A", "B" )` is correct; three-value columns were correct.
  The same column on a copy of Regions with a neutral first row ("Head office") was correct for every manager.
  The video uses Luc, Sofia and Kenji, and the gotchas section says: test every user, it's a preview.
- A **measure** that filters on a user-context column (`CALCULATE ( [Revenue], Regions[My Region] = "★ My region" )`)
  failed with `QuerySystemError`. The model's measures filter `Manager UPN` directly instead.

## 3. USERCULTURE()
- `USERCULTURE()` follows the client's locale. Over a connection with Locale Identifier 1036 it returns `fr-FR`, and
  `FORMAT ( ..., "mmmm", USERCULTURE() )` returns *janvier*; 1031 → *Januar*; es-MX → *enero*.
  `ja-JP` came back in English from `FORMAT`, so the Asia Pacific manager uses `en-AU`.
- **View as cannot fake a culture.** The two real options (Desktop's application language + restart, or the
  service with the viewer's browser language) were not used: the first changes the whole Desktop UI, the second
  needs Fabric. Instead the video reads a preferred culture from the manager's row and falls back to
  `USERCULTURE()`:
  `COALESCE ( LOOKUPVALUE ( Regions[Culture], Regions[Manager UPN], USERPRINCIPALNAME () ), USERCULTURE () )`.
  View as Luc → French month and weekday names, Sofia → Spanish, Kenji → English.

## 4. Where it can be used
| Use | Result |
|---|---|
| Legend / series color (stacked bar, stacked column) | works |
| Axis, table column | works |
| Button slicer | works |
| Sort by column (`sortByColumn: 'Month Number'`) | works |
| Group by columns (`relatedColumnDetails` → `groupByColumn`) | works, **but only in a full-table TMDL script** (`createOrReplace` + `table Date` with every column). In a `ref table` script Apply fails: *"For deserialization of property 'groupByColumns' we must know the owning table!"* |
| Measure filtering the column | `QuerySystemError` (see 2) |
| Relationships, RLS expressions, standard calculated columns, calculated tables | not allowed (SQLBI) |
- After applying a TMDL script that recreates a user-context column, Desktop shows "One or more calculated columns
  need to be manually refreshed": click Refresh now.

## 5. The slicer gotcha (translated labels)
- Weekday as a user-context column **without** Group By: select *Sunday* in a button slicer, then View as Luc →
  the tiles read *lundi … dimanche*, none is selected, and every visual on the page goes blank. The selection was
  stored as the text "Sunday".
- With `groupByColumn: 'Day of Week Number'`: select Sunday again, View as Luc → *dimanche* stays selected and the
  visuals keep the Sunday numbers.

## 6. Security pattern (redacted, not broken)
- `'Product Cost'` is hidden and **disconnected** (no relationship). Role `Sales Rep`: `tablePermission 'Product Cost' = FALSE()`.
- `Supplier` / `Margin Band` on Products = `LOOKUPVALUE ( 'Product Cost'[...], 'Product Cost'[Product ID], Products[Product ID] )`.
- As **standard** columns, View as Sales Rep still shows every supplier and margin band (the card says the cost table
  is blocked): a standard column was computed at refresh, outside any role. That is a leak.
- Switched to **User Context**: View as Sales Rep → both columns blank, charts show (Blank), revenue intact,
  no visual errors.
- The column names stay visible: it hides values, not the field. To remove a field entirely, use OLS.

## 7. Storage
In DAX query view, `INFO.STORAGETABLECOLUMNSEGMENTS()` + `INFO.STORAGETABLECOLUMNS()` on 9,125 sales rows:
| Column | Data | Hierarchy | Dictionary |
|---|---|---|---|
| Sales Amount (imported, stored) | 36,632 B | 5,032 B | 144 B |
| Line Amount (user context, same numbers) | 136 B | none | 296 B |
So the user-context column is an empty shell (~0.4 KB), computed at query time.


Channel: https://www.youtube.com/@pbi101  |  https://pbi101.com
