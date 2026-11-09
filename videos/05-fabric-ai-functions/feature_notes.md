# Feature notes: AI functions in Fabric Data Warehouse (T-SQL)

Tested 2026-11-08 on a Fabric F8 capacity (Canada East), in a new warehouse with the Toastly demo data
(16 products, 260 reviews in 5 languages, 110 support emails). Every result in the video is a real run; nothing is mocked.

## Requirements (what it took to make the first call work)
| What | Notes |
|---|---|
| Paid Fabric capacity | F2 or bigger, or P. Not a trial capacity (Microsoft Learn). |
| Tenant setting "Users can use Copilot and other features powered by Azure OpenAI" | Was already on. |
| Tenant setting "Data sent to Azure OpenAI can be processed outside your capacity's geographic region, compliance boundary, or national cloud instance" | **Needed for a Canada capacity** (Azure OpenAI for Fabric runs in the US / EU Data Boundary). Without it every call failed with `403002 Cross-geo use of Azure OpenAI is disabled for this tenant`. After the admin turned it on, calls kept failing for a few minutes and then worked; for about 10 more minutes some calls still failed (retry fixed it). |
| Preview | All seven functions are preview. They work in the Warehouse and on the Lakehouse SQL analytics endpoint. |
| Model | GPT-5 mini (low reasoning) on Fabric's built-in endpoint, per the AI functions overview on Microsoft Learn. |

## Functions and syntax
`AI_ANALYZE_SENTIMENT(text)` positive / negative / mixed / neutral · `AI_CLASSIFY(text, 'label1', 'label2', ...)` ·
`AI_EXTRACT(text, 'field1', 'field2', ...)` returns JSON · `AI_SUMMARIZE(text)` · `AI_TRANSLATE(text, 'en')`
(de, en, fr, it, es, el, pl, sv, fi, cs) · `AI_FIX_GRAMMAR(text)` · `AI_GENERATE_RESPONSE(prompt [, data])`.
Every function takes `NULL ON ERROR` (default) / `ERROR ON ERROR` / `DEFAULT <value> ON ERROR`.

## What I measured (status bar of the Fabric query editor)
| Query | Rows sent to the AI | Time |
|---|---|---|
| Sentiment, TOP 20 reviews | 260 (TOP came after the AI) | 12.4 s |
| 5 stars AND negative (all reviews) | 260 | 7.8 s |
| Classify 110 emails + GROUP BY | 110 | 5.9 s |
| Extract 4 fields, TOP 10 + OPENJSON | 110 (TOP came after the AI) | 11.7 s |
| Money at risk (classify + extract, 110 emails) | 110 + 110 | 16.1 s |
| Translate TOP 10 foreign reviews (simple WHERE) | 10 | 3.4 s |
| Sentiment by country (all reviews) | 260 | 13.1 s |
| Cheat sheet: STRING_AGG per product + 1 call each | 16 | 9.1 s |
| Live sentiment + topic over the table | 260 + 260 | 24.5 s |
| CTAS into ai.review_enriched | 260 + 260 | 24.3 s |
| SELECT from ai.review_enriched | 0 | 1.5 s |
| Incremental, `WHERE review_id > @last` (3 new rows) | 3 + 3 | 4.7 s |

Rows sent come from `queryinsights.external_api_call_stats.rows_total`, joined to `queryinsights.exec_requests_history`
on `distributed_statement_id`. Query Insights lags a few minutes behind.

## Findings worth knowing (all reproduced, in the video)
1. **Stars vs words works, across languages.** 8-9 of the hand-written sarcastic or misclicked 5-star reviews came back
   negative, including the German and French ones. The exact set varied by one review between runs.
2. **The field name is part of the prompt.** `AI_EXTRACT(..., 'refund_amount')` returned "45 dollars", "119 bucks",
   "$99.00 + $39.99". `'refund_amount_as_decimal_number'` returned 45, 329.00, 119, so `TRY_CAST` + `SUM` worked.
3. **Extraction makes mistakes.** In the take, row 1 had its order number put into the `product` field.
4. **An AI column referenced three times is called three times.** `CROSS APPLY (SELECT AI_GENERATE_RESPONSE(...) AS answer)`
   then `answer`, `JSON_VALUE(answer, '$.issue')`, `JSON_VALUE(answer, '$.urgent')`: 8 emails sent 24 rows, and email 1
   showed `"issue":"refund"` in `answer` but `defect` in the parsed column. Fix: `SELECT ... INTO #answers` first.
5. **`WHERE NOT EXISTS` (or `LEFT JOIN ... IS NULL`) does not stop the AI.** The incremental insert sent all 263 rows
   to the AI for 3 new ones; with zero new rows it still sent 260. The AI runs before the anti-join. A plain predicate
   on the same table is pushed down (`WHERE body LIKE '%refund%'` sent 34 rows; `WHERE review_id > @last` sent 3).
   `CASE WHEN language = 'en' THEN text ELSE AI_TRANSLATE(...) END` also translated all 260 rows.
6. **TOP is not a sample when there's a join or CROSS APPLY.** `TOP 15` over `CROSS APPLY OPENJSON(AI_EXTRACT(...))`
   sent all 110 emails. A simple `SELECT TOP 8 ... AI_GENERATE_RESPONSE(...)` sent 8.
7. **Vague prompts wander.** "What is this email about?" gave JSON once, bullet lists, summaries and suggested replies,
   and repeated phone numbers. The spec prompt (task, allowed issues, urgent rule, JSON only, context) gave the same
   JSON shape for every row.
8. **Speed** was about 20-40 rows per second per function in these runs (260 rows of sentiment in 10-13 s).

## Not used in the video
`AI_SUMMARIZE` and `AI_FIX_GRAMMAR` work (shown on the map), but `AI_GENERATE_RESPONSE` with a format did the
cheat-sheet job better, and grammar fixing had no strong demo in this data.
