# AI Skills for Power BI (episode 1): one prompt, a whole new report

Materials for the PBI101 video. Everything here is synthetic demo data: **Bean There Coffee Co.**, a made-up chain of
8 cafes in Canada (Jul 2024 - Oct 2026).

## What's inside
| Path | What |
|---|---|
| `before/` | The plain first-draft report (PBIP). Open `BeanThere_Sales.pbip` in Power BI Desktop, then **Refresh**. The tables read the CSVs from this repo, so no local files are needed (if Desktop asks how to connect to the web source, pick **Anonymous**). |
| `after/` | The same project after the session in the video: the redesign, the AI-ready model and the leadership KPIs. Same data source. |
| `CLAUDE.md` | The 10-line business-context file. Claude Code reads it at the start of every session. |
| `prompts.md` | The exact prompts typed in the video. |
| `ai-ready-model.md` | Every description the agent wrote for the tables, columns and measures. |
| `ai-ready.diff` | The git diff of the "make the model AI-ready" step. |
| `data/` | The CSVs. |
| `build_report.py` | Generates the data and the "before" PBIP (Python, standard library only). |

## Try it yourself
1. Install [VS Code](https://code.visualstudio.com/) and [Claude Code](https://code.claude.com/docs).
2. Install the Power BI CLIs the skills use: `npm install -g @microsoft/powerbi-report-authoring-cli @microsoft/powerbi-desktop-bridge-cli`.
3. Copy `before/` and `data/` into a new folder and run `git init` there, so every change the agent makes is a diff you can review (and undo).
4. Open `before/BeanThere_Sales.pbip` in Power BI Desktop and refresh it. Keep it open: the skills preview the report in this window.
5. Open the folder in VS Code, start `claude` in the terminal, and paste the prompts from `prompts.md` one by one.
6. Add `CLAUDE.md` before the KPI prompt and compare the answer with and without it.

Permission modes: the video uses **auto** mode (Claude works on its own, a safety classifier blocks risky actions).
`bypassPermissions` skips every check: use it only in an isolated, git-tracked sandbox, never near production data or credentials.

## The skills
Microsoft's official **Skills for Fabric**: https://github.com/microsoft/skills-for-fabric
(`powerbi-report-cli`, `semantic-model-authoring` and 24 Fabric skills).

## The #1 tip
**Add business context.** The skills know Power BI. Only you know your business. A short context file plus model
descriptions make every answer sharper: the right fiscal year, the right margin, the right audience.

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


Channel: https://www.youtube.com/@pbi101  |  https://pbi101.com
