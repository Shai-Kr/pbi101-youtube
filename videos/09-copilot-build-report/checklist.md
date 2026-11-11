# The date check (and the fix that always works)

Model facts: the data runs from January 1, 2025 to October 31, 2026. The fiscal year starts on February 1
(it is written in the model's AI instructions, see the earlier video's folder `08-copilot-prep-data-ai`).

| What the page showed | Value | What it really is |
|---|---|---|
| Card "FYTD Revenue" | $20M | every sale in the model, all 22 months ($19,506,990) |
| Small multi-row card | $9,561,827 | calendar 2026, January to October |
| The real fiscal year to date (Feb 1 - Oct 31, 2026) | **$8,898,525** | 4,199 orders, margin 45.15% |

## The ten-second check
1. Open the Filters pane.
2. Click the card (or any visual).
3. Look at "Filters on this visual". No date there, and nothing under "Filters on this page"? Then the number is all time.
4. In Copilot's answer, open "Show more": it lists the filters it added to each visual.

## The fix: a page filter you set yourself
1. Open the Data pane and expand the Date table.
2. Drag `Date` into "Filters on this page".
3. Filter type: Advanced filtering. Show items when the value: is on or after `2/1/2026`. Apply filter.
4. The cards now show $9M and 4K (8,898,525 and 4,199).

## My rule
- Copilot picks the visuals. You own the dates.
- Either keep time out of the prompt and add a Year slicer, or set a page filter yourself.
- Before you share a report, compare one number with a source you trust.

## A DAX check for the true number (DAX query view)
```dax
EVALUATE
ROW(
    "Fiscal YTD revenue", CALCULATE([Revenue], 'Date'[Date] >= DATE(2026, 2, 1)),
    "Fiscal YTD orders", CALCULATE([Orders], 'Date'[Date] >= DATE(2026, 2, 1)),
    "All time revenue", [Revenue]
)
```
