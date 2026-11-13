# The three questions, what ChatGPT said, and the check

One voice chat in ChatGPT, with the Fabric data agent plugin from the earlier video tagged first. The questions were
played in my AI voice; ChatGPT's answers are its own voice, recorded as it happened. It **speaks a short headline** and
**writes a longer answer on screen**. The wait is ChatGPT's own "Worked for" counter.

## 1. How's the year going?
```
Keep your answers short, like I'm driving. Ask the Aurora sales agent: how's this fiscal year going so far, compared to last year?
```
Waited 59 s. Spoken: "So far, stronger than last year. About 19 percent revenue growth through October, margins a touch lower."

| Check (fiscal year to date, Feb 1 - Oct 31) | Model |
|---|---|
| Revenue this year vs last year | $8,898,525 vs $7,492,807 (+18.8%, +$1,405,718) |
| Margin | 45.1% vs 45.4% |

## 2. The best month, and why
```
What was our best month this fiscal year, and what drove it?
```
Waited 53 s. Spoken: "June was the peak, biggest order volume and strong camping sales, especially from North America and Europe."

| Check | Model |
|---|---|
| Best month | June 2026: $1,337,975, 603 orders, average order $2,219 |
| Camping in June | $555,719 |
| North America + Europe in June | $1,007,959 |

A note on "biggest order volume": June had the highest revenue. By number of orders July was slightly ahead
(613 vs 603), so read "volume" as dollars.

## 3. One thing to fix
```
If I could fix only one thing in the business right now, what should it be?
```
Waited 77 s. Spoken: "Focus margins on European camping products, and check pricing, discounts, and shipping. That's the pressure point."

| Check (Europe, Camping, fiscal year to date) | Model |
|---|---|
| Revenue | $1,128,326 (+37.3% vs last year) |
| Margin | 34.9% -> 34.4% |
| What the lost margin is worth | about $5,397 |

The direction is real, and it is small: about $5,397 on more than a million dollars of sales. That's the point
the video makes: you get **an** answer, not **the** answer.

The DAX for every check: `dax/check_numbers.dax`.
