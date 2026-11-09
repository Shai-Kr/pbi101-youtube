# The two prompts from the video

Both were sent in a ChatGPT chat with the plugin tagged first (type `@` and pick **Aurora Sales Agent**), model "Instant".

## 1. A plain question
```
Which region had the highest revenue in October 2026?
```
On camera: "Worked for 28s", one call to the Aurora Sales Agent, then **North America $384,656**, a bar chart and a table
(Europe $228,659, Asia Pacific $143,554, Latin America $77,872; North America about 46.1% of October).
All four numbers match the semantic model to the dollar. The first try right after the capacity resumed failed (cold
agent; ChatGPT reported an authorization error); a minute later it worked.

## 2. A one-off HTML report
```
Build me a one-page HTML report for our sales managers: this fiscal year to date vs last year, revenue by region,
the top 5 products, and a short summary. One single file, with KPI cards and a small chart.
```
On camera: "Worked for 2m 48s" (about 100 s of it was the agent call). ChatGPT used **fiscal year to date, Feb 1 - Oct
31**, which it got from the agent's instructions (video 06), not from the prompt. The file is in
`report/aurora_sales_fytd_report.html`:

| In the report | Value | Model |
|---|---|---|
| Revenue FY2026 YTD vs FY2025 YTD | $8.90M vs $7.49M, +18.8% | $8,898,525 vs $7,492,807 |
| Orders | 4,199 vs 3,535, +18.8% | same |
| Units | 56,457 vs 48,124, +17.3% | same |
| Gross margin | 45.1% vs 45.4%, -0.2 pp | 45.15% vs 45.37% |
| Regions | NA $3.75M +15.9% · Europe $2.73M +32.1% · APAC $1.54M +11.5% · LatAm $0.88M +8.4% | same |
| Top 5 products | Summit 2P Tent $1,478,050 ... Alpine Hiking Boots $1,018,602 ($6.12M, 68.8% of revenue) | same |
| Europe margin | "declined to 44.8%" | 45.6% -> 44.8% |

Answers are not deterministic: ask the same prompt and you'll get a different layout. Check the numbers every time.
