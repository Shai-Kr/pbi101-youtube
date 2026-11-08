"""Build the demo dataset (CSV) and the Power BI project (PBIP, PBIR + TMDL) for video 02 (OLS deep dive).

Same data as video 01 (same seed), plus the two "one report, every audience" fixes:
  page 2  Field parameters : 'Metric Picker' field parameter with an Is Sensitive flag (RLS filters it)
  page 3  Role detector    : 'Security Marker' one-row table (RLS FALSE() empties it) -> [Full Access]
  page 4  Margin Details   : hidden finance page, reached from page 3's button

Output: next to this script
  data\\*.csv
  pbip\\SalesPerformance.pbip (+ .Report / .SemanticModel)
Run: C:\\Python315\\python.exe -I build_report.py [--data-url <base url for the CSVs>]
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
NAME = "OLS_Deep_Dive"
HERE = Path(__file__).resolve().parent
BASE_THEME = HERE / "theme" / "CY26SU05.json"
DATA_URL = None  # set by --data-url: the published materials read the CSVs from GitHub instead of a local folder

# ---------------------------------------------------------------- data
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


def poisson(rng: random.Random, lam: float) -> int:
    import math
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


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
    with open(DATA / "sales.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Order ID", "Order Date", "Product ID", "Region ID", "Quantity",
                    "Unit Price", "Unit Cost", "Sales Amount", "Cost Amount"])
        w.writerows(rows)
    with open(DATA / "products.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Product ID", "Product", "Category"])
        w.writerows([p[:3] for p in PRODUCTS])
    with open(DATA / "regions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Region ID", "Region"])
        w.writerows([r[:2] for r in REGIONS])
    with open(DATA / "date.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Month", "Year"])
        d = START
        while d <= END:
            w.writerow([d.isoformat(), d.replace(day=1).isoformat(), d.year])
            d += dt.timedelta(days=1)
    rev = sum(r[7] for r in rows)
    cost = sum(r[8] for r in rows)
    return {"lines": len(rows), "revenue": round(rev), "margin_pct": round(1 - cost / rev, 3)}


# ---------------------------------------------------------------- semantic model (TMDL)
_TAGS = [0]


def tag() -> str:
    _TAGS[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"datavideos02/{_TAGS[0]}"))


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


def m_partition(table: str, file: str, types: list[tuple[str, str]]) -> list[str]:
    tlist = ", ".join('{"%s", %s}' % (c, t) for c, t in types)
    if DATA_URL:
        src = f'Web.Contents("{DATA_URL.rstrip("/")}/{file}")'
    else:
        src = f'File.Contents("{DATA / file}")'
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


def measure(name, expr, fmt=None, folder=None, desc=None):
    out = []
    if desc:
        out.append(f"\t/// {desc}")
    out.append(f"\tmeasure {q(name)} = {expr}")
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    if folder:
        out.append(f"\t\tdisplayFolder: {folder}")
    out += [f"\t\tlineageTag: {tag()}", ""]
    return out


MONEY = '\\$#,0;(\\$#,0);\\$#,0'
PCT = "0.0%;-0.0%;0.0%"
# label, measure, sensitive
METRICS = [("Revenue", "Revenue", False), ("Orders", "Orders", False), ("Avg Order Value", "Avg Order Value", False),
           ("Gross Margin", "Gross Margin", True), ("Margin %", "Margin %", True)]


def build_model(root: Path):
    sm = root / f"{NAME}.SemanticModel"
    d = sm / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    write_json(sm / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    write_json(sm / ".platform", platform("SemanticModel"))
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1600\n\n", encoding="utf-8")
    tables = ["Sales", "Products", "Regions", "Date", "Metric Picker", "Security Marker"]
    (d / "model.tmdl").write_text("\n".join([
        "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures", "\tsourceQueryCulture: en-US", "\tdataAccessOptions",
        "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        'annotation PBI_QueryOrder = ["Sales","Products","Regions","Date"]', "",
        *[f"ref table {q(t)}" for t in tables], ""]), encoding="utf-8")

    sales = ["table Sales", f"\tlineageTag: {tag()}", "",
             *measure("Revenue", "SUM(Sales[Sales Amount])", MONEY),
             *measure("Orders", "DISTINCTCOUNT(Sales[Order ID])", "#,0"),
             *measure("Avg Order Value", "DIVIDE([Revenue], [Orders])", MONEY),
             *measure("Gross Margin", "[Revenue] - SUM(Sales[Cost Amount])", MONEY),
             *measure("Margin %", "DIVIDE([Gross Margin], [Revenue])", PCT),
             *col("Order ID", "int64", fmt="0"),
             *col("Order Date", "dateTime", fmt="Short Date"),
             *col("Product ID", "int64", fmt="0", hidden=True),
             *col("Region ID", "int64", fmt="0", hidden=True),
             *col("Quantity", "int64", fmt="#,0", summarize="sum"),
             *col("Unit Price", "double", fmt=MONEY, summarize="sum"),
             *col("Unit Cost", "double", fmt=MONEY, summarize="sum"),
             *col("Sales Amount", "double", fmt=MONEY, summarize="sum"),
             *col("Cost Amount", "double", fmt=MONEY, summarize="sum"),
             *m_partition("Sales", "sales.csv", [
                 ("Order ID", "Int64.Type"), ("Order Date", "type date"), ("Product ID", "Int64.Type"),
                 ("Region ID", "Int64.Type"), ("Quantity", "Int64.Type"), ("Unit Price", "type number"),
                 ("Unit Cost", "type number"), ("Sales Amount", "type number"), ("Cost Amount", "type number")])]
    products = ["table Products", f"\tlineageTag: {tag()}", "",
                *col("Product ID", "int64", fmt="0", hidden=True, extra=["\t\tisKey"]),
                *col("Product", "string"), *col("Category", "string"),
                *m_partition("Products", "products.csv", [
                    ("Product ID", "Int64.Type"), ("Product", "type text"), ("Category", "type text")])]
    regions = ["table Regions", f"\tlineageTag: {tag()}", "",
               *col("Region ID", "int64", fmt="0", hidden=True, extra=["\t\tisKey"]),
               *col("Region", "string"),
               *m_partition("Regions", "regions.csv", [("Region ID", "Int64.Type"), ("Region", "type text")])]
    date = ["table Date", f"\tlineageTag: {tag()}", "",
            *col("Date", "dateTime", fmt="Short Date", extra=["\t\tisKey"]),
            *col("Month", "dateTime", fmt="mmm yy"),
            *col("Year", "int64", fmt="0"),
            *m_partition("Date", "date.csv", [("Date", "type date"), ("Month", "type date"), ("Year", "Int64.Type")])]

    # Fix 2: field parameter with a 4th column the role can filter on
    tuples = ",\n".join(
        f'\t\t\t\t    ("{lbl}", NAMEOF(\'Sales\'[{m}]), {i}, {"TRUE" if sens else "FALSE"}())'
        for i, (lbl, m, sens) in enumerate(METRICS))
    picker = ["table 'Metric Picker'", f"\tlineageTag: {tag()}", "",
              "\tcolumn Metric", "\t\tdataType: string", f"\t\tlineageTag: {tag()}", "\t\tsummarizeBy: none",
              "\t\tsourceColumn: [Value1]", "\t\tsortByColumn: 'Metric Order'", "",
              "\t\trelatedColumnDetails", "\t\t\tgroupByColumn: 'Metric Fields'", "",
              "\tcolumn 'Metric Fields'", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {tag()}",
              "\t\tsummarizeBy: none", "\t\tsourceColumn: [Value2]", "\t\tsortByColumn: 'Metric Order'", "",
              '\t\textendedProperty ParameterMetadata = {"version":3,"kind":2}', "",
              "\tcolumn 'Metric Order'", "\t\tdataType: int64", "\t\tisHidden", "\t\tformatString: 0",
              f"\t\tlineageTag: {tag()}", "\t\tsummarizeBy: sum", "\t\tsourceColumn: [Value3]", "",
              "\tcolumn 'Is Sensitive'", "\t\tdataType: boolean",
              '\t\tformatString: """TRUE"";""TRUE"";""FALSE"""',
              f"\t\tlineageTag: {tag()}", "\t\tsummarizeBy: none", "\t\tsourceColumn: [Value4]", "",
              "\tpartition 'Metric Picker' = calculated", "\t\tmode: import", "\t\tsource =",
              "\t\t\t\t{", tuples, "\t\t\t\t}", ""]

    # Fix 3: role detector. One row for everyone; the restricted role filters it to zero rows.
    marker = ["table 'Security Marker'", f"\tlineageTag: {tag()}", "",
              *measure("Full Access", "NOT ISEMPTY('Security Marker')",
                       desc="TRUE when this viewer is not in a restricted role (the role empties this table)"),
              *measure("Access Label",
                       'IF([Full Access], "\u2705  Full access: cost and margin included", '
                       '"\U0001F512  Sales view: cost and margin are protected")'),
              *measure("Margin Button Text",
                       'IF([Full Access], "Open margin details  \u2192", "\U0001F512  Margin details: finance only")'),
              *measure("Margin Button Target", 'IF([Full Access], "Margin Details", "")'),
              *measure("Margin Button Color", 'IF([Full Access], "#F59E0B", "#CBD5E1")'),
              "\tcolumn Marker", "\t\tdataType: int64", "\t\tisHidden", "\t\tformatString: 0",
              f"\t\tlineageTag: {tag()}", "\t\tsummarizeBy: none", "\t\tsourceColumn: [Value]", "",
              "\tpartition 'Security Marker' = calculated", "\t\tmode: import", "\t\tsource = { 1 }", ""]

    for t, lines in (("Sales", sales), ("Products", products), ("Regions", regions), ("Date", date),
                     ("Metric Picker", picker), ("Security Marker", marker)):
        (d / "tables" / f"{t}.tmdl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    rel = []
    for name, a, b in (("Sales_Products", "Sales.'Product ID'", "Products.'Product ID'"),
                       ("Sales_Regions", "Sales.'Region ID'", "Regions.'Region ID'"),
                       ("Sales_Date", "Sales.'Order Date'", "Date.Date")):
        rel += [f"relationship {name}", f"\tfromColumn: {a}", f"\ttoColumn: {b}", ""]
    (d / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")


# ---------------------------------------------------------------- report (PBIR)
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
INK, MUTED, GRID, CARD_LINE = "#0F172A", "#64748B", "#EEF1F7", "#E3E8F0"
BLUE, TEAL, AMBER, VIOLET, RED = "#2563EB", "#0EA5A4", "#F59E0B", "#7C3AED", "#DC2626"
P1, P2, P3, P4 = "a1f0c3d2e4b5a6978801", "b2f1e1d2a3c4b5d6e702", "c3a2b1d0e9f8a7b6c503", "d4b3c2a1f0e9d8c7b604"


def lit(v): return {"expr": {"Literal": {"Value": v}}}
def s(t): return lit("'" + t.replace("'", "''") + "'")
def dnum(n): return lit(f"{n}D")
def lnum(n): return lit(f"{n}L")
def b(flag): return lit("true" if flag else "false")
def color(h): return {"solid": {"color": s(h)}}
def props(**kw): return [{"properties": kw}]
def dprops(**kw): return [{"properties": kw, "selector": {"id": "default"}}]
def mexpr(entity, prop): return {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}}


def fld(kind, entity, prop):
    return {kind: {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj(kind, entity, prop, active=None):
    p = {"field": fld(kind, entity, prop), "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if active is not None:
        p["active"] = active
    return p


def container(title: str | None, shadow=True):
    o = {
        "background": props(show=b(True), color=color("#FFFFFF"), transparency=dnum(0)),
        "border": props(show=b(True), color=color(CARD_LINE), radius=dnum(12)),
        "padding": props(top=lnum(10), bottom=lnum(10), left=lnum(14), right=lnum(14)),
        "dropShadow": props(show=b(shadow)),
        "visualHeader": props(show=b(False)),
    }
    o["title"] = props(show=b(bool(title)), text=s(title or ""), fontColor=color(INK), fontSize=dnum(12),
                       bold=b(True), alignment=s("left"))
    return o


def axis_objects(cat_type="Categorical"):
    return {
        "categoryAxis": props(show=b(True), fontSize=dnum(9), labelColor=color(MUTED), showAxisTitle=b(False),
                              axisType=s(cat_type)),
        "valueAxis": props(show=b(True), fontSize=dnum(9), labelColor=color(MUTED), showAxisTitle=b(False),
                           gridlineColor=color(GRID), gridlineShow=b(True), gridlineThickness=dnum(1)),
        "legend": props(show=b(False)),
    }


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


def kpi_card(name, x, y, w, h, z, measure_name, label, accent, units=0, decimals=None, entity="Sales", size=30):
    value = dict(fontSize=dnum(size), bold=b(True), fontColor=color(INK), horizontalAlignment=s("left"),
                 labelDisplayUnits=dnum(units))
    if decimals is not None:
        value["labelPrecision"] = lnum(decimals)
    objects = {
        "value": dprops(**value),
        "label": dprops(show=b(bool(label)), fontSize=dnum(11), fontColor=color(MUTED), horizontalAlignment=s("left"),
                        text=s(label or ""), position=s("aboveValue")),
        "accentBar": dprops(show=b(True), position=s("Left"), color=color(accent), width=dnum(5)),
        "outline": dprops(show=b(False)),
        "fillCustom": dprops(show=b(False)),
        "padding": dprops(paddingUniform=lnum(14)),
    }
    return visual(name, x, y, w, h, z, "cardVisual",
                  query={"Data": {"projections": [proj("Measure", entity, measure_name)]}},
                  objects=objects, vco=container(None))


def textbox(name, x, y, w, h, z, title, subtitle=None, size="22pt"):
    paras = [{"textRuns": [{"value": title, "textStyle": {
        "fontSize": size, "fontWeight": "bold", "color": INK, "fontFamily": "Segoe UI Semibold"}}]}]
    if subtitle:
        paras.append({"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "11pt", "color": MUTED}}]})
    return visual(name, x, y, w, h, z, "textbox", objects={"general": [{"properties": {"paragraphs": paras}}]},
                  vco={"background": props(show=b(False))}, drill=False)


def note_box(name, x, y, w, h, z, heading, lines):
    """'How it works' panel: a textbox on a soft card."""
    paras = [{"textRuns": [{"value": heading, "textStyle": {"fontSize": "12pt", "fontWeight": "bold", "color": INK}}]}]
    for ln in lines:
        runs = []
        for part, code in ln:
            st = {"fontSize": "11pt", "color": INK if not code else "#7C3AED"}
            if code:
                st["fontFamily"] = "Consolas"
            runs.append({"value": part, "textStyle": st})
        paras.append({"textRuns": runs})
    vco = {"background": props(show=b(True), color=color("#FFFFFF"), transparency=dnum(0)),
           "border": props(show=b(True), color=color(CARD_LINE), radius=dnum(12)),
           "padding": props(top=lnum(12), bottom=lnum(12), left=lnum(18), right=lnum(18))}
    return visual(name, x, y, w, h, z, "textbox", objects={"general": [{"properties": {"paragraphs": paras}}]},
                  vco=vco, drill=False)


TBL_OBJ = {
    "columnHeaders": props(fontSize=dnum(10), fontColor=color(MUTED), bold=b(True), backColor=color("#FFFFFF")),
    "values": props(fontSize=dnum(11), fontColor=color(INK), backColorPrimary=color("#FFFFFF"),
                    backColorSecondary=color("#F8FAFC")),
    "total": props(totals=b(True), fontSize=dnum(11), bold=b(True)),
    "grid": props(gridHorizontal=b(True), gridHorizontalColor=color(GRID), gridVertical=b(False), rowPadding=dnum(3)),
}


def param_table(name, x, y, w, h, z, dim_entity, dim_col, title):
    """Table whose metric columns come from the 'Metric Picker' field parameter."""
    projs = [proj("Column", dim_entity, dim_col)] + [proj("Measure", "Sales", m) for _, m, _ in METRICS]
    query = {"Values": {"projections": projs,
                        "fieldParameters": [{"parameterExpr": fld("Column", "Metric Picker", "Metric"),
                                             "index": 1, "length": len(METRICS)}]}}
    return visual(name, x, y, w, h, z, "tableEx", query=query,
                  sort={"sort": [{"field": fld("Column", dim_entity, dim_col), "direction": "Ascending"}]},
                  objects=TBL_OBJ, vco=container(title))


def page_json(pid, display, hidden=False):
    p = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
         "name": pid, "displayName": display, "displayOption": "FitToPage", "height": 720, "width": 1280,
         "objects": {"background": props(color=color("#F3F5F9"), transparency=dnum(0))}}
    if hidden:
        p["visibility"] = "HiddenInViewMode"
    return p


def page1() -> list:
    V = [textbox("b0000000000000000001", 24, 2, 900, 80, 1000, "Sales Performance",
                 "Aurora Outdoor  \u00b7  Jan 2025 \u2013 Oct 2026  \u00b7  all regions")]
    cards = [("Revenue", "Revenue", BLUE, 1000000, 1), ("Orders", "Orders", TEAL, 1, 0),
             ("Gross Margin", "Gross Margin", AMBER, 1000000, 1), ("Margin %", "Margin %", VIOLET, 0, 1)]
    for i, (m, label, accent, units, dec) in enumerate(cards):
        V.append(kpi_card(f"c000000000000000000{i + 1}", 24 + i * 312, 84, 296, 104, 2000 + i, m, label, accent,
                          units, dec))
    line_obj = axis_objects("Categorical")
    line_obj["dataPoint"] = props(defaultColor=color(BLUE))
    line_obj["lineStyles"] = props(strokeWidth=dnum(3))
    line_obj["labels"] = props(show=b(False))
    V.append(visual("d0000000000000000001", 24, 204, 760, 250, 3000, "lineChart",
                    query={"Category": {"projections": [proj("Column", "Date", "Month", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Revenue")]}},
                    sort={"sort": [{"field": fld("Column", "Date", "Month"), "direction": "Ascending"}],
                          "isDefaultSort": True},
                    objects=line_obj, vco=container("Revenue by month")))
    bar_obj = axis_objects()
    bar_obj["dataPoint"] = props(defaultColor=color(TEAL))
    bar_obj["labels"] = props(show=b(True), fontSize=dnum(9), color=color(INK), labelDisplayUnits=dnum(1000000),
                              labelPrecision=lnum(1))
    bar_obj["valueAxis"] = props(show=b(False), gridlineShow=b(False))
    V.append(visual("d0000000000000000002", 800, 204, 456, 250, 3001, "clusteredBarChart",
                    query={"Category": {"projections": [proj("Column", "Regions", "Region", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Revenue")]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Revenue"), "direction": "Descending"}]},
                    objects=bar_obj, vco=container("Revenue by region")))
    V.append(visual("d0000000000000000003", 24, 470, 600, 234, 3002, "tableEx",
                    query={"Values": {"projections": [proj("Column", "Products", "Category"),
                                                      proj("Measure", "Sales", "Revenue"),
                                                      proj("Measure", "Sales", "Gross Margin"),
                                                      proj("Measure", "Sales", "Margin %")]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Revenue"), "direction": "Descending"}]},
                    objects=TBL_OBJ, vco=container("Category performance")))
    col_obj = axis_objects()
    col_obj["dataPoint"] = props(defaultColor=color(AMBER))
    col_obj["labels"] = props(show=b(True), fontSize=dnum(9), color=color(INK), labelDisplayUnits=dnum(1000000),
                              labelPrecision=lnum(1))
    col_obj["valueAxis"] = props(show=b(False), gridlineShow=b(False))
    V.append(visual("d0000000000000000004", 640, 470, 616, 234, 3003, "clusteredColumnChart",
                    query={"Category": {"projections": [proj("Column", "Products", "Category", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Gross Margin")]}},
                    objects=col_obj, vco=container("Gross margin by category")))
    return V


def page2() -> list:
    V = [textbox("e0000000000000000001", 24, 2, 1000, 80, 1000, "Fix 2 \u00b7 Field parameters + RLS",
                 "Same visuals for everyone. The metric list adapts to the viewer's role, so nothing breaks.")]
    slicer_obj = {
        "header": props(show=b(False)),
        "value": dprops(show=b(True), fontSize=dnum(13), bold=b(True), fontColor=color(INK),
                        horizontalAlignment=s("center")),
        "layout": props(rowCount=lnum(1), columnCount=lnum(len(METRICS))),
        "selection": props(singleSelect=b(False)),
    }
    V.append(visual("e0000000000000000002", 24, 88, 1232, 72, 1500, "advancedSlicerVisual",
                    query={"Values": {"projections": [proj("Column", "Metric Picker", "Metric", active=True)]}},
                    objects=slicer_obj, vco=container(None, shadow=False), drill=False))
    V.append(param_table("e0000000000000000003", 24, 176, 600, 300, 3000, "Regions", "Region", "Metrics by region"))
    V.append(param_table("e0000000000000000004", 640, 176, 616, 300, 3001, "Products", "Category",
                         "Metrics by category"))
    V.append(note_box("e0000000000000000005", 24, 492, 1232, 212, 4000, "How it works", [
        [("1.  ", False), ("'Metric Picker'", True), (" is a field parameter. Each metric row has an ", False),
         ("Is Sensitive", True), (" flag.", False)],
        [("2.  The Sales Team role filters it:  ", False), ("'Metric Picker'[Is Sensitive] = FALSE()", True)],
        [("3.  So a restricted viewer never even gets the sensitive metrics to pick. No error, no broken visual.",
          False)],
        [("4.  The RLS filter and the OLS rules live in the same role.", False)],
    ]))
    return V


def page3() -> list:
    V = [textbox("f0000000000000000001", 24, 2, 1000, 80, 1000, "Fix 3 \u00b7 Role detector",
                 "One tiny table tells the report who is looking. The report adapts, nothing breaks.")]
    banner = kpi_card("f0000000000000000002", 24, 88, 1232, 76, 1500, "Access Label", None, TEAL,
                      entity="Security Marker", size=18)
    V.append(banner)
    for i, (m, label, accent, units, dec) in enumerate([("Revenue", "Revenue", BLUE, 1000000, 1),
                                                        ("Orders", "Orders", TEAL, 1, 0),
                                                        ("Avg Order Value", "Avg order value", VIOLET, 1, 0)]):
        V.append(kpi_card(f"f00000000000000000{10 + i}", 24 + i * 312, 180, 296, 104, 2000 + i, m, label, accent,
                          units, dec))
    btn = visual("f0000000000000000020", 960, 180, 296, 104, 2500, "actionButton", drill=True)
    btn["visual"]["objects"] = {
        "text": [{"properties": {"show": b(True)}},
                 {"properties": {"text": mexpr("Security Marker", "Margin Button Text"), "fontSize": dnum(13),
                                 "bold": b(True), "fontColor": color(INK), "horizontalAlignment": s("center")},
                  "selector": {"id": "default"}}],
        "icon": [{"properties": {"show": b(False)}}],
        "fill": [{"properties": {"show": b(True)}},
                 {"properties": {"fillColor": {"solid": {"color": mexpr("Security Marker", "Margin Button Color")}},
                                 "transparency": dnum(0)}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": b(False)}}],
        "shape": [{"properties": {"tileShape": s("rectangleRounded"), "roundEdge": lnum(12)}},
                  {"properties": {"tileShape": s("rectangleRounded")}, "selector": {"id": "default"}}],
    }
    btn["visual"]["visualContainerObjects"] = {
        "background": props(show=b(False)), "border": props(show=b(False)),
        "visualLink": [{"properties": {"show": b(True), "type": s("PageNavigation"),
                                       "navigationSection": mexpr("Security Marker", "Margin Button Target"),
                                       "tooltip": s("Finance only")}}]}
    btn["howCreated"] = "InsertVisualButton"
    V.append(btn)
    line_obj = axis_objects("Categorical")
    line_obj["dataPoint"] = props(defaultColor=color(BLUE))
    line_obj["lineStyles"] = props(strokeWidth=dnum(3))
    line_obj["labels"] = props(show=b(False))
    V.append(visual("f0000000000000000030", 24, 300, 1232, 190, 3000, "lineChart",
                    query={"Category": {"projections": [proj("Column", "Date", "Month", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Revenue")]}},
                    sort={"sort": [{"field": fld("Column", "Date", "Month"), "direction": "Ascending"}],
                          "isDefaultSort": True},
                    objects=line_obj, vco=container("Revenue by month")))
    V.append(note_box("f0000000000000000040", 24, 506, 1232, 198, 4000, "How it works", [
        [("1.  ", False), ("'Security Marker'", True), (" has one row. The Sales Team role filters it with  ", False),
         ("FALSE()", True), ("  so it's empty for them.", False)],
        [("2.  ", False), ("[Full Access] = NOT ISEMPTY('Security Marker')", True),
         ("  never touches a secured column, so it never breaks.", False)],
        [("3.  It drives the banner, the button text, its color and where it navigates.", False)],
        [("4.  Secured visuals live on a hidden finance page that only full-access users reach.", False)],
    ]))
    return V


def page4() -> list:
    V = [textbox("g0000000000000000001", 24, 2, 1000, 80, 1000, "Margin details",
                 "Finance only  \u00b7  hidden page, reached from the role detector")]
    for i, (m, label, accent, units, dec) in enumerate([("Gross Margin", "Gross Margin", AMBER, 1000000, 1),
                                                        ("Margin %", "Margin %", VIOLET, 0, 1)]):
        V.append(kpi_card(f"g00000000000000000{10 + i}", 24 + i * 312, 88, 296, 104, 2000 + i, m, label, accent,
                          units, dec))
    back = visual("g0000000000000000020", 1096, 112, 160, 56, 2500, "actionButton")
    back["visual"]["objects"] = {
        "text": [{"properties": {"show": b(True)}},
                 {"properties": {"text": s("\u2190  Back"), "fontSize": dnum(12), "bold": b(True),
                                 "fontColor": color("#FFFFFF"), "horizontalAlignment": s("center")},
                  "selector": {"id": "default"}}],
        "icon": [{"properties": {"show": b(False)}}],
        "fill": [{"properties": {"show": b(True)}},
                 {"properties": {"fillColor": color(INK), "transparency": dnum(0)}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": b(False)}}],
        "shape": [{"properties": {"tileShape": s("rectangleRounded"), "roundEdge": lnum(10)}},
                  {"properties": {"tileShape": s("rectangleRounded")}, "selector": {"id": "default"}}],
    }
    back["visual"]["visualContainerObjects"] = {
        "background": props(show=b(False)), "border": props(show=b(False)),
        "visualLink": [{"properties": {"show": b(True), "type": s("Back")}}]}
    back["howCreated"] = "InsertVisualButton"
    V.append(back)
    V.append(visual("g0000000000000000030", 24, 208, 600, 300, 3000, "tableEx",
                    query={"Values": {"projections": [proj("Column", "Products", "Category"),
                                                      proj("Measure", "Sales", "Revenue"),
                                                      proj("Measure", "Sales", "Gross Margin"),
                                                      proj("Measure", "Sales", "Margin %")]}},
                    sort={"sort": [{"field": fld("Measure", "Sales", "Revenue"), "direction": "Descending"}]},
                    objects=TBL_OBJ, vco=container("Category performance")))
    col_obj = axis_objects()
    col_obj["dataPoint"] = props(defaultColor=color(AMBER))
    col_obj["labels"] = props(show=b(True), fontSize=dnum(9), color=color(INK), labelDisplayUnits=dnum(1000000),
                              labelPrecision=lnum(1))
    col_obj["valueAxis"] = props(show=b(False), gridlineShow=b(False))
    V.append(visual("g0000000000000000031", 640, 208, 616, 300, 3001, "clusteredColumnChart",
                    query={"Category": {"projections": [proj("Column", "Products", "Category", active=True)]},
                           "Y": {"projections": [proj("Measure", "Sales", "Gross Margin")]}},
                    objects=col_obj, vco=container("Gross margin by category")))
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
        "pageOrder": [P1, P2, P3, P4], "activePageName": P1, "landingPageName": P1})
    for pid, display, hidden, visuals in ((P1, "Sales Overview", False, page1()),
                                          (P2, "Fix 2 \u00b7 Field parameters", False, page2()),
                                          (P3, "Fix 3 \u00b7 Role detector", False, page3()),
                                          (P4, "Margin Details", True, page4())):
        write_json(d / "pages" / pid / "page.json", page_json(pid, display, hidden))
        for v in visuals:
            write_json(d / "pages" / pid / "visuals" / v["name"] / "visual.json", v)


# ---------------------------------------------------------------- helpers
def platform(kind):
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": kind, "displayName": NAME},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid5(uuid.NAMESPACE_URL, "datavideos02/" + kind))}}


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
    print(json.dumps(stats))


if __name__ == "__main__":
    if "--data-url" in sys.argv:
        DATA_URL = sys.argv[sys.argv.index("--data-url") + 1]
    main(Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else PBIP)
