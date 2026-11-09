# Build a Fabric data agent in 5 minutes (then do this before production)

Materials for the PBI101 video. A **Fabric data agent** on a Power BI semantic model: you ask in plain English,
the agent writes DAX against the model, runs it and answers in words. Then the 6 checks before real users get it.
Demo data: **Aurora Outdoor**, a made-up outdoor gear company (12 products, 4 regions, Jan 2025 - Oct 2026), the same
data as the OLS and user-aware-columns videos. The CSVs live in this repo (`videos/02-ols-deep-dive/data`).

## Requirements
1. **A paid Fabric capacity**, F2 or bigger (or P1+). Trial capacities don't support data agents.
2. Tenant setting **"Users can use Copilot and other features powered by Azure OpenAI"**.
3. Capacity **outside the US / EU** (Canada, UK, Asia...)? Also the two cross-geo settings: data sent to Azure OpenAI
   can be **processed** / **stored** outside your capacity's geographic region.
4. Permission to query the semantic model (at least Read). RLS applies to whoever asks.

## Setup
1. **The model.** Open `Aurora Sales.pbip` in Power BI Desktop, sign in to the web source anonymously, Refresh, and
   publish it to a workspace on that capacity. (Or put `Aurora Sales.SemanticModel` in a Git-connected workspace folder
   and *Update from Git*; then set the web credentials to Anonymous and refresh.) The model reads the CSVs from GitHub
   raw (`DataRoot` parameter), so it refreshes anywhere.
2. **The agent.** New item > **Data agent** > name it > **Add a data source** > filter the OneLake catalog by name >
   **Aurora Sales** > Add > tick **Sales, Products, Regions, Date**.
3. Ask the questions in `agent/golden_questions.md`. Open "1 step completed" > the arrow > **Show input** to see the DAX.
4. **Agent instructions**: paste `agent/instructions.md`. Ask question 2 again.
5. **Publish** with the description in `agent/description.txt`.

## The agent instructions used in the video
```
## Objective
You answer sales questions for Aurora Outdoor's regional sales managers.

## Key terminology
- Our fiscal year starts on February 1. Fiscal 2026 runs from February 1, 2026 to January 31, 2027.
- "This year" means the current fiscal year to date. The latest sales date is October 31, 2026.
- Compare a period with the same dates last year. Never compare a part year with a full year.
- "Margin" means Margin % (gross margin percent). Show dollars only when asked.

## Response guidelines
- Start with one sentence that answers the question. Name the period, and say amounts are in US dollars.
- Then a small table if there is more than one number.
- Only answer sales questions. For anything else, say it's outside what you can answer.
```

## What's inside
| Path | What |
|---|---|
| `Aurora Sales.pbip`, `Aurora Sales.SemanticModel/`, `Aurora Sales.Report/` | The model as TMDL (descriptions on every table, column and measure; same-dates YoY measures; a marked date table) + a blank report page so it opens in Desktop. |
| `agent/instructions.md` | The agent instructions. |
| `agent/description.txt` | The publish description (Copilot and other agents read it to decide when to call yours). |
| `agent/golden_questions.md` | Questions with known answers + a DAX check. |
| `agent/git_definition/` | What Fabric Git integration wrote for this agent (ids replaced with placeholders). |
| `checklist/production_checklist.md` | The 6 checks + an access inventory template. |
| `feature_notes.md` | What the docs say and what I tested (including the non-deterministic answer). |

## What I learned
- The model's **descriptions** show up in the agent and steer which measure it picks. Write them.
- Same question, different day, different answer: without context it once compared 12 months with 10. A few lines of
  **instructions** (fiscal year, "same dates", answer format) made it consistent, and the steps show the agent putting
  those rules into the question it sends to the model.
- Always open the steps and look at the DAX.
- The OneLake catalog lists every item you can reach across workspaces: filter by name.

## Related
Fabric AI functions in T-SQL: https://youtu.be/tG6wGB8_YcI
Microsoft Learn: https://learn.microsoft.com/fabric/data-science/concept-data-agent

Channel: https://www.youtube.com/@pbi101  |  https://pbi101.com
