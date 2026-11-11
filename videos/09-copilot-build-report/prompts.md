# The prompts from the video

All typed into the Copilot pane of a new report (Power BI service, report in Edit mode), on the Aurora Sales model.

## The template that gives a clean page on the first try
Copilot told me its own limits: a page has **2 slicers, 2 card slots and 4 more visuals**. So:

```
Create a new page called <name>. Two KPI cards: <measure> and <measure>.
Then four visuals: <chart of X by Y>, <chart>, <chart>, and <table or matrix>.
Add slicers for <field> and <field>.
```

## Page 1 (built in 17 seconds)
```
Create a new page called Sales Dashboard. Two KPI cards: Revenue and Margin %. Then four visuals: a line chart of Revenue by Month, a bar chart of Revenue by Region, a bar chart of Revenue by Category, and a table of the top 10 products by Revenue with Margin %. Add slicers for Year and Region.
```

## Two edits
```
In the Revenue by Month chart, add Revenue PY as a second line.
```
```
Change the Revenue by Category chart to a donut chart.
```

## Page 2 (built in 15 seconds)
```
Create a new page called Regional Performance. Two KPI cards: Orders and Avg Order Value. Then four visuals: a bar chart of Revenue by Region, a bar chart of Margin % by Region, a matrix of Revenue by Region and Category, and a line chart of Orders by Month. Add slicers for Year and Category.
```

## What Copilot refused
```
Apply a dark theme to this report.
```
Answer: applying a report theme isn't supported. Do it yourself: View, Theme, pick one (two clicks).

## The date trap (don't copy this one)
```
Create a sales performance page for this fiscal year to date. Add cards for Revenue, Orders, Margin % and Revenue YoY %. Add a line chart of Revenue by month, a bar chart of Revenue by Region, a bar chart of Revenue by Category, and a table of the top 10 products by Revenue with Margin %. Add slicers for Region and Category.
```
Copilot first asked me to choose (more visuals than the template allows); I answered `Option B`.
The page title and the cards said "FYTD", but the two big cards had no date filter at all ($20M = all 22 months) and
the other visuals were filtered to the calendar year (1/1/2026 - 12/31/2026). Then:
```
The cards show all dates. Filter every visual on this page, including the cards, to our fiscal year to date: February 1, 2026 onward.
```
Copilot answered that every visual, the cards included, was now filtered. The cards still showed $20M and 9K.
See `checklist.md` for the fix.
