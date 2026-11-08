"""Build the demo dataset (CSV) and the deliberately plain "before" Power BI project (PBIP: PBIR + TMDL) for
video 03 (AI Skills for Power BI, episode 1).

Bean There Coffee Co. is a made-up chain of 8 cafes in Canada (synthetic data, fixed seed):
  - sales by day x store x product x channel (In-store, Mobile Order, Delivery), Jul 2024 - Oct 2026
  - tickets (transactions) by day x store x channel
  - two stores opened recently (Calgary Beltline 2025-09, Toronto Union Station 2026-03), so "same-store"
    growth differs from total growth
  - the company's fiscal year starts July 1, and delivery orders pay the delivery app a commission.
    Neither fact is in the model: that is what the business-context file adds in the video.

The report is a typical first draft on purpose: default theme, auto titles, a pie chart, uneven layout,
"Page 1" / "Page 2". The model has no descriptions, no display folders and a few cryptic names.

Run: C:\\Python315\\python.exe -I build_report.py [--out <folder>] [--data-dir <folder for the CSVs>]
                                                   [--data-url <base url for the CSVs>]
Default output: next to this script
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import random
import shutil
import sys
import uuid
from pathlib import Path

WORK = Path(__file__).resolve().parent
HERE = Path(__file__).resolve().parent
NAME = "BeanThere_Sales"
BASE_THEME = HERE / "theme" / "CY26SU05.json"
DATA = WORK / "data"     # --data-dir
DATA_URL = None          # --data-url: the published materials read the CSVs from GitHub instead of a local folder

# ---------------------------------------------------------------- data
# id, name, city, province, open date, size (relative traffic)
STORES = [
    (1, "King West", "Toronto", "ON", dt.date(2019, 5, 1), 1.15),
    (2, "Yorkville", "Toronto", "ON", dt.date(2020, 2, 1), 1.00),
    (3, "Distillery", "Toronto", "ON", dt.date(2021, 6, 1), 0.85),
    (4, "Plateau", "Montreal", "QC", dt.date(2021, 9, 1), 0.95),
    (5, "Old Port", "Montreal", "QC", dt.date(2022, 4, 1), 0.80),
    (6, "Gastown", "Vancouver", "BC", dt.date(2022, 10, 1), 1.05),
    (7, "Beltline", "Calgary", "AB", dt.date(2025, 9, 15), 0.90),
    (8, "Union Station", "Toronto", "ON", dt.date(2026, 3, 2), 1.30),
]
# id, product, category, price, unit cost, base weight, cold (1 = iced drink, -1 = hot drink, 0 = neutral)
PRODUCTS = [
    (1, "Latte", "Espresso Bar", 5.75, 1.35, 1.00, -1), (2, "Cappuccino", "Espresso Bar", 5.25, 1.20, 0.55, -1),
    (3, "Americano", "Espresso Bar", 3.95, 0.70, 0.60, -1), (4, "Drip Coffee", "Brewed & Cold", 2.95, 0.45, 0.85, -1),
    (5, "Cold Brew", "Brewed & Cold", 4.95, 0.95, 0.45, 1), (6, "Iced Latte", "Brewed & Cold", 6.25, 1.55, 0.50, 1),
    (7, "Matcha Latte", "Tea & More", 6.25, 1.80, 0.30, 0), (8, "Chai Latte", "Tea & More", 5.75, 1.45, 0.25, -1),
    (9, "Butter Croissant", "Bakery & Food", 3.75, 1.45, 0.55, 0), (10, "Banana Bread", "Bakery & Food", 3.95, 1.30, 0.30, 0),
    (11, "Breakfast Sandwich", "Bakery & Food", 7.95, 3.30, 0.35, 0), (12, "Whole Bean Bag 340g", "Retail", 18.99, 9.80, 0.05, 0),
]
CHANNELS = [(1, "In-store", 0.64), (2, "Mobile Order", 0.24), (3, "Delivery", 0.12)]
START, END = dt.date(2024, 7, 1), dt.date(2026, 10, 31)
SEASON = {1: .90, 2: .92, 3: .97, 4: 1.0, 5: 1.04, 6: 1.06, 7: 1.03, 8: 1.0, 9: 1.04, 10: 1.03, 11: 1.0, 12: 1.08}
COLD = {1: .35, 2: .4, 3: .6, 4: .85, 5: 1.25, 6: 1.6, 7: 1.85, 8: 1.75, 9: 1.2, 10: .75, 11: .45, 12: .35}


def noisy(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    return max(0, int(round(rng.gauss(lam, math.sqrt(lam) * 1.1))))


def build_data(data_dir: Path) -> dict:
    rng = random.Random(20261108)
    data_dir.mkdir(parents=True, exist_ok=True)
    sales, tickets = [], []
    day = START
    while day <= END:
        years = (day - START).days / 365.25
        weekday = [0.98, 1.0, 1.02, 1.03, 1.08, 1.12, 0.92][day.weekday()]
        for sid, _, city, _, opened, size in STORES:
            if day < opened:
                continue
            age_days = (day - opened).days
            ramp = min(1.0, 0.55 + 0.45 * age_days / 120)               # new stores ramp up over ~4 months
            growth = 1.0 + 0.055 * years                                # same-store growth ~5.5% a year
            if sid == 8:
                weekday_f = [1.25, 1.25, 1.25, 1.25, 1.15, 0.55, 0.45][day.weekday()]   # commuter store
            else:
                weekday_f = weekday
            base = 430 * size * ramp * growth * weekday_f * SEASON[day.month]
            if city == "Vancouver" and day.month in (11, 12, 1, 2):
                base *= 0.94                                            # rainy-season dip
            for cid, _, share in CHANNELS:
                sh = share
                if cid == 3:
                    sh = share * (0.85 + 0.22 * years)                  # delivery keeps growing
                elif cid == 2:
                    sh = share * (0.92 + 0.08 * years)
                n_t = noisy(rng, base * sh)
                if n_t == 0:
                    continue
                tickets.append([day.isoformat(), sid, cid, n_t])
                items = n_t * (1.62 if cid == 3 else 1.38)              # delivery baskets are bigger
                for pid, _, cat, price, cost, wgt, cold in PRODUCTS:
                    w = wgt
                    if cold == 1:
                        w *= COLD[day.month]
                    elif cold == -1:
                        w *= 1.12 - 0.12 * COLD[day.month]
                    if cat == "Bakery & Food":
                        w *= 1.35 if cid == 3 else 1.0
                        if day.weekday() >= 5:
                            w *= 1.2
                    if cat == "Retail" and cid == 3:
                        w *= 0.3
                    if pid == 7:
                        w *= 1.0 + 0.35 * years                           # matcha trend
                    lam = items * w / 6.75
                    q = noisy(rng, lam)
                    if q == 0:
                        continue
                    p = price * (0.95 if cid == 2 else 1.0)              # 5% app discount on mobile orders
                    rev = round(q * p, 2)
                    cg = round(q * cost * rng.uniform(.985, 1.015), 2)
                    sales.append([day.isoformat(), sid, pid, cid, q, rev, cg])
        day += dt.timedelta(days=1)

    def write(name, header, rows):
        with open(data_dir / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    write("sales.csv", ["Date", "StoreID", "ProductID", "ChannelID", "Qty", "Net Sales", "COGS"], sales)
    write("tickets.csv", ["Date", "StoreID", "ChannelID", "Tickets"], tickets)
    write("stores.csv", ["StoreID", "Store Name", "City", "Province", "Open Date"],
          [[s[0], s[1], s[2], s[3], s[4].isoformat()] for s in STORES])
    write("products.csv", ["ProductID", "Product", "Category", "List Price"], [p[:4] for p in PRODUCTS])
    write("channels.csv", ["ChannelID", "Channel"], [c[:2] for c in CHANNELS])
    dates = []
    d = START
    while d <= END:
        dates.append([d.isoformat(), d.year, d.replace(day=1).isoformat(), d.strftime("%b"), d.month,
                      d.strftime("%a"), d.isoweekday()])
        d += dt.timedelta(days=1)
    write("date.csv", ["Date", "Year", "Month", "Month Name", "Month No", "Weekday", "Weekday No"], dates)
    rev = sum(r[5] for r in sales)
    cogs = sum(r[6] for r in sales)
    return {"sales_rows": len(sales), "ticket_rows": len(tickets), "revenue": round(rev),
            "gm_pct": round(1 - cogs / rev, 3), "tickets": sum(t[3] for t in tickets)}


# ---------------------------------------------------------------- semantic model (TMDL)
_TAGS = [0]


def tag() -> str:
    _TAGS[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"datavideos03/{_TAGS[0]}"))


def q(name: str) -> str:
    return f"'{name}'" if any(c in name for c in " %-&") else name


def col(name, dtype, src=None, fmt=None, summarize="none", extra=()):
    out = [f"\tcolumn {q(name)}", f"\t\tdataType: {dtype}"]
    out += list(extra)
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    out += [f"\t\tlineageTag: {tag()}", f"\t\tsummarizeBy: {summarize}", f"\t\tsourceColumn: {src or name}", ""]
    if dtype == "double" and not fmt:
        out.insert(-1, "\t\tannotation PBI_FormatHint = {\"isGeneralNumber\":true}")
    return out


def m_partition(table: str, file: str, types: list[tuple[str, str]], data_dir: Path) -> list[str]:
    tlist = ", ".join('{"%s", %s}' % (c, t) for c, t in types)
    if DATA_URL:
        src = f'Web.Contents("{DATA_URL.rstrip("/")}/{file}")'
    else:
        src = f'File.Contents("{data_dir / file}")'
    return [
        f"\tpartition {q(table)} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\t\tlet",
        f'\t\t\t\t\tSource = Csv.Document({src}, [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "\t\t\t\t\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'\t\t\t\t\tTyped = Table.TransformColumnTypes(Headers, {{{tlist}}}, "en-US")',
        "\t\t\t\tin",
        "\t\t\t\t\tTyped",
        "",
    ]


def measure(name, expr, fmt=None):
    out = [f"\tmeasure {q(name)} = {expr}"]
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    out += [f"\t\tlineageTag: {tag()}", ""]
    return out


MONEY = '\\$#,0;(\\$#,0);\\$#,0'
MONEY2 = '\\$#,0.00;(\\$#,0.00);\\$#,0.00'
PCT = "0.0%;-0.0%;0.0%"


def build_model(root: Path, data_dir: Path):
    sm = root / f"{NAME}.SemanticModel"
    d = sm / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    write_json(sm / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    write_json(sm / ".platform", platform("SemanticModel"))
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1600\n\n", encoding="utf-8")
    tables = ["Sales", "Tickets", "Stores", "Products", "Channels", "Date"]
    (d / "model.tmdl").write_text("\n".join([
        "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US", "\tdataAccessOptions",
        "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        'annotation PBI_QueryOrder = ["Sales","Tickets","Stores","Products","Channels","Date"]', "",
        *[f"ref table {q(t)}" for t in tables], ""]), encoding="utf-8")

    sales = ["table Sales", f"\tlineageTag: {tag()}", "",
             *measure("Total Sales", "SUM(Sales[Net Sales])", MONEY),
             *measure("Total COGS", "SUM(Sales[COGS])", MONEY),
             *measure("GM", "[Total Sales] - [Total COGS]", MONEY),
             *measure("GM %", "DIVIDE([GM], [Total Sales])", PCT),
             *measure("Units", "SUM(Sales[Qty])", "#,0"),
             *col("Date", "dateTime", fmt="Short Date"),
             *col("StoreID", "int64", fmt="0"),
             *col("ProductID", "int64", fmt="0"),
             *col("ChannelID", "int64", fmt="0"),
             *col("Qty", "int64", fmt="#,0", summarize="sum"),
             *col("Net Sales", "double", fmt=MONEY2, summarize="sum"),
             *col("COGS", "double", fmt=MONEY2, summarize="sum"),
             *m_partition("Sales", "sales.csv", [
                 ("Date", "type date"), ("StoreID", "Int64.Type"), ("ProductID", "Int64.Type"),
                 ("ChannelID", "Int64.Type"), ("Qty", "Int64.Type"), ("Net Sales", "type number"),
                 ("COGS", "type number")], data_dir)]
    tix = ["table Tickets", f"\tlineageTag: {tag()}", "",
           *measure("Ticket Count", "SUM(Tickets[Tickets])", "#,0"),
           *measure("Avg Ticket", "DIVIDE([Total Sales], [Ticket Count])", MONEY2),
           *col("Date", "dateTime", fmt="Short Date"),
           *col("StoreID", "int64", fmt="0"),
           *col("ChannelID", "int64", fmt="0"),
           *col("Tickets", "int64", fmt="#,0", summarize="sum"),
           *m_partition("Tickets", "tickets.csv", [
               ("Date", "type date"), ("StoreID", "Int64.Type"), ("ChannelID", "Int64.Type"),
               ("Tickets", "Int64.Type")], data_dir)]
    stores = ["table Stores", f"\tlineageTag: {tag()}", "",
              *col("StoreID", "int64", fmt="0", extra=["\t\tisKey"]),
              *col("Store Name", "string"), *col("City", "string"), *col("Province", "string"),
              *col("Open Date", "dateTime", fmt="Short Date"),
              *m_partition("Stores", "stores.csv", [
                  ("StoreID", "Int64.Type"), ("Store Name", "type text"), ("City", "type text"),
                  ("Province", "type text"), ("Open Date", "type date")], data_dir)]
    products = ["table Products", f"\tlineageTag: {tag()}", "",
                *col("ProductID", "int64", fmt="0", extra=["\t\tisKey"]),
                *col("Product", "string"), *col("Category", "string"),
                *col("List Price", "double", fmt=MONEY2),
                *m_partition("Products", "products.csv", [
                    ("ProductID", "Int64.Type"), ("Product", "type text"), ("Category", "type text"),
                    ("List Price", "type number")], data_dir)]
    channels = ["table Channels", f"\tlineageTag: {tag()}", "",
                *col("ChannelID", "int64", fmt="0", extra=["\t\tisKey"]),
                *col("Channel", "string"),
                *m_partition("Channels", "channels.csv", [("ChannelID", "Int64.Type"), ("Channel", "type text")],
                             data_dir)]
    date = ["table Date", f"\tlineageTag: {tag()}", "",
            *col("Date", "dateTime", fmt="Short Date", extra=["\t\tisKey"]),
            *col("Year", "int64", fmt="0"),
            *col("Month", "dateTime", fmt="mmm yyyy"),
            *col("Month Name", "string", extra=["\t\tsortByColumn: 'Month No'"]),
            *col("Month No", "int64", fmt="0"),
            *col("Weekday", "string", extra=["\t\tsortByColumn: 'Weekday No'"]),
            *col("Weekday No", "int64", fmt="0"),
            *m_partition("Date", "date.csv", [
                ("Date", "type date"), ("Year", "Int64.Type"), ("Month", "type date"), ("Month Name", "type text"),
                ("Month No", "Int64.Type"), ("Weekday", "type text"), ("Weekday No", "Int64.Type")], data_dir)]
    for t, lines in (("Sales", sales), ("Tickets", tix), ("Stores", stores), ("Products", products),
                     ("Channels", channels), ("Date", date)):
        (d / "tables" / f"{t}.tmdl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    rel = []
    for name, a, b in (("Sales_Stores", "Sales.StoreID", "Stores.StoreID"),
                       ("Sales_Products", "Sales.ProductID", "Products.ProductID"),
                       ("Sales_Channels", "Sales.ChannelID", "Channels.ChannelID"),
                       ("Sales_Date", "Sales.Date", "Date.Date"),
                       ("Tickets_Stores", "Tickets.StoreID", "Stores.StoreID"),
                       ("Tickets_Channels", "Tickets.ChannelID", "Channels.ChannelID"),
                       ("Tickets_Date", "Tickets.Date", "Date.Date")):
        rel += [f"relationship {name}", f"\tfromColumn: {a}", f"\ttoColumn: {b}", ""]
    (d / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")


# ---------------------------------------------------------------- report (PBIR): a plain first draft
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
P1, P2 = "a03f1c2d3e4b5a697801", "b03f2e1d0c9b8a7f6e02"


def lit(v): return {"expr": {"Literal": {"Value": v}}}
def s(t): return lit("'" + t.replace("'", "''") + "'")


def fld(kind, entity, prop):
    return {kind: {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj(kind, entity, prop, active=None):
    p = {"field": fld(kind, entity, prop), "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if active is not None:
        p["active"] = active
    return p


def visual(name, x, y, w, h, z, vtype, query=None, sort=None, objects=None):
    v = {"visualType": vtype, "drillFilterOtherVisuals": True}
    if query:
        v["query"] = {"queryState": query}
        if sort:
            v["query"]["sortDefinition"] = sort
    if objects:
        v["objects"] = objects
    return {"$schema": VC, "name": name,
            "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}, "visual": v}


def card(name, x, y, w, h, z, entity, m):
    return visual(name, x, y, w, h, z, "card", query={"Values": {"projections": [proj("Measure", entity, m)]}})


def textbox(name, x, y, w, h, z, text):
    paras = [{"textRuns": [{"value": text, "textStyle": {"fontSize": "16pt"}}]}]
    return visual(name, x, y, w, h, z, "textbox", objects={"general": [{"properties": {"paragraphs": paras}}]})


def page1() -> list:
    """The kind of first draft everyone has made: default everything, slightly uneven."""
    V = [textbox("a1000000000000000001", 12, 6, 300, 44, 1000, "Sales Report")]
    for i, (ent, m, x, w) in enumerate([("Sales", "Total Sales", 12, 214), ("Tickets", "Ticket Count", 236, 196),
                                        ("Tickets", "Avg Ticket", 444, 186), ("Sales", "GM %", 642, 205)]):
        V.append(card(f"a20000000000000000{i + 1:02d}", x, 56, w, 112, 2000 + i, ent, m))
    V.append(visual("a3000000000000000001", 870, 52, 196, 138, 2100, "slicer",
                    query={"Values": {"projections": [proj("Column", "Stores", "City", active=True)]}}))
    V.append(visual("a4000000000000000001", 12, 180, 640, 262, 3000, "lineChart",
                    query={"Category": {"projections": [proj("Column", "Date", "Month", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Total Sales")]}},
                    sort={"sort": [{"field": fld("Column", "Date", "Month"), "direction": "Ascending"}],
                          "isDefaultSort": True}))
    V.append(visual("a4000000000000000002", 668, 204, 600, 238, 3001, "clusteredColumnChart",
                    query={"Category": {"projections": [proj("Column", "Stores", "Store Name", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Total Sales")]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Total Sales"), "direction": "Descending"}]}))
    V.append(visual("a4000000000000000003", 12, 456, 400, 252, 3002, "pieChart",
                    query={"Category": {"projections": [proj("Column", "Channels", "Channel", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Total Sales")]}}))
    V.append(visual("a4000000000000000004", 426, 456, 842, 252, 3003, "tableEx",
                    query={"Values": {"projections": [proj("Column", "Products", "Product"),
                                                      proj("Column", "Products", "Category"),
                                                      proj("Measure", "Sales", "Units"),
                                                      proj("Measure", "Sales", "Total Sales"),
                                                      proj("Measure", "Sales", "GM"),
                                                      proj("Measure", "Sales", "GM %")]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Total Sales"), "direction": "Descending"}]}))
    return V


def page2() -> list:
    V = [textbox("b1000000000000000001", 12, 6, 300, 44, 1000, "Stores")]
    V.append(visual("b2000000000000000001", 12, 56, 760, 330, 2000, "pivotTable",
                    query={"Rows": {"projections": [proj("Column", "Stores", "Store Name", active=True)]},
                           "Columns": {"projections": [proj("Column", "Date", "Year", active=True)]},
                           "Values": {"projections": [proj("Measure", "Sales", "Total Sales")]}}))
    V.append(visual("b2000000000000000002", 790, 56, 478, 330, 2001, "clusteredBarChart",
                    query={"Category": {"projections": [proj("Column", "Stores", "Store Name", active=True)]},
                           "Y": {"projections": [proj("Measure", "Tickets", "Avg Ticket")]}},
                    sort={"sort": [{"field": fld("Measure", "Tickets", "Avg Ticket"), "direction": "Descending"}]}))
    V.append(visual("b2000000000000000003", 12, 400, 1256, 308, 2002, "lineChart",
                    query={"Category": {"projections": [proj("Column", "Date", "Month", active=True)]},
                           "Y": {"projections": [proj("Measure", "Tickets", "Ticket Count")]},
                           "Series": {"projections": [proj("Column", "Channels", "Channel", active=True)]}},
                    sort={"sort": [{"field": fld("Column", "Date", "Month"), "direction": "Ascending"}],
                          "isDefaultSort": True}))
    return V


def page_json(pid, display):
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": pid, "displayName": display, "displayOption": "FitToPage", "height": 720, "width": 1280}


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
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [
            {"name": "CY26SU05", "path": "BaseThemes/CY26SU05.json", "type": "BaseTheme"}]}],
        "settings": {"useEnhancedTooltips": True}})
    write_json(d / "pages" / "pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [P1, P2], "activePageName": P1})
    for pid, display, visuals in ((P1, "Page 1", page1()), (P2, "Page 2", page2())):
        write_json(d / "pages" / pid / "page.json", page_json(pid, display))
        for v in visuals:
            write_json(d / "pages" / pid / "visuals" / v["name"] / "visual.json", v)


# ---------------------------------------------------------------- helpers
def platform(kind):
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": kind, "displayName": NAME},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid5(uuid.NAMESPACE_URL, "datavideos03/" + kind))}}


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main(out: Path, data_dir: Path):
    stats = build_data(data_dir)
    for item in (f"{NAME}.pbip", f"{NAME}.Report", f"{NAME}.SemanticModel"):
        p = out / item
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / f"{NAME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})
    build_model(out, data_dir)
    build_report(out)
    print(json.dumps(stats))


def _arg(flag):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else None


if __name__ == "__main__":
    DATA_URL = _arg("--data-url")
    out_dir = Path(_arg("--out") or WORK / "pbip")
    data = Path(_arg("--data-dir") or DATA)
    main(out_dir, data)
