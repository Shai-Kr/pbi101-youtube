# Connect ChatGPT to Power BI with a Fabric data agent (MCP)

Materials for the PBI101 video, the follow-up to [Build a Fabric data agent in 5 minutes](https://youtu.be/KOMo49vQUAc)
(folder `06-fabric-data-agent`). A **published** Fabric data agent has its own **MCP endpoint**. Any chat app that speaks
MCP can call it. Here: ChatGPT, with one plain question and one one-off HTML report, both with real numbers from the
Power BI semantic model behind the agent.

## How it works
ChatGPT sends the question to the agent's MCP endpoint -> the data agent writes DAX and runs it on the semantic model ->
the answer goes back to ChatGPT -> ChatGPT answers, or builds something with it (a chart, an HTML file...).
The agent's own instructions (fiscal year, answer format) travel with it into any chat.

## Requirements
1. The **data agent from video 06, published**, on a paid Fabric capacity (F2+, or P1+). Only published agents get an
   MCP endpoint. The same tenant settings as video 06 (Copilot / Azure OpenAI, cross-geo outside the US/EU).
2. A chat app that accepts **custom MCP servers**. In the video: **ChatGPT Business** (Plugins > Add > Add custom MCP
   server). Plans and menus change; check your own ChatGPT settings.
3. One **app registration in Microsoft Entra** (see `entra/`), because the endpoint doesn't support dynamic client
   registration.

## Steps
**Fabric**
1. Open the published agent > **Settings** (gear in the ribbon) > **Model Context Protocol**.
2. Copy the **MCP server URL**. It looks like `https://api.fabric.microsoft.com/v1/mcp/workspaces/<workspace-key>/dataagents/<agent-key>/agent`.
   It contains your workspace and agent keys: treat it like an internal link.
3. The **MCP server tool description** there is the publish description: it's what the chat reads to decide when to call
   the agent.

**Entra (once, by an admin)**: `entra/app_registration.md` or `entra/create_app_registration.ps1`.

**ChatGPT**
1. **Plugins** > **Add** > **Add custom MCP server**.
2. Name + description. **Server URL** = the MCP URL. Authentication: **OAuth** (ChatGPT discovers Microsoft Entra from the
   endpoint by itself).
3. **Advanced OAuth settings**: registration method **User-Defined OAuth Client** (DCR and CIMD show as unavailable);
   copy the **Callback URL** into the app registration; paste the **OAuth client ID**; no secret, token endpoint auth
   method **none**; default scope `https://api.fabric.microsoft.com/.default` (filled in).
4. Single-tenant app? In **Auth URL** and **Token URL** replace `organizations` with your tenant (domain or key).
5. Tick **Server supports PKCE (S256)** (Entra supports it but doesn't advertise it).
6. Tick **I understand and want to continue** > **Create as a plugin** > **Continue** > sign in > **Accept** the four
   permissions (an admin can consent for the organization).
7. New chat > type `@` > pick the plugin > ask. Prompts and results: `prompts.md`.

## What's inside
| Path | What |
|---|---|
| `prompts.md` | The two prompts, what came back, and every number checked against the model. |
| `report/aurora_sales_fytd_report.html` | The one-page HTML report ChatGPT built on camera (unchanged; open it in a browser). |
| `entra/` | The app registration settings + an az CLI script (placeholders only). |
| `security_checklist.md` | The 5 security points from the video. |
| `feature_notes.md` | What the docs say, what the endpoint advertises, what I tested. |

## What I learned
- ChatGPT found the sign-in by itself: the endpoint answers 401 with OAuth protected-resource metadata that points to
  Microsoft Entra and the Fabric scope. What it can't do is register itself, hence the app registration.
- The first call after resuming a paused capacity can be slow enough to fail. Ask again.
- The agent's instructions came along: ChatGPT used fiscal year to date (Feb 1 - Oct 31) without being told.
- Answers aren't deterministic. Check the numbers (`prompts.md` has the known ones).

## Related
- Video 06, building the agent: https://youtu.be/KOMo49vQUAc
- Microsoft Learn, the data agent MCP server: https://learn.microsoft.com/fabric/data-science/data-agent-mcp-server

Channel: https://www.youtube.com/@pbi101
