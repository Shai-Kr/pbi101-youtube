"""Build the demo dataset (CSV) and the Power BI project (PBIP, PBIR + TMDL) for video 04
(user-aware calculated columns: column property Expression Context = User Context).

Aurora Outdoor, the same synthetic sales as videos 01-02 (same seed), plus:
  - Regions carries each region's manager: a fake UPN on the reserved domain aurora.example, a culture and a
    monthly target;
  - Date gets stable keys (Month Number, Day of Week Number, Monday = 1) and Month / Weekday columns;
  - 'Product Cost' is a hidden, DISCONNECTED lookup (supplier, unit cost, margin band) that the role
    'Sales Rep' blocks with FALSE();
  - three report pages in a new look (warm paper background, navy header band, amber "mine" accent).

Stages (--stage):
  start  the state at the start of the recording: My Region + Line Amount are user-context columns already;
         Month / Weekday are plain (standard) columns; Supplier / Margin Band are STANDARD LOOKUPVALUE
         columns (so they leak past RLS until they are switched to User Context on camera).
  final  every change made in the video: Month/Day names in the viewer's language (Weekday grouped by its key),
         Supplier / Margin Band as user-context columns. Used for the hook shots and the published materials.

Output: next to this script (data/, pbip/)
Run: C:\\Python315\\python.exe -I build_report.py [--stage start|final] [--out <folder>] [--data-url <base url>]
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import random
import shutil
import sys
import uuid
from pathlib import Path

WORK = Path(__file__).resolve().parent
DATA = WORK / "data"
PBIP = WORK / "pbip"
NAME = "User_Aware_Columns"
HERE = Path(__file__).resolve().parent
BASE_THEME = HERE / "theme" / "CY26SU05.json"
DATA_URL = None   # --data-url: the published materials read the CSVs from GitHub instead of a local folder
STAGE = "start"   # --stage

# ---------------------------------------------------------------- data (same generator + seed as video 02)
PRODUCTS = [  # id, name, category, price, cost
    (1, "Summit 2P Tent", "Camping", 349, 215), (2, "Basecamp 6P Tent", "Camping", 699, 452),
    (3, "Arctic Sleeping Bag", "Camping", 229, 131), (4, "Trailhead 45L Pack", "Hiking", 189, 98),
    (5, "Ridge Trekking Poles", "Hiking", 89, 41), (6, "Alpine Hiking Boots", "Hiking", 219, 124),
    (7, "Storm Shell Jacket", "Apparel", 259, 101), (8, "Thermal Base Layer", "Apparel", 79, 29),
    (9, "Summit Fleece", "Apparel", 129, 52), (10, "Glacier Water Bottle", "Accessories", 35, 13),
    (11, "Headlamp Pro", "Accessories", 59, 24), (12, "Trail First-Aid Kit", "Accessories", 45, 19),
]
PRODUCT_WEIGHT = [1.0, 0.5, 0.8, 1.2, 0.9, 1.1, 1.0, 1.4, 1.1, 1.6, 1.2, 0.9]
REGIONS = [(1, "North America", 0.42), (2, "Europe", 0.30), (3, "Asia Pacific", 0.18), (4, "Latin America", 0.10)]
SEASON = {1: .70, 2: .72, 3: .86, 4: 1.0, 5: 1.18, 6: 1.34, 7: 1.40, 8: 1.24, 9: 1.0, 10: .95, 11: 1.12, 12: 1.30}
START, END = dt.date(2025, 1, 1), dt.date(2026, 10, 31)

# the regional managers (fictional people, reserved domain .example)
MANAGERS = {1: ("Maya Brooks", "maya@aurora.example", "en-US"),
            2: ("Luc Moreau", "luc@aurora.example", "fr-FR"),
            3: ("Kenji Sato", "kenji@aurora.example", "en-AU"),
            4: ("Sofia Reyes", "sofia@aurora.example", "es-MX")}
SUPPLIERS = {1: "Ridgeway Mills", 2: "Ridgeway Mills", 3: "Bluepine Supply", 4: "Kestrel Works",
             5: "Kestrel Works", 6: "Kestrel Works", 7: "Tundra Textiles", 8: "Tundra Textiles",
             9: "Tundra Textiles", 10: "Bluepine Supply", 11: "Bluepine Supply", 12: "Bluepine Supply"}


def poisson(rng: random.Random, lam: float) -> int:
    import math
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def margin_band(price: float, cost: float) -> str:
    m = 1 - cost / price
    return "High margin" if m >= 0.55 else ("Mid margin" if m >= 0.45 else "Low margin")


def build_data() -> dict:
    rng = random.Random(20261106)
    DATA.mkdir(parents=True, exist_ok=True)
    rows, oid, day = [], 100000, START
    while day <= END:
        growth = 1.0 if day.year == 2025 else 1.19
        weekday = 0.75 if day.weekday() >= 5 else 1.0
        for _ in range(poisson(rng, 12.5 * SEASON[day.month] * growth * weekday)):
            oid += 1
            p = rng.choices(PRODUCTS, weights=PRODUCT_WEIGHT)[0]
            r = rng.choices(REGIONS, weights=[x[2] for x in REGIONS])[0]
            qty = max(1, int(rng.gauss(14, 7)))
            price = round(p[3] * (1 - rng.choice([0, 0, 0, .05, .10, .15])), 2)
            cost = round(p[4] * rng.uniform(.97, 1.03), 2)
            rows.append([oid, day.isoformat(), p[0], r[0], qty, price, cost,
                         round(qty * price, 2), round(qty * cost, 2)])
        day += dt.timedelta(days=1)

    def write(name, header, data):
        with open(DATA / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(data)

    write("sales.csv", ["Order ID", "Order Date", "Product ID", "Region ID", "Quantity",
                        "Unit Price", "Unit Cost", "Sales Amount", "Cost Amount"], rows)
    write("products.csv", ["Product ID", "Product", "Category"], [p[:3] for p in PRODUCTS])
    write("product_cost.csv", ["Product ID", "Supplier", "Unit Cost", "Margin Band"],
          [(p[0], SUPPLIERS[p[0]], p[4], margin_band(p[3], p[4])) for p in PRODUCTS])
    # monthly target = the region's average 2026 month, +6%, rounded to 5K
    months26 = {d for _, d, *_ in rows if d.startswith("2026")}
    n26 = len({d[:7] for d in months26})
    regions = []
    for rid, name, _ in REGIONS:
        rev26 = sum(r[7] for r in rows if r[3] == rid and r[1].startswith("2026"))
        target = int(round(rev26 / n26 * 1.06 / 5000) * 5000)
        mgr, upn, cult = MANAGERS[rid]
        regions.append((rid, name, mgr, upn, cult, target))
    write("regions.csv", ["Region ID", "Region", "Manager", "Manager UPN", "Culture", "Monthly Target"], regions)
    # (the Date table is a DAX calculated table: no file, so a scripted table never shows a local path)
    rev = sum(r[7] for r in rows)
    return {"lines": len(rows), "revenue": round(rev), "targets": {r[1]: r[5] for r in regions}}


# ---------------------------------------------------------------- semantic model (TMDL)
_TAGS = [0]


def tag() -> str:
    _TAGS[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"datavideos04/{_TAGS[0]}"))


def q(name: str) -> str:
    return f"'{name}'" if any(c in name for c in " %-") else name


def col(name, dtype, src=None, fmt=None, hidden=False, summarize="none", extra=()):
    out = [f"\tcolumn {q(name)}", f"\t\tdataType: {dtype}"]
    if hidden:
        out.append("\t\tisHidden")
    out += list(extra)
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    out += [f"\t\tlineageTag: {tag()}", f"\t\tsummarizeBy: {summarize}", f"\t\tsourceColumn: {src or name}", ""]
    if dtype == "double" and not fmt:
        out.insert(-1, "\t\tannotation PBI_FormatHint = {\"isGeneralNumber\":true}")
    return out


def calc(name, expr, dtype="string", user=False, sort_by=None, group_by=None, fmt=None, hidden=False,
         summarize="none", desc=None):
    """A calculated column. user=True -> Expression Context = User Context (evaluated at query time)."""
    out = [f"\t/// {desc}"] if desc else []
    if "\n" in expr:
        out += [f"\tcolumn {q(name)} = ```", *[f"\t\t\t{ln}" for ln in expr.split("\n")], "\t\t\t```"]
    else:
        out.append(f"\tcolumn {q(name)} = {expr}")
    out.append(f"\t\tdataType: {dtype}")
    if hidden:
        out.append("\t\tisHidden")
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    out += [f"\t\tlineageTag: {tag()}", f"\t\tsummarizeBy: {summarize}"]
    if user:
        out.append("\t\texpressionContext: userContext")
    if sort_by:
        out.append(f"\t\tsortByColumn: {q(sort_by)}")
    if group_by:
        out += ["", "\t\trelatedColumnDetails", f"\t\t\tgroupByColumn: {q(group_by)}"]
    out.append("")
    return out


def m_partition(table: str, file: str, types: list[tuple[str, str]], keep: list[str] | None = None) -> list[str]:
    tlist = ", ".join('{"%s", %s}' % (c, t) for c, t in types)
    if DATA_URL:
        src = f'Web.Contents("{DATA_URL.rstrip("/")}/{file}")'
    else:
        src = f'File.Contents("{DATA / file}")'
    steps = [f'\t\t\t\t\tSource = Csv.Document({src}, [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
             "\t\t\t\t\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),"]
    last = "Headers"
    if keep:
        klist = ", ".join(f'"{c}"' for c in keep)
        steps.append(f"\t\t\t\t\tKept = Table.SelectColumns(Headers, {{{klist}}}),")
        last = "Kept"
    steps.append(f'\t\t\t\t\tTyped = Table.TransformColumnTypes({last}, {{{tlist}}}, "en-US")')
    return [f"\tpartition {q(table)} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet", *steps,
            "\t\t\t\tin", "\t\t\t\t\tTyped", ""]


def measure(name, expr, fmt=None, desc=None):
    out = [f"\t/// {desc}"] if desc else []
    if "\n" in expr:
        out += [f"\tmeasure {q(name)} = ```", *[f"\t\t\t{ln}" for ln in expr.split("\n")], "\t\t\t```"]
    else:
        out.append(f"\tmeasure {q(name)} = {expr}")
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    out += [f"\t\tlineageTag: {tag()}", ""]
    return out


MONEY = '\\$#,0;(\\$#,0);\\$#,0'
PCT = "0%;-0%;0%"
MINE, OTHERS = "\u2605 My region", "Other regions"

# --- the user-aware columns (the DAX shown in the video) ---
MY_REGION = f'IF ( Regions[Manager UPN] = USERPRINCIPALNAME (), "{MINE}", "{OTHERS}" )'
# the viewer's language: USERCULTURE() (browser / app language). Desktop has no "view as culture", so the
# video also reads a preferred culture from the manager row and falls back to USERCULTURE().
CULTURE = ("COALESCE (\n    LOOKUPVALUE ( Regions[Culture], Regions[Manager UPN], USERPRINCIPALNAME () ),\n"
           "    USERCULTURE ()\n)")
MONTH_STD = 'FORMAT ( DATE ( 2020, \'Date\'[Month Number], 1 ), "mmm" )'
DAY_STD = 'FORMAT ( DATE ( 2020, 1, 5 + \'Date\'[Day of Week Number] ), "dddd" )'


def month_local():
    return ("VAR Lang =\n    " + CULTURE.replace("\n", "\n    ") + "\nRETURN\n"
            "    FORMAT ( DATE ( 2020, 'Date'[Month Number], 1 ), \"mmm\", Lang )")


def day_local():
    return ("VAR Lang =\n    " + CULTURE.replace("\n", "\n    ") + "\nRETURN\n"
            "    FORMAT ( DATE ( 2020, 1, 5 + 'Date'[Day of Week Number] ), \"dddd\", Lang )")


SUPPLIER = "LOOKUPVALUE ( 'Product Cost'[Supplier], 'Product Cost'[Product ID], Products[Product ID] )"
BAND = "LOOKUPVALUE ( 'Product Cost'[Margin Band], 'Product Cost'[Product ID], Products[Product ID] )"
LINE_AMOUNT = "Sales[Quantity] * Sales[Unit Price]"


DATE_TABLE_DAX = """ADDCOLUMNS (
    CALENDAR ( DATE ( 2025, 1, 1 ), DATE ( 2026, 10, 31 ) ),
    "Year Month", DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 ),
    "Year", YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Day of Week Number", WEEKDAY ( [Date], 2 )
)"""


def date_table(stage: str) -> list[str]:
    """The Date table (a DAX calculated table). stage: start (plain names), month (Month user-aware, done in the UI
    on camera), weekday (+ Weekday user-aware, no Group By: the slicer gotcha), final (both grouped by their keys)."""
    month_uc = stage in ("month", "weekday", "final")
    day_uc = stage in ("weekday", "final")
    grouped = stage == "final"
    return ["table Date", f"\tlineageTag: {tag()}", "",
            *col("Date", "dateTime", src="[Date]", fmt="Short Date", extra=["\t\tisKey"]),
            *col("Year Month", "dateTime", src="[Year Month]", fmt="mmm yy"),
            *col("Year", "int64", src="[Year]", fmt="0"),
            *col("Month Number", "int64", src="[Month Number]", fmt="0", hidden=True),
            *col("Day of Week Number", "int64", src="[Day of Week Number]", fmt="0", hidden=True),
            *(calc("Month", month_local(), user=True, sort_by="Month Number",
                   group_by="Month Number" if grouped else None)
              if month_uc else calc("Month", MONTH_STD, sort_by="Month Number")),
            *(calc("Weekday", day_local(), user=True, sort_by="Day of Week Number",
                   group_by="Day of Week Number" if grouped else None)
              if day_uc else calc("Weekday", DAY_STD, sort_by="Day of Week Number")),
            "\tpartition Date = calculated", "\t\tmode: import", "\t\tsource = ```",
            *[f"\t\t\t\t{ln}" for ln in DATE_TABLE_DAX.split("\n")], "\t\t\t\t```", ""]


def as_script(table_lines: list[str]) -> str:
    """A TMDL view script (createOrReplace) for a whole table, without lineage tags."""
    body = [("\t" + ln if ln.strip() else "") for ln in table_lines if "lineageTag" not in ln]
    return "createOrReplace\n\n" + "\n".join(body).rstrip() + "\n"


def write_scripts(folder: Path):
    """The scripts pasted in the video (and published in the materials)."""
    folder.mkdir(parents=True, exist_ok=True)
    w = lambda name, text: (folder / name).write_text(text, encoding="utf-8", newline="\n")
    w("1_my_region.dax", "// Regions table > New column, then Properties > Advanced > Expression Context = User Context\n"
      f"My Region =\n{MY_REGION}\n")
    w("2a_month.dax", "// Date table: set Expression Context = User Context first, then replace the formula\n"
      f"Month =\n{month_local()}\n")
    w("2b_weekday_user_context.tmdl", "\n".join([
        "createOrReplace", "", "\tref table Date", "", "\t\tcolumn Weekday = ```",
        *[f"\t\t\t\t{ln}" for ln in day_local().split("\n")], "\t\t\t\t```",
        "\t\t\tdataType: string", "\t\t\tsummarizeBy: none", "\t\t\texpressionContext: userContext",
        "\t\t\tsortByColumn: 'Day of Week Number'", ""]))
    w("2c_group_by_keys.tmdl", as_script(date_table("final")))
    w("3_cost_columns_and_role.tmdl", "\n".join([
        "createOrReplace", "", "\tref table Products", "",
        f"\t\tcolumn Supplier = {SUPPLIER}", "\t\t\tdataType: string", "\t\t\tsummarizeBy: none",
        "\t\t\texpressionContext: userContext", "",
        f"\t\tcolumn 'Margin Band' = {BAND}", "\t\t\tdataType: string", "\t\t\tsummarizeBy: none",
        "\t\t\texpressionContext: userContext", "",
        "\trole 'Sales Rep'", "\t\tmodelPermission: read", "",
        "\t\ttablePermission 'Product Cost' = FALSE()", ""]))
    w("3_cost_columns_take.tmdl", "\n".join([   # the same columns without the role (it exists already in the take)
        "createOrReplace", "", "\tref table Products", "",
        f"\t\tcolumn Supplier = {SUPPLIER}", "\t\t\tdataType: string", "\t\t\tsummarizeBy: none",
        "\t\t\texpressionContext: userContext", "",
        f"\t\tcolumn 'Margin Band' = {BAND}", "\t\t\tdataType: string", "\t\t\tsummarizeBy: none",
        "\t\t\texpressionContext: userContext", ""]))
    w("4_storage_check.dax", STORAGE_DAX)


STORAGE_DAX = """// How much data does each column store? (DAX query view)
DEFINE
    VAR Seg = SELECTCOLUMNS ( INFO.STORAGETABLECOLUMNSEGMENTS (), "Id", [TABLE_ID] & [COLUMN_ID], "Bytes", [USED_SIZE] )
EVALUATE
ADDCOLUMNS (
    DATATABLE ( "Column", STRING, { { "Sales Amount" }, { "Line Amount" } } ),
    "Data KB",
        VAR c = [Column]
        RETURN ROUND ( SUMX ( FILTER ( Seg, CONTAINSSTRING ( [Id], c ) ), [Bytes] ) / 1024, 1 )
)
"""


def build_model(root: Path):
    final = STAGE == "final"
    sm = root / f"{NAME}.SemanticModel"
    d = sm / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (d / "roles").mkdir(parents=True, exist_ok=True)
    write_json(sm / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    write_json(sm / ".platform", platform("SemanticModel"))
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1705\n\n", encoding="utf-8")
    tables = ["Sales", "Products", "Regions", "Date", "Product Cost"]
    (d / "model.tmdl").write_text("\n".join([
        "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures", "\tsourceQueryCulture: en-US", "\tdataAccessOptions",
        "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        'annotation PBI_QueryOrder = ["Sales","Products","Regions","Date","Product Cost"]', "",
        *[f"ref table {q(t)}" for t in tables], ""]), encoding="utf-8")

    sales = ["table Sales", f"\tlineageTag: {tag()}", "",
             *measure("Revenue", "SUM ( Sales[Sales Amount] )", MONEY),
             *measure("Orders", "DISTINCTCOUNT ( Sales[Order ID] )", "#,0"),
             *measure("Units", "SUM ( Sales[Quantity] )", "#,0"),
             *measure("My Revenue",
                      "CALCULATE ( [Revenue], KEEPFILTERS ( Regions[Manager UPN] = USERPRINCIPALNAME () ) )",
                      MONEY, desc="Revenue of the viewer's own region (blank if the viewer manages no region). "
                      "Filters Manager UPN: a measure filtering the user-context column failed in the preview"),
             *measure("My Share", "DIVIDE ( [My Revenue], CALCULATE ( [Revenue], REMOVEFILTERS ( Regions ) ) )",
                      PCT),
             *measure("Avg Monthly Revenue", "DIVIDE ( [Revenue], DISTINCTCOUNT ( 'Date'[Year Month] ) )", MONEY),
             *measure("Monthly Target", "SUM ( Regions[Monthly Target] )", MONEY),
             *measure("vs Target", "DIVIDE ( [Avg Monthly Revenue], [Monthly Target] )", PCT),
             *measure("Greeting", "\n".join([
                 "VAR Who = LOOKUPVALUE ( Regions[Manager], Regions[Manager UPN], USERPRINCIPALNAME () )",
                 "RETURN",
                 '    IF ( ISBLANK ( Who ), "Hi there \U0001F44B", "Hi " & Who & " \U0001F44B" )'])),
             *measure("Cost Access", "\n".join([
                 "IF (",
                 "    ISEMPTY ( 'Product Cost' ),",
                 '    "\U0001F512  Cost table blocked for your role",',
                 '    "\u2705  Cost table visible"',
                 ")"])),
             *col("Order ID", "int64", fmt="0"),
             *col("Order Date", "dateTime", fmt="Short Date"),
             *col("Product ID", "int64", fmt="0", hidden=True),
             *col("Region ID", "int64", fmt="0", hidden=True),
             *col("Quantity", "int64", fmt="#,0", summarize="sum"),
             *col("Unit Price", "double", fmt=MONEY, summarize="sum"),
             *col("Sales Amount", "double", fmt=MONEY, summarize="sum"),
             *calc("Line Amount", LINE_AMOUNT, dtype="double", user=True, fmt=MONEY, summarize="sum",
                   desc="Same numbers as Sales Amount, but computed at query time: not stored"),
             *m_partition("Sales", "sales.csv", [
                 ("Order ID", "Int64.Type"), ("Order Date", "type date"), ("Product ID", "Int64.Type"),
                 ("Region ID", "Int64.Type"), ("Quantity", "Int64.Type"), ("Unit Price", "type number"),
                 ("Sales Amount", "type number")],
                 keep=["Order ID", "Order Date", "Product ID", "Region ID", "Quantity", "Unit Price",
                       "Sales Amount"])]
    products = ["table Products", f"\tlineageTag: {tag()}", "",
                *col("Product ID", "int64", fmt="0", hidden=True, extra=["\t\tisKey"]),
                *col("Product", "string"), *col("Category", "string"),
                *calc("Supplier", SUPPLIER, user=final),
                *calc("Margin Band", BAND, user=final),
                *m_partition("Products", "products.csv", [
                    ("Product ID", "Int64.Type"), ("Product", "type text"), ("Category", "type text")])]
    regions = ["table Regions", f"\tlineageTag: {tag()}", "",
               *col("Region ID", "int64", fmt="0", hidden=True, extra=["\t\tisKey"]),
               *col("Region", "string"), *col("Manager", "string"), *col("Manager UPN", "string"),
               *col("Culture", "string"),
               *col("Monthly Target", "int64", fmt=MONEY, hidden=True, summarize="sum"),
               *calc("My Region", MY_REGION, user=True,
                     desc="Evaluated per viewer: the region this viewer manages, versus all the others"),
               *m_partition("Regions", "regions.csv", [
                   ("Region ID", "Int64.Type"), ("Region", "type text"), ("Manager", "type text"),
                   ("Manager UPN", "type text"), ("Culture", "type text"), ("Monthly Target", "Int64.Type")])]
    date = date_table("final" if final else "start")
    cost =["table 'Product Cost'", "\tisHidden", f"\tlineageTag: {tag()}", "",
            *col("Product ID", "int64", fmt="0"),
            *col("Supplier", "string"),
            *col("Unit Cost", "double", fmt=MONEY),
            *col("Margin Band", "string"),
            *m_partition("Product Cost", "product_cost.csv", [
                ("Product ID", "Int64.Type"), ("Supplier", "type text"), ("Unit Cost", "type number"),
                ("Margin Band", "type text")])]

    for t, lines in (("Sales", sales), ("Products", products), ("Regions", regions), ("Date", date),
                     ("Product Cost", cost)):
        (d / "tables" / f"{t}.tmdl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    rel = []
    for name, a, b in (("Sales_Products", "Sales.'Product ID'", "Products.'Product ID'"),
                       ("Sales_Regions", "Sales.'Region ID'", "Regions.'Region ID'"),
                       ("Sales_Date", "Sales.'Order Date'", "Date.Date")):
        rel += [f"relationship {name}", f"\tfromColumn: {a}", f"\ttoColumn: {b}", ""]
    (d / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")
    # the restricted role: the cost table is empty for it (no relationship, so sales rows are untouched)
    (d / "roles" / "Sales Rep.tmdl").write_text("\n".join([
        "role 'Sales Rep'", "\tmodelPermission: read", "",
        "\ttablePermission 'Product Cost' = FALSE()", "",
        f"\tannotation PBI_Id = {uuid.uuid5(uuid.NAMESPACE_URL, 'datavideos04/role').hex}", ""]), encoding="utf-8")
    # Model view layout for the camera: the cost table stands apart (top right), no lines to it
    tags = {t: next(ln.split(": ")[1] for ln in lines if ln.startswith("\tlineageTag"))
            for t, lines in (("Sales", sales), ("Products", products), ("Regions", regions), ("Date", date),
                             ("Product Cost", cost))}
    boxes = {"Products": (0, 0, 240, 230), "Regions": (0, 280, 240, 270), "Sales": (320, 60, 240, 330),
             "Date": (640, 280, 240, 270), "Product Cost": (960, 0, 240, 170)}
    write_json(sm / "diagramLayout.json", {
        "version": "1.1.0",
        "diagrams": [{"ordinal": 0, "scrollPosition": {"x": 0, "y": 0},
                      "nodes": [{"location": {"x": x, "y": y}, "nodeIndex": t, "nodeLineageTag": tags[t],
                                 "size": {"height": h, "width": w}, "zIndex": i}
                                for i, (t, (x, y, w, h)) in enumerate(boxes.items())],
                      "name": "All tables", "zoomValue": 100, "pinKeyFieldsToTop": False,
                      "showExtraHeaderInfo": False, "hideKeyFieldsWhenCollapsed": False, "tablesLocked": False}],
        "selectedDiagram": "All tables", "defaultDiagram": "All tables"})


# ---------------------------------------------------------------- report (PBIR): new look for 04
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
PAPER, BAND_BG, CARD_LINE, GRID = "#F6F4EF", "#13233F", "#E8E2D6", "#EFEBE3"
INK, MUTED, LIGHT = "#1E293B", "#6B7280", "#CBD5E1"
AMBER, SLATE, TEAL, BLUE, ROSE = "#F59E0B", "#A7B1C2", "#0EA5A4", "#2F6FED", "#E11D48"
P1, P2, P3 = "a4f0c3d2e4b5a6978801", "b4f1e1d2a3c4b5d6e702", "c4a2b1d0e9f8a7b6c503"


def lit(v): return {"expr": {"Literal": {"Value": v}}}
def s(t): return lit("'" + t.replace("'", "''") + "'")
def dnum(n): return lit(f"{n}D")
def lnum(n): return lit(f"{n}L")
def b(flag): return lit("true" if flag else "false")
def color(h): return {"solid": {"color": s(h)}}
def props(**kw): return [{"properties": kw}]
def dprops(**kw): return [{"properties": kw, "selector": {"id": "default"}}]


def fld(kind, entity, prop):
    return {kind: {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj(kind, entity, prop, active=None):
    p = {"field": fld(kind, entity, prop), "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if active is not None:
        p["active"] = active
    return p


def container(title: str | None, bg="#FFFFFF", border=True):
    o = {
        "background": props(show=b(True), color=color(bg), transparency=dnum(0)),
        "border": props(show=b(border), color=color(CARD_LINE), radius=dnum(14)),
        "padding": props(top=lnum(10), bottom=lnum(10), left=lnum(16), right=lnum(16)),
        "dropShadow": props(show=b(False)),
        "visualHeader": props(show=b(False)),
    }
    o["title"] = props(show=b(bool(title)), text=s(title or ""), fontColor=color(INK), fontSize=dnum(12),
                       bold=b(True), alignment=s("left"), fontFamily=s("Segoe UI Semibold"))
    return o


def axis_objects(legend=False):
    return {
        "categoryAxis": props(show=b(True), fontSize=dnum(10), labelColor=color(MUTED), showAxisTitle=b(False)),
        "valueAxis": props(show=b(False), showAxisTitle=b(False), gridlineShow=b(False)),
        "legend": props(show=b(legend), position=s("TopRight"), fontSize=dnum(10), labelColor=color(INK)),
    }


def series_colors(entity, column, mapping: dict[str, str]):
    """dataPoint fill per legend value (e.g. '★ My region' amber, 'Other regions' slate)."""
    out = []
    for value, hexc in mapping.items():
        out.append({"properties": {"fill": color(hexc)},
                    "selector": {"data": [{"scopeId": {"Comparison": {
                        "ComparisonKind": 0,
                        "Left": fld("Column", entity, column),
                        "Right": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}}}]}})
    return out


def visual(name, x, y, w, h, z, vtype, query=None, objects=None, vco=None, sort=None, drill=True):
    v = {"visualType": vtype}
    if query:
        v["query"] = {"queryState": query}
        if sort:
            v["query"]["sortDefinition"] = sort
    if objects:
        v["objects"] = objects
    if vco:
        v["visualContainerObjects"] = vco
    if drill:
        v["drillFilterOtherVisuals"] = True
    return {"$schema": VC, "name": name,
            "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}, "visual": v}


def kpi_card(name, x, y, w, h, z, measure_name, label, accent, units=0, decimals=None, entity="Sales", size=28,
             fg=INK, bg="#FFFFFF", border=True, align="left"):
    value = dict(fontSize=dnum(size), bold=b(True), fontColor=color(fg), horizontalAlignment=s(align),
                 labelDisplayUnits=dnum(units))
    if decimals is not None:
        value["labelPrecision"] = lnum(decimals)
    objects = {
        "value": dprops(**value),
        "label": dprops(show=b(bool(label)), fontSize=dnum(11), fontColor=color(MUTED), horizontalAlignment=s(align),
                        text=s(label or ""), position=s("aboveValue")),
        "accentBar": dprops(show=b(bool(accent)), position=s("Left"), color=color(accent or AMBER), width=dnum(5)),
        "outline": dprops(show=b(False)),
        "fillCustom": dprops(show=b(False)),
        "padding": dprops(paddingUniform=lnum(12)),
    }
    vco = container(None, bg=bg, border=border)
    if bg == "transparent":
        vco["background"] = props(show=b(False))
    return visual(name, x, y, w, h, z, "cardVisual",
                  query={"Data": {"projections": [proj("Measure", entity, measure_name)]}},
                  objects=objects, vco=vco)


def band(name, title, subtitle):
    """Full-width navy header band with a white title (new look for video 04)."""
    paras = [{"textRuns": [{"value": title, "textStyle": {
        "fontSize": "20pt", "fontWeight": "bold", "color": "#FFFFFF", "fontFamily": "Segoe UI Semibold"}}]},
        {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "10pt", "color": LIGHT}}]}]
    vco = {"background": props(show=b(True), color=color(BAND_BG), transparency=dnum(0)),
           "border": props(show=b(False)),
           "padding": props(top=lnum(10), bottom=lnum(6), left=lnum(28), right=lnum(20))}
    return visual(name, 0, 0, 1280, 76, 1000, "textbox", objects={"general": [{"properties": {"paragraphs": paras}}]},
                  vco=vco, drill=False)


def greeting(name):
    """'Hi Luc 👋' in the header band: a classic card, transparent, white text (never shows the real UPN)."""
    objects = {"labels": props(color=color("#FFFFFF"), fontSize=dnum(16), fontFamily=s("Segoe UI Semibold")),
               "categoryLabels": props(show=b(False))}
    vco = {"background": props(show=b(False)), "border": props(show=b(False)), "title": props(show=b(False)),
           "visualHeader": props(show=b(False)), "dropShadow": props(show=b(False))}
    return visual(name, 900, 10, 360, 56, 1100, "card",
                  query={"Values": {"projections": [proj("Measure", "Sales", "Greeting")]}},
                  objects=objects, vco=vco, drill=False)


TBL_OBJ = {
    "columnHeaders": props(fontSize=dnum(10), fontColor=color(MUTED), bold=b(True), backColor=color("#FFFFFF")),
    "values": props(fontSize=dnum(11), fontColor=color(INK), backColorPrimary=color("#FFFFFF"),
                    backColorSecondary=color("#FAF8F4")),
    "total": props(totals=b(False)),
    "grid": props(gridHorizontal=b(True), gridHorizontalColor=color(GRID), gridVertical=b(False), rowPadding=dnum(4)),
}


def button_slicer(name, x, y, w, h, z, entity, column, rows, cols, title=None):
    objects = {
        "header": props(show=b(False)),
        "value": dprops(show=b(True), fontSize=dnum(11), bold=b(True), fontColor=color(INK),
                        horizontalAlignment=s("center")),
        "layout": props(rowCount=lnum(rows), columnCount=lnum(cols)),
        "selection": props(singleSelect=b(False)),
    }
    return visual(name, x, y, w, h, z, "advancedSlicerVisual",
                  query={"Values": {"projections": [proj("Column", entity, column, active=True)]}},
                  objects=objects, vco=container(title), drill=False)


def page_json(pid, display):
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": pid, "displayName": display, "displayOption": "FitToPage", "height": 720, "width": 1280,
            "objects": {"background": props(color=color(PAPER), transparency=dnum(0))}}


MINE_COLORS = {MINE: AMBER, OTHERS: SLATE}


def page1() -> list:
    """Example 1: 'Mine', without hiding everyone else."""
    V = [band("a1000000000000000001", "Regional sales", "Aurora Outdoor  \u00b7  Jan 2025 \u2013 Oct 2026  \u00b7  "
              "every region, one report"), greeting("a1000000000000000002")]
    V.append(button_slicer("a2000000000000000001", 24, 92, 300, 104, 1500, "Regions", "My Region", 1, 2))
    for i, (m, label, accent, units, dec) in enumerate([("Revenue", "Total revenue", BLUE, 1000000, 1),
                                                        ("My Revenue", "My region", AMBER, 1000000, 1),
                                                        ("My Share", "My share of total", TEAL, 0, 0)]):
        V.append(kpi_card(f"a30000000000000000{i + 1:02d}", 340 + i * 312, 92, 292, 104, 2000 + i, m, label, accent,
                          units, dec, size=24))
    bar = axis_objects(legend=True)
    bar["dataPoint"] = series_colors("Regions", "My Region", MINE_COLORS)
    bar["labels"] = props(show=b(True), fontSize=dnum(10), color=color(INK), labelDisplayUnits=dnum(1000000),
                          labelPrecision=lnum(1))
    V.append(visual("a4000000000000000001", 24, 212, 500, 266, 3000, "barChart",
                    query={"Category": {"projections": [proj("Column", "Regions", "Region", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Revenue")]},
                           "Series": {"projections": [proj("Column", "Regions", "My Region", active=True)]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Revenue"), "direction": "Descending"}]},
                    objects=bar, vco=container("Revenue by region")))
    colm = axis_objects(legend=True)
    colm["dataPoint"] = series_colors("Regions", "My Region", MINE_COLORS)
    V.append(visual("a4000000000000000002", 540, 212, 716, 266, 3001, "columnChart",
                    query={"Category": {"projections": [proj("Column", "Date", "Month", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Revenue")]},
                           "Series": {"projections": [proj("Column", "Regions", "My Region", active=True)]}},
                    sort={"sort": [{"field": fld("Column", "Date", "Month"), "direction": "Ascending"}]},
                    objects=colm, vco=container("Revenue by month of year")))
    V.append(visual("a5000000000000000001", 24, 494, 1232, 210, 4000, "tableEx",
                    query={"Values": {"projections": [proj("Column", "Regions", "Region"),
                                                      proj("Column", "Regions", "Manager"),
                                                      proj("Column", "Regions", "My Region"),
                                                      proj("Measure", "Sales", "Revenue"),
                                                      proj("Measure", "Sales", "Avg Monthly Revenue"),
                                                      proj("Measure", "Sales", "Monthly Target"),
                                                      proj("Measure", "Sales", "vs Target")]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Revenue"), "direction": "Descending"}]},
                    objects=TBL_OBJ, vco=container("Regional managers")))
    return V


def page2() -> list:
    """Example 2: the report speaks your language."""
    V = [band("b1000000000000000001", "When we sell", "Revenue by month and weekday  \u00b7  "
              "labels in the viewer's language"), greeting("b1000000000000000002")]
    V.append(button_slicer("b2000000000000000001", 24, 92, 1232, 64, 1500, "Date", "Weekday", 1, 7))
    for i, (m, label, accent, units, dec) in enumerate([("Revenue", "Revenue", BLUE, 1000000, 1),
                                                        ("Orders", "Orders", TEAL, 1, 0),
                                                        ("Units", "Units sold", AMBER, 1000, 1)]):
        V.append(kpi_card(f"b30000000000000000{i + 1:02d}", 24 + i * 416, 172, 400, 104, 2000 + i, m, label, accent,
                          units, dec, size=24))
    colm = axis_objects()
    colm["dataPoint"] = props(defaultColor=color(TEAL))
    colm["labels"] = props(show=b(True), fontSize=dnum(9), color=color(INK), labelDisplayUnits=dnum(1000000),
                           labelPrecision=lnum(1))
    V.append(visual("b4000000000000000001", 24, 292, 760, 412, 3000, "clusteredColumnChart",
                    query={"Category": {"projections": [proj("Column", "Date", "Month", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Revenue")]}},
                    sort={"sort": [{"field": fld("Column", "Date", "Month"), "direction": "Ascending"}]},
                    objects=colm, vco=container("Revenue by month")))
    bar = axis_objects()
    bar["dataPoint"] = props(defaultColor=color(AMBER))
    bar["labels"] = props(show=b(True), fontSize=dnum(9), color=color(INK), labelDisplayUnits=dnum(1000000),
                          labelPrecision=lnum(1))
    V.append(visual("b4000000000000000002", 800, 292, 456, 412, 3001, "clusteredBarChart",
                    query={"Category": {"projections": [proj("Column", "Date", "Weekday", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Revenue")]}},
                    sort={"sort": [{"field": fld("Column", "Date", "Weekday"), "direction": "Ascending"}]},
                    objects=bar, vco=container("Revenue by weekday")))
    return V


def page3() -> list:
    """Example 3: redacted, not broken."""
    V = [band("c1000000000000000001", "Product margins", "Supplier and margin band come from a protected cost table"),
         greeting("c1000000000000000002")]
    V.append(kpi_card("c3000000000000000001", 24, 92, 760, 84, 2000, "Cost Access", None, ROSE, size=17))
    V.append(kpi_card("c3000000000000000002", 800, 92, 456, 84, 2001, "Revenue", "Revenue", BLUE, 1000000, 1,
                      size=18))
    V.append(visual("c4000000000000000001", 24, 192, 760, 512, 3000, "tableEx",
                    query={"Values": {"projections": [proj("Column", "Products", "Product"),
                                                      proj("Column", "Products", "Category"),
                                                      proj("Column", "Products", "Supplier"),
                                                      proj("Column", "Products", "Margin Band"),
                                                      proj("Measure", "Sales", "Revenue")]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Revenue"), "direction": "Descending"}]},
                    objects=TBL_OBJ, vco=container("Products")))
    for i, (column, hexc, title) in enumerate([("Margin Band", AMBER, "Revenue by margin band"),
                                               ("Supplier", TEAL, "Revenue by supplier")]):
        bar = axis_objects()
        bar["dataPoint"] = props(defaultColor=color(hexc))
        bar["labels"] = props(show=b(True), fontSize=dnum(9), color=color(INK), labelDisplayUnits=dnum(1000000),
                              labelPrecision=lnum(1))
        V.append(visual(f"c400000000000000000{i + 2}", 800, 192 + i * 264, 456, 248, 3001 + i, "clusteredBarChart",
                        query={"Category": {"projections": [proj("Column", "Products", column, active=True)]},
                               "Y": {"projections": [proj("Measure", "Sales", "Revenue")]}},
                        sort={"sort": [{"field": fld("Measure", "Sales", "Revenue"), "direction": "Descending"}]},
                        objects=bar, vco=container(title)))
    return V


def build_report(root: Path):
    rp = root / f"{NAME}.Report"
    d = rp / "definition"
    write_json(rp / ".platform", platform("Report"))
    write_json(rp / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(d / "version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    theme_dir = rp / "StaticResources" / "SharedResources" / "BaseThemes"
    theme_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BASE_THEME, theme_dir / "CY26SU05.json")
    write_json(d / "report.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY26SU05", "reportVersionAtImport": {
            "visual": "2.12.0", "report": "3.4.0", "page": "2.3.1"}, "type": "SharedResources"}},
        "objects": {"outspacePane": [{"properties": {"expanded": lit("true")}}]},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [
            {"name": "CY26SU05", "path": "BaseThemes/CY26SU05.json", "type": "BaseTheme"}]}],
        "settings": {"useEnhancedTooltips": True}})
    write_json(d / "pages" / "pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [P1, P2, P3], "activePageName": P1, "landingPageName": P1})
    for pid, display, visuals in ((P1, "Regions", page1()), (P2, "Calendar", page2()), (P3, "Products", page3())):
        write_json(d / "pages" / pid / "page.json", page_json(pid, display))
        for v in visuals:
            write_json(d / "pages" / pid / "visuals" / v["name"] / "visual.json", v)


# ---------------------------------------------------------------- helpers
def platform(kind):
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": kind, "displayName": NAME},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid5(uuid.NAMESPACE_URL, "datavideos04/" + kind))}}


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main(out: Path = PBIP):
    stats = build_data()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    write_json(out / f"{NAME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})
    build_model(out)
    build_report(out)
    write_scripts(HERE / "scripts")
    print(json.dumps(stats))


def _arg(flag):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else None


if __name__ == "__main__":
    DATA_URL = _arg("--data-url")
    STAGE = _arg("--stage") or "start"
    main(Path(_arg("--out")) if _arg("--out") else PBIP)
