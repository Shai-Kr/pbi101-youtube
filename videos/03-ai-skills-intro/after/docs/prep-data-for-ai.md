# BeanThere_Sales: Prep data for AI drafts

These are drafts for the parts of AI readiness that Power BI keeps in its own
**Prep data for AI** experience (Home > Prep data for AI in Desktop or the
service). Review them, adjust the wording to your business language, and paste
them in there. The model metadata (descriptions, hidden columns, display
folders, hierarchies, date table, Q&A on) is already in the TMDL files.

Items marked **[confirm]** are interpretations, not facts from the data.
Items marked **[pending]** wait for the business rules you said you'll provide.

## 1. AI instructions (paste into "Add AI instructions")

```text
BeanThere Coffee Co. sales model: 8 stores in 4 Canadian cities, daily data from July 2024 to October 2026.

Metric routing
- "Sales" or "revenue" = [Total Sales].
- GM means gross margin, never General Manager. Gross margin or gross profit in dollars = [GM]; margin %, margin rate or profitability = [GM %].
- "Cost" or "COGS" = [Total COGS].
- Transactions, tickets, traffic or customer count = [Ticket Count]. Average ticket, average order value or spend per visit = [Avg Ticket].
- Units, items sold or quantity = [Units]. Units count items, not transactions; do not mix them with [Ticket Count].

Grain rules
- The Tickets table has no product detail. Never break [Ticket Count] or [Avg Ticket] down by Products[Product] or Products[Category]; for product questions use [Total Sales], [Units], [GM] and [GM %].
- [GM %] and [Avg Ticket] are ratios: never sum or average them across rows, always evaluate the measure at the requested level.

Time
- Use the Date table for all time questions. 2024 (Jul-Dec) and 2026 (Jan-Oct) are partial years: when comparing years, compare the same months and say which months were compared.
- [pending] Fiscal year definition: add here once confirmed.

Stores
- Beltline opened in September 2025 and Union Station in March 2026, so their totals cover fewer months. When ranking stores on totals, mention this; for fair comparisons prefer [Avg Ticket] or monthly averages.
- "Location", "cafe" or "shop" = Stores[Store Name]; regional questions use Stores[City] or Stores[Province] (ON, QC, BC, AB).

Channels
- Channels[Channel] is In-store, Mobile Order or Delivery.
- [confirm] "Digital" orders = Mobile Order + Delivery.
```

## 2. Synonyms (AI data schema / Q&A setup > Synonyms)

| Object | Suggested synonyms |
|---|---|
| Sales[Total Sales] | sales, revenue, net sales, sales dollars, turnover |
| Sales[Total COGS] | COGS, cost of goods sold, cost of sales, product cost |
| Sales[GM] | gross margin, gross profit, margin dollars, margin $ |
| Sales[GM %] | gross margin %, margin %, margin rate, GM percent, profit margin |
| Sales[Units] | units sold, items sold, quantity, qty, volume |
| Tickets[Ticket Count] | tickets, transactions, receipts, orders, traffic, customer count |
| Tickets[Avg Ticket] | average ticket, average transaction value, average order value, AOV, average spend |
| Stores[Store Name] | store, location, cafe, café, shop, branch |
| Stores[City] | city, market |
| Stores[Province] | province, region |
| Products[Product] | product, item, menu item, drink |
| Products[Category] | category, product category, menu category, product line |
| Products[List Price] | menu price, list price |
| Channels[Channel] | channel, order channel, order type, sales channel |
| Date[Month] | month, period |
| Date[Weekday] | day of week, weekday |

## 3. AI data schema

No changes recommended. Every key, foreign-key and raw amount column is now
hidden in the model, so the default schema already exposes only the 7 measures
and 13 business-facing columns.

## 4. Verified answers (top 5)

Mark these report visuals as verified answers, each with 3 to 5 trigger phrasings:

| Question | Visual (page) |
|---|---|
| What are total sales, tickets, average ticket and margin? | KPI cards (Sales Performance) |
| How are sales trending month to month? | Monthly Sales Trend (Sales Performance) |
| Which stores sell the most? | Sales by Store (Sales Performance) |
| How do sales split across channels? | Channel Mix (Sales Performance) |
| Which products sell best and at what margin? | Product Performance (Sales Performance) |

## 5. Test prompts after publishing

- "What was our gross margin % by category in 2025?"
- "Which store had the highest average ticket last quarter?" (should not split by product)
- "Compare Mobile Order and Delivery tickets for Jan–Oct 2026 vs 2025."
- "What's the GM for Latte?" (should return gross margin, not a person)
- "Show monthly sales for Toronto stores."
