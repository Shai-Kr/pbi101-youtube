# Golden questions (known answers, Aurora Sales demo data)

Ask them again after every change to the agent, the model or the instructions. If an answer moves, find out why
before your users do.

| # | Question | Known answer |
|---|---|---|
| 1 | Which region had the highest revenue in October 2026? | North America, $384,656 |
| 2 | How are we doing this year compared to last year? | With the instructions: fiscal year to date (Feb 1 - Oct 31) $8,898,525 vs $7,492,807, +18.8%; orders 4,199 vs 3,535 (+18.8%); units 56,457 vs 48,124 (+17.3%); Margin % 45.1% vs 45.4% |
| 3 | What's our margin this fiscal year? | 45.1% (Margin %, Feb 1 - Oct 31, 2026) |

Calendar-year check (no fiscal rule): Jan - Oct 2026 $9,561,827 vs Jan - Oct 2025 $8,028,836, +19.1%.
Full year 2025 is $9,945,163: comparing it with ten months of 2026 is the mistake the instructions prevent.

DAX to verify #1 in DAX query view:
```
EVALUATE
CALCULATETABLE (
    SUMMARIZECOLUMNS ( Regions[Region], "Revenue", [Revenue] ),
    'Date'[Year] = 2026, 'Date'[Month Number] = 10
)
ORDER BY [Revenue] DESC
```
