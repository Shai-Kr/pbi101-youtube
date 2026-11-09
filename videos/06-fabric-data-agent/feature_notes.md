# Feature notes: Fabric data agent on a Power BI semantic model

Docs read 2026-11-09 (Microsoft Learn, links at the end). The "Tested" section is filled in during the capacity window;
anything that doesn't work there is dropped from the video, never faked.

## Requirements (docs)
| What | Notes |
|---|---|
| Paid Fabric capacity | F2 or higher, or P1+ with Fabric enabled. **Trial capacities are not supported** (feature/SKU table). |
| Tenant: "Users can use Copilot and other features powered by Azure OpenAI" | On by default. Already ON here. |
| Tenant: "Capacities can be designated as Fabric Copilot capacities" | Listed as required, on by default. |
| Tenant: cross-geo **processing** + **storing** for Azure OpenAI | Needed when the capacity is outside the US / EU data boundary (ours is Canada East). Both ON here since video 05. "Stored" keeps chat history up to 28 days. |
| No separate "data agent" tenant switch | None in the docs (matches the admin API list). |
| XMLA | DAX runs through the XMLA endpoint; not listed as a requirement, but ON here (`OnPremAnalyzeInExcel`). |
| Permission on the model | **Read** is enough to add it to an agent and to query it (create page). Write only to change the model / use Prep data for AI. The sharing page says "Build/Write" (docs disagree; the video says "at least Read, Build is safest"). RLS/CLS apply to whoever asks. |
| Status | The data agent is GA; Git source control, Purview audit, the Python SDK and Foundry via Fabric IQ are still preview. |

## Semantic model as a source (docs)
- Up to **5 sources per agent**, any mix: lakehouse, warehouse, SQL database, mirrored DB, KQL, semantic model, ontology, graph, AI Search (preview).
- Semantic model options: table selection **yes**; agent instructions **yes (routing/format)**; **data source instructions NO**,
  **example queries NO** ("use Verified Answers in Prep for AI"), data source description no.
- **The DAX tool uses only the model's metadata + Prep data for AI** (AI data schema, AI instructions, verified answers,
  synonyms, descriptions, report visual metadata) and, per the semantic-model best-practices page, **ignores instructions
  added at the agent level**. Another page (create) says agent instructions help it write "SQL, DAX or KQL". → **Test which is true.**
- Answers are capped at 25 rows x 25 columns (standard runtime). English only. Read-only (it writes DAX and runs it).
- Select the same tables in the agent as in the model's AI data schema.

## Agent instructions (docs)
- Button "Data agent instructions", up to 15,000 characters. Suggested sections: Objective, Data sources, Key terminology,
  Response guidelines, Handling common topics. Saved in Git as `aiInstructions` in `stage_config.json`.

## Showing its work (docs)
- Each answer has a steps dropdown ("view all the steps") with the generated query; best practice = review the DAX in every answer.
- Draft vs Published versions can be switched and asked the same questions.

## Publish and channels (docs)
- **Publish** opens a dialog with a description → a read-only published version + a draft you keep editing.
  The description becomes the tool description for MCP / Microsoft 365 Copilot. "Publish to Agent Store" (M365 Copilot) is a tick box.
- Where a **published** agent can be used: Microsoft 365 Copilot / Teams (Agent Store), Copilot Studio (Fabric IQ Data MCP tool),
  Azure AI Foundry (Fabric IQ tool, preview), its own **MCP server** URL (Settings → Model Context Protocol), the Python SDK.
- Sharing: "no extra permission" = query the published version; "view details"; "edit and view details". Sharing never grants data access.

## Git / ALM (docs)
- Git integration and deployment pipelines are supported (source control in preview). Item folder `files/config/`:
  `data_agent.json`, `publish_info.json`, `draft/stage_config.json` (instructions) + one folder per source
  (`semantic-model-<name>/datasource.json`), `published/` (don't edit by hand).

## Identity and audit (docs)
- Service principals: "supported only as part of ALM scenarios" (source control page) vs MCP tokens "user or service principal".
  Copilot Studio "Maker" auth is the documented way to answer under one identity. → the video says: use a dedicated identity /
  service principal where the channel supports it, and test it; never a person's account.
- Capacity Metrics: operation "AI Query" (item kind LlmPlugin), plus the query engine cost of the generated DAX.
- Purview audit (preview): "Copilot Interaction" records, app "Fabric-Data Agent"; needs "Allow Microsoft Purview to secure AI interactions".

## Tested (capacity window 2026-11-09, 09:56-10:49 Toronto, F8 Canada East, standard runtime)
Model: `Aurora Sales` (Import, 4 tables, 9 measures, descriptions everywhere), pushed to `fabric/Semantic Models/` and
synced with `git/updateFromGit`. The web source (raw.githubusercontent.com, one data source thanks to `RelativePath`) was
set to Anonymous with the Power BI datasource PATCH; the service refresh took 10 s.

| What | Result |
|---|---|
| New item > "data agent" | One card; a name dialog; the empty agent loads in ~7 s. |
| Add a data source | Opens the **OneLake catalog**, which lists items from *every* workspace you can reach (other clients' models were visible), so filter by name first; the video blurs the other rows. |
| Table selection | Tick each table. Unticked = the warning "No tables selected yet". The first tick removes the warning and shifts the tree up (take note when automating clicks). Selecting all tables once showed a "Standard runtime supports up to 25 tables" notice (don't show again). |
| What the agent sees | Table and measure descriptions from the model show up in the Explorer and in the Git definition (`datasource.json` keeps each element's description). Hidden columns are not listed. |
| Q1 "Which region had the highest revenue in October 2026?" | **North America $384,656** in 21 s (rehearsal 18 s). Correct to the dollar (checked with executeQueries). The steps panel shows the question the agent sent to the model ("Find the region with the highest total revenue in October 2026...") and, under Show input, readable DAX with comments: `DATESBETWEEN` Oct 1-31, `SUMMARIZECOLUMNS` by region, `TOPN(1 ... DESC)`. |
| Q2 "How are we doing this year compared to last year?" (no instructions) | **Not deterministic.** Rehearsal: revenue 2025 $9,945,163 vs 2026 $9,561,827 with "+19.1%" next to it, orders/units/margin $ "down": 12 months of 2025 vs 10 months of 2026, only the YoY measure was right. On camera an hour later: correct calendar YTD (Jan-Oct both years, +19.1% / orders +18.8%), but without naming the period. |
| Agent instructions (747 characters: objective, fiscal year Feb 1, "this year" = fiscal YTD, same-dates rule, margin = Margin %, answer format) | Same question: "Through the current fiscal year to date (Feb 1-Oct 31)... FY 2026 YTD $8,898,525 vs FY 2025 YTD $7,492,807, +18.8%", in one table, "amounts in US dollars". Correct (matches my own DAX). 25 s. |
| How instructions reach a semantic model | The step text shows the agent **rewrote the question with our rules** ("this fiscal year to date (February 1, 2026 through October 31, 2026) versus the same date range last fiscal year..."). So agent-level instructions do change semantic-model answers through the question the agent sends, even though the best-practices page says the DAX tool itself ignores them. Model logic still belongs in Prep data for AI. |
| Publish | Dialog: description + "Also publish to Microsoft Copilot" switch (left off). Toast "Successfully published data agent". |
| Git | `git/commitToGit` (Selective) wrote `fabric/AI Agents/Aurora Sales Agent.DataAgent/Files/Config/`: `data_agent.json`, `publish_info.json` (description), `draft/` + `published/` each with `stage_config.json` (`aiInstructions`) and `semantic-model-Aurora Sales/datasource.json` (artifactId = the model's logical id, workspaceId zeros = same workspace, every table/column/measure with `is_selected` + description). Item type shows as `LLMPlugin` in git/status, `DataAgent` in the folder name. |
| Clear chat | A confirm dialog the first time per agent ("Don't show this again"). |

Not used in the video: Prep data for AI (verified answers, AI instructions on the model), the preview runtime, the MCP
endpoint screen (shows ids), Share (shows emails).

## Sources
concept-data-agent · data-agent-tenant-settings · how-to-create-data-agent · data-agent-configurations ·
data-agent-add-datasources · semantic-model-best-practices · data-agent-sharing · data-agent-source-control ·
data-agent-runtime · data-agent-mcp-server · fabric-data-agent-sdk · data-agent-microsoft-365-copilot ·
data-agent-microsoft-copilot-studio-tool · data-agent-purview-governance · fundamentals/data-agent-consumption
(all under https://learn.microsoft.com/en-us/fabric/data-science/ unless noted).
