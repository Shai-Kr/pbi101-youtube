# The one-time app registration in Microsoft Entra

The data agent's MCP endpoint is protected by Microsoft Entra ID and supports **no dynamic client registration** and no
client metadata documents, so ChatGPT needs an app registration of its own (a "user-defined OAuth client").
Your admin creates it once. In the Entra admin center: **App registrations > New registration**.

| Setting | Value |
|---|---|
| Name | anything, e.g. `ChatGPT - data agent` |
| Supported account types | This organizational directory only (single tenant) |
| Redirect URI | platform **Mobile and desktop applications** (public client, no secret): the **Callback URL** that ChatGPT shows in *Advanced OAuth settings* (looks like `https://chatgpt.com/connector/oauth/<your-code>`). Adding `https://chatgpt.com/connector_platform_oauth_redirect` too doesn't hurt. |
| API permissions (delegated) | Power BI Service: **DataAgent.Execute.All**, **DataAgent.Read.All**, **Dataset.Read.All**; Microsoft Graph: **User.Read** |
| Client secret | none (token endpoint auth method `none` in ChatGPT) |
| You get back | the **Application (client) ID**: paste it into ChatGPT's *OAuth client ID* box |

Consent: the first sign-in shows "Permissions requested". An admin can tick "Consent on behalf of your organization".
Where users can't consent, they send a request and the admin approves it.

Script version: `create_app_registration.ps1` (az CLI).
