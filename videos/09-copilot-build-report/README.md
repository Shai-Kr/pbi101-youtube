# 09 · Copilot builds a Power BI report from a prompt (and one trap)

Video: https://youtu.be/6HiZLJL3kQI

A report built with Copilot in the Power BI service (Microsoft Fabric), from an existing semantic model: two pages,
edited with prompts, a dark theme, saved to the workspace. Plus the part that went wrong: a "fiscal year to date" page
whose cards showed all 22 months, and how to check and fix it.

## What's here
| File | What it is |
|---|---|
| `Aurora Sales Dashboard.pbip` | The report Copilot built on camera, exactly as Fabric saved it (PBIR), plus the Aurora Sales model (TMDL). Opens in Power BI Desktop; the CSVs load from this repo. |
| `prompts.md` | Every prompt from the video and the template that gives a clean page. |
| `checklist.md` | The date check, the page-filter fix and the true numbers (with a DAX check). |

## What has to be turned on (one-time admin work)
- A paid Fabric capacity (F2 or bigger) or Power BI Premium (P1+). A trial capacity doesn't count.
- Tenant setting: "Users can use Copilot, AI Agents and other AI experiences powered by Azure OpenAI".
- Capacity outside the US and EU: "Data sent to Azure OpenAI can be processed outside your capacity's geographic
  region, compliance boundary, or national cloud instance".
- Q&A turned on for the semantic model. No page creation on live connections to Analysis Services, real-time streaming
  models, or models with implicit measures turned off.

## Minimum permissions for the person who builds
From Microsoft Learn (the demo tenant has one user, so this part was not tested with a second account):
- **Build** permission on the semantic model (model, More options, Manage permissions, Add user, only the Build box).
- **Contributor** in one workspace on a Fabric capacity, to save the report there.
- A Power BI **Pro** (or Premium Per User) license.

They can't change the model, and row-level security still applies to them.

## The steps
1. Workspace, the semantic model, More options (...), **Create report**.
2. **Copilot** in the ribbon. "Suggest content for a new report page" gives an outline of page ideas.
3. Type a prompt that fits Copilot's page template: a page name, 2 KPI cards, 4 visuals, 2 slicers (`prompts.md`).
4. Change visuals with prompts (a second line, another chart type).
5. View, **Theme** for the look. Copilot doesn't do themes, colors or layout.
6. **Save**, pick the workspace and folder, name it. It is a regular report on the same semantic model.

## What worked, what didn't
| | |
|---|---|
| ✔ A full page from one prompt | 17 s and 15 s on camera |
| ✔ Changing a visual that's already on the page | a second line (Revenue PY), a donut chart |
| ✔ Saving | a normal report item, reopens in reading view; Edit brings Copilot back |
| ✖ Themes, colors, layout | "isn't supported"; View, Theme is two clicks |
| ✖ Adding visuals later | they landed on top of the others in my tests; drag them into place |
| ✖ Dates | titles said FYTD, the cards showed all time, Copilot said it had fixed them and hadn't (`checklist.md`) |

## Open it yourself
Open `Aurora Sales Dashboard.pbip` in Power BI Desktop (PBIP is on by default in current builds), click Refresh once.
The model reads three small CSV files from this repo (synthetic data, Aurora Outdoor, a made-up company).

The earlier video where this model got its AI instructions: Make Power BI Copilot Answer Right: Prep Data for AI
https://youtu.be/Ybn1boUXbt4 (folder `08-copilot-prep-data-ai`).
