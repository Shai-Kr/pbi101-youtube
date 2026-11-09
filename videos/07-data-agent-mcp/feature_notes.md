# Feature notes: the Fabric data agent as an MCP server, used from ChatGPT

Docs read and tested 2026-11-09 (Toronto). Anything that didn't work in the test is not in the video.

## Fabric side (docs: learn.microsoft.com/fabric/data-science/data-agent-mcp-server, updated 2026-09-04)
- Endpoint: `https://api.fabric.microsoft.com/v1/mcp/workspaces/<workspace-key>/dataagents/<agent-key>/agent`, also on the agent's
  **Settings → Model Context Protocol** tab (with a `mcp.json` download for VS Code).
- Works **only for a published agent**. One tool = the agent; the **publish description becomes the tool description**.
- Auth: every request carries an **Entra ID access token** (Authorization header) for `https://api.fabric.microsoft.com/.default`, user or service
  principal. **No dynamic client registration and no client metadata documents**: "your client must use its own
  authentication flow".
- Documented clients: VS Code + GitHub Copilot agent mode (HTTP server, sign-in prompt) and a Python script (MCP SDK +
  azure-identity). ChatGPT / Claude aren't named; the page says any client that speaks streamable HTTP and can attach a
  Fabric token works.
- Supports long-running MCP tasks. Notice on the page: responses "might be sent outside of Fabric's compliance boundary or
  geographic region" and are handled by the MCP client's own terms.
- Prerequisites: paid F2+/P1+ capacity, cross-geo processing + storing for AI (on since video 05), read access to the
  source, a published agent.

### What the endpoint actually advertises (probed without a token, 2026-11-09)
- A call with no token → **401** with `WWW-Authenticate: Bearer ... resource_metadata=".../.well-known/oauth-protected-resource/v1/mcp/workspaces/<ws>/dataagents/<agent>/agent"`.
- That metadata (RFC 9728): authorization server `https://login.microsoftonline.com/organizations/v2.0`, resource
  `https://api.fabric.microsoft.com`, scope `https://api.fabric.microsoft.com/.default`.
- Entra's metadata has no registration endpoint, no CIMD flag and no `code_challenge_methods_supported` (it does support PKCE).
- So a client can *find* Entra by itself but must bring its own **app registration (client ID)**.

## ChatGPT side (tested in a ChatGPT Business workspace, Chrome, 2026-11-09)
- The place is **Plugins** (sidebar, or `chatgpt.com/plugins`) → **Add ▾ → Add custom MCP server**. No Developer-mode
  toggle was needed on this Business workspace. (OpenAI's docs call these apps / plugins; older posts say "connectors".)
- A chat can't add a server by URL. You add it once in Plugins, then use it in any chat with **@Aurora Sales Agent** in the
  composer, or the plugin page's **Try in chat**.
- Dialog: icon, **Name**, Description, Connection (**Server URL** / Tunnel), Authentication (**OAuth** / No authentication /
  either), **Advanced OAuth settings**, the "Custom MCP servers introduce risk" box with "I understand and want to
  continue", **Create as a plugin**.
- Advanced OAuth settings, after pasting the URL, were **discovered from the server**:
  - Auth URL and Token URL (`login.microsoftonline.com/organizations/...`), Resource `https://api.fabric.microsoft.com`;
  - default scope `https://api.fabric.microsoft.com/.default` (ticked), OIDC on (openid, profile, email, offline_access).
  - Registration method: DCR "unavailable" (no registration URL) and CIMD "unavailable", so **User-Defined OAuth Client**.
  - Fields: **Callback URL** (`https://chatgpt.com/connector/oauth/<code>`, shown with a copy button), **OAuth client ID**,
    client secret (optional), token endpoint auth method (`none` / basic / post / tls).
  - The **PKCE (S256)** box is unticked (Entra doesn't advertise it): tick it.
  - For a **single-tenant** app, change `organizations` to your tenant in Auth URL + Token URL (the tenant domain works).
- After Create: "Connect Aurora Sales Agent - Approved by your admin" (workspace admin) → **Continue** → Microsoft sign-in in
  the same tab: **account picker** (lists every Microsoft account in the browser, including unrelated ones: keep it off camera) → **Permissions requested** (app name, publisher domain, "not published by Microsoft", the 4 permissions,
  "Consent on behalf of your organization" for admins) → **Accept** → back in Plugins, a new **Personal** tab lists it.
- The authorize request: `scope=openid email offline_access https://api.fabric.microsoft.com/.default`, PKCE S256, and
  `resource=https://api.fabric.microsoft.com` (Entra accepted it).
- Plugin page: "By <your name>", Apps 1, Manage, **Try in chat**, and a note that ChatGPT may share relevant chats and memories
  with the app.

## The Entra app registration
- "ChatGPT - data agent demo", single tenant, **public client** (redirects under Mobile and desktop, no secret),
  redirect = the ChatGPT callback URL (+ the stable `https://chatgpt.com/connector_platform_oauth_redirect`).
- Delegated permissions: Power BI Service **DataAgent.Execute.All, DataAgent.Read.All, Dataset.Read.All**, Graph
  **User.Read**. All user-consentable; no admin consent pre-granted (consent happens in the sign-in window).

## Test results (2026-11-09)
| Prompt | Result |
|---|---|
| `@Aurora Sales Agent` Which region had the highest revenue in October 2026? (Instant) | "Worked for 34s", a collapsible line "@ Compared October 2026 regional revenue" (the tool call; it doesn't expand further). **North America $384,656**, plus a bar chart and a table: Europe $228,659, Asia Pacific $143,554, Latin America $77,872, "about 46.1% of total", "+$155,997". **All correct** (truth.json). |
| `@Aurora Sales Agent` Build me a one-page HTML report for our sales managers: this fiscal year to date vs last year, revenue by region, the top 5 products, and a short summary. One single file, with KPI cards and a small chart. (Instant) | Worked 1 min 53 s. The chat text used the **fiscal rules from the agent's instructions** (Feb 1 - Oct 31 both years): $8.90M vs $7.49M (+18.8%), NA $3.75M, Europe +32.1%, Summit 2P Tent $1.48M. Then a file card "Aurora Sales FYTD Dashboard - Single HTML file - 10 KB" whose **Download HTML Report** link opens a **side-panel preview** (Download / Enter full view / Close). The report: 4 KPI cards (revenue $8.90M +18.8%, orders 4,199 +18.8%, units 56,457 +17.3%, margin 45.1% -0.2 pp), region bars FY26 vs FY25, a management summary, the top 5 products table. **Every number checked against the model: correct.** One slip in the chat text only: "margin down about 0.3 points" (true: 0.23; the report itself says -0.2 pp). |
