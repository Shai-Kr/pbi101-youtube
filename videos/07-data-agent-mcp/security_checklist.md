# Security checklist: a Fabric data agent in a chat app (MCP)

From the PBI101 video (folder 07-data-agent-mcp).

1. **You sign in as yourself.**
   - [ ] The agent answers with the signed-in user's permissions; row-level security on the model still applies.
   - [ ] Test with a user who should see less.
2. **The answers land in the chat app.**
   - [ ] Your company policy allows this chat app for this data.
   - [ ] A business / enterprise plan with data controls. Never real company data in a personal account.
   - [ ] Microsoft's own note: responses can leave Fabric's compliance boundary and region and follow the MCP client's terms.
3. **The address isn't a password,** but it shows your workspace and agent keys.
   - [ ] Share it like an internal link; keep it out of public repos and screenshots.
4. **Publish only the agent you mean to share.**
   - [ ] One narrow job, a clear publish description (it becomes the MCP tool description).
   - [ ] The app registration asks only for read/run permissions: DataAgent.Execute.All, DataAgent.Read.All,
         Dataset.Read.All (+ User.Read). Nothing that writes.
5. **Remove it when you're done, and audit it.**
   - [ ] ChatGPT: Plugins > Personal > the plugin's ... menu > Uninstall.
   - [ ] Entra: remove the consent or the app registration if it's no longer used.
   - [ ] Fabric Capacity Metrics (operation "AI Query") and Microsoft Purview (preview) for usage and conversations.
