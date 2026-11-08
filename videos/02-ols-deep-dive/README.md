# Object-Level Security (OLS) in Power BI: setup + 3 ways to fix the broken visuals

Materials for the PBI101 video. Everything here is synthetic demo data (Aurora Outdoor, a made-up outdoor-gear shop).

## What's inside
| Folder | What |
|---|---|
| `pbip/` | The Power BI project (PBIP: PBIR report + TMDL model). Open `OLS_Deep_Dive.pbip` in Power BI Desktop, then **Refresh**. The tables read the CSVs from this repo on GitHub, so no local files are needed (if Power BI asks how to connect to the web source, pick **Anonymous**). |
| `scripts/` | The three TMDL scripts from the video. Paste them into **TMDL view** and click **Apply**, in order. |
| `dax/` | The DAX behind fix 2 (field parameter) and fix 3 (role detector). |
| `data/` | The CSVs (9,125 order lines, Jan 2025 - Oct 2026). |
| `build_report.py` | The Python script that generates the data and the whole PBIP (standard library only). |

## The demo in 4 steps
1. **OLS role**: `scripts/1_ols_role.tmdl` creates the role **Sales Team** with `columnPermission ... = none` on `Unit Cost` and `Cost Amount`.
   Test it: Modeling > View as > Sales Team. Cost, gross margin and margin % disappear, and every visual that used them breaks.
2. **Fix 1: a separate report per audience.** Simple and often the right call (in a Power BI app, give each audience its own report).
3. **Fix 2: field parameters + RLS.** `Metric Picker` is a field parameter with an extra `Is Sensitive` column.
   `scripts/2_add_field_parameter_rls.tmdl` adds `tablePermission 'Metric Picker' = 'Metric Picker'[Is Sensitive] = FALSE()`,
   so the Sales Team never even gets the sensitive metrics to pick. (TMDL view underlines `[Is Sensitive]` in red: an editor quirk with calculated-table columns. It applies fine.)
4. **Fix 3: role detector.** `Security Marker` is a one-row table. `scripts/3_add_role_detector_rls.tmdl` adds `tablePermission 'Security Marker' = FALSE()`.
   `[Full Access] = NOT ISEMPTY('Security Marker')` never touches a secured column, so it never breaks. It drives the banner, the button text, its color and the button's page navigation to the hidden **Margin Details** page.

## Good to know
- OLS only applies to **Viewers** in the Power BI service. Admins, Members and Contributors see everything.
- RLS and OLS for the same people must live in the **same role**.
- Any measure built on a secured column disappears with it.
- Hide a whole table: `tablePermission <Table>` with `metadataPermission: none`.

🎬 **Watch the video: https://youtu.be/6vz2SXUkJ68**  |  Channel: https://www.youtube.com/@pbi101  |  https://pbi101.com
