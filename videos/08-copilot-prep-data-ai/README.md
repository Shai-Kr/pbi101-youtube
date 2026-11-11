# Make Power BI Copilot answer right: Prep data for AI

YouTube link: coming soon

Copilot in the Power BI service told me revenue grew **143%** this year. The real number was **18.8%**. Nothing was
wrong with the model: Copilot just didn't know our fiscal year starts in February, or what "this year" means. Prep
data for AI fixed it in three steps: a simpler **AI data schema**, **AI instructions**, and a **verified answer**.

## Requirements
1. A paid Fabric capacity (F2 or bigger) or Power BI Premium (P1+). Trial capacities don't work.
2. Tenant setting **"Users can use Copilot and other features powered by Azure OpenAI"**. Capacity outside the US / EU?
   Also the cross-geo setting for Azure OpenAI.
3. **Q&A** turned on for the semantic model (otherwise the Prep data for AI tabs are disabled).
4. Edit rights on the semantic model (to set it up). Viewers just ask.
5. Prep data for AI is in **preview**. Copilot data questions run in the **Power BI service** (the docs say Desktop
   support is coming), so the video works there.

## Setup
1. Open `Aurora Sales Overview.pbip` in Power BI Desktop, sign in to the web source anonymously, Refresh, and publish
   to a workspace on that capacity. The model reads the CSVs from GitHub raw (`DataRoot` parameter).
2. **Before**: open the report in the service > Copilot (top right) > ask the questions in `prep/golden_questions.md`.
3. Open the semantic model > **Editing** > **Prep data for AI**:
   - **Simplify the data schema**: see `prep/simplify_schema.md`. Apply.
   - **Add AI instructions**: paste `prep/ai_instructions.md`. Apply.
   (This repo's model already carries the instructions in `cultures/en-US.tmdl`, `CustomInstructions`. Remove that
   line first if you want to see the "before" answers yourself.)
4. Wait a few minutes, open a new Copilot pane and ask again.
5. **Verified answer**: report > Editing > page *Finance view* > right-click the table > **Set up a verified answer** >
   add the phrases in `prep/verified_answer.md` > Apply. Ask "How is this fiscal year going so far?" with Fabric IQ off.

## The AI instructions used in the video
```
## Business context
Aurora Outdoor sells outdoor gear in four regions. All amounts are in US dollars.

## Fiscal year
- Our fiscal year starts on February 1. Fiscal 2026 runs from February 1, 2026 to January 31, 2027.
- Fiscal quarters: Q1 is February to April, Q2 is May to July, Q3 is August to October, Q4 is November to January.
- "This year" means this fiscal year to date, up to the last date that has sales.
- "Last quarter" means the last complete fiscal quarter.

## Comparing periods
- When you compare with last year, use the same dates one year earlier. Never compare a full year with a partial year.

## Terms
- "Sales" or "revenue" means the Revenue measure.
- "Margin" means the Margin % measure, unless the user asks for dollars.

## Answers
- Always say which dates you used.
```

## What's inside
| Path | What |
|---|---|
| `Aurora Sales Overview.pbip`, `Aurora Sales.SemanticModel/`, `Aurora Sales Overview.Report/` | The model as TMDL (descriptions everywhere, 9 measures, a Date table, the AI instructions in `cultures/en-US.tmdl`) + the report: *Sales overview* and *Finance view* (the verified-answer table, filtered to fiscal 2026). |
| `prep/ai_instructions.md` | The AI instructions (792 characters; the limit is 10,000). |
| `prep/simplify_schema.md` | What I unticked in the AI data schema, and why. |
| `prep/verified_answer.md` | The visual, its filter, the trigger phrases, the limits. |
| `prep/golden_questions.md` | The questions, Copilot's real answers before and after, the true numbers + DAX checks. |

## What I learned
- Copilot reads names and descriptions. Business rules (fiscal year, "this year", which number is official) aren't in
  any model: put them in the **AI instructions**.
- Open **How Copilot arrived at this**: the 143% answer had one filter, "Year is not blank".
- **Fabric IQ** (the reasoning mode) did better before the prep (+19.1%, calendar year) and followed the instructions
  after it, but it doesn't return **verified answers** (yet). Turn it off to get them.
- Changes took about two minutes to reach Copilot. An unchanged model can repeat a cached answer for up to a day.
- When you're happy, mark the model **Approved for Copilot** (semantic model settings).
- Instructions guide Copilot; they don't guarantee it. Keep the golden questions and keep checking.

## Related
Build a Fabric Data Agent in 5 Minutes (the same fiscal-year problem, solved with agent instructions): https://youtu.be/KOMo49vQUAc
Microsoft Learn: https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai

Channel: https://www.youtube.com/@pbi101  |  https://pbi101.com
