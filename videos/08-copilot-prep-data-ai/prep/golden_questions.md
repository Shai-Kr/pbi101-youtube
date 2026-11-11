# Golden questions: real answers before and after

All Copilot answers below are real (Power BI service, report Copilot pane, Nov 10, 2026). The true numbers come from
the CSVs (`truth` in the DAX below).

| Question | Before (no prep) | After (schema + AI instructions) |
|---|---|---|
| How are we doing this year compared to last year? | Fabric IQ off: "revenue more than doubled, ~143% growth" ($19,506,990 for all 22 months vs $8,028,836; filter "Year is not blank"). Fabric IQ on: Jan-Oct 2026 vs Jan-Oct 2025, $9.56M, +19.1% (calendar year). | Feb 1 - Oct 31, 2026: $8,898,525 vs $7,492,807, +18.8% (both modes) |
| What was our revenue last quarter? | $3,319,375 (July - September, calendar Q3) | Fiscal Q3 FY2026 (Aug 1 - Oct 31): $2,876,098 |
| How is this fiscal year going so far? | - | Verified answer (Fabric IQ off): the Finance view table, total $8,898,525 |
| Are we ahead of last year? (not a trigger phrase) | - | Matched the same verified answer |

Aurora's fiscal year starts on **February 1**. The model has no fiscal columns on purpose: the rule lives in the AI
instructions.

## Check the numbers yourself (DAX query view)
```
// fiscal 2026 to date vs the same dates last year
EVALUATE
CALCULATETABLE (
    ROW ( "Revenue", [Revenue], "Revenue PY", [Revenue PY], "YoY %", [Revenue YoY %] ),
    DATESBETWEEN ( 'Date'[Date], DATE ( 2026, 2, 1 ), DATE ( 2026, 10, 31 ) )
)

// last complete fiscal quarter (Aug - Oct 2026) vs the calendar quarter (Jul - Sep 2026)
EVALUATE
ROW (
    "Fiscal Q3", CALCULATE ( [Revenue], DATESBETWEEN ( 'Date'[Date], DATE ( 2026, 8, 1 ), DATE ( 2026, 10, 31 ) ) ),
    "Calendar Q3", CALCULATE ( [Revenue], DATESBETWEEN ( 'Date'[Date], DATE ( 2026, 7, 1 ), DATE ( 2026, 9, 30 ) ) )
)
```
Keep this list, and ask it again after every change to the model or the instructions.
