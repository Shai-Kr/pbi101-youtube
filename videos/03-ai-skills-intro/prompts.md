## The prompts (typed exactly like this in the video)
Claude Code CLI 2.1.319 in the VS Code terminal, Opus 5.5 at extra-high effort, **auto** permission mode (the default).

1. **Install the skills** (URL copied from GitHub):
   > Install these skills into this project: https://github.com/microsoft/skills-for-fabric
2. **Redesign the report** (Power BI Desktop has the PBIP open, so the skill previews it there):
   > Redesign this report so it looks like a premium product: a dark espresso theme with coffee accents, a clean grid, strong KPI cards, consistent colors, clear titles, and page navigation. Keep the same data and pages. Preview it in Power BI Desktop and keep polishing until it looks stunning.
3. **Make the model AI-ready**:
   > Now make the semantic model AI-ready: descriptions for every table, column and measure, synonyms, display folders, hide the technical columns, and anything else that helps Copilot and data agents answer questions about it.
4. **The business-context test**: run this in a fresh session (`/clear`) without `CLAUDE.md`, then again with it:
   > Add the KPIs our leadership team checks every Monday: YTD sales, margin, and same-store sales growth. Create the measures with descriptions and put them on the first page.

What came back:

| | Without context | With `CLAUDE.md` |
|---|---|---|
| YTD sales | $7.73M (calendar year, from Jan 1) | $3.57M (fiscal year, from Jul 1) |
| Margin | 72.8% gross margin | 69.3% net margin, after the 20% delivery fee, checked against the 68% target |
| Same-store growth | +12.5% (its own guess at the rule) | +12.6% (the 13-month rule) |
| Names | `YTD GM %` | `Net Margin % YTD` |

Notes from making it:
- Without context, the agent stopped and asked: calendar or fiscal year? Which stores count as same-store? That's exactly what the context file answers once, for every session.
- The redesign took about 30 minutes, most of it the skill's validate, reload, screenshot, fix loop (4 rounds). The AI-ready step took about 25 minutes.
- Power BI Desktop sometimes asks to be reopened after the agent changes the model files: close it without saving, reopen the `.pbip`, refresh.
