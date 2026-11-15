# The prompts from the video

Both were typed into an AI coding agent (Claude Code) inside a new Fabric App project
(`npm create @microsoft/rayfin@latest aurora-pulse`). Change the names of the model and the workspace to yours.

## 1. Build the app and deploy it

```text
Turn this new project into a simple Fabric App called Aurora Pulse. One page: three big numbers for 2026 (revenue,
orders and margin percent) and a bar chart of revenue by region. Take the numbers from my Power BI semantic model
"Aurora Sales" in the workspace "pbi101". When it works, deploy it to that same workspace and give me the link.
Don't open a browser to test it, I'll check it myself.
```

What the agent did with it, in order: read the instructions that came with the project, switched on the parts the app
needs (data connection, analytics, charts), found the semantic model and connected to it, wrote the DAX and ran it
against the real model before drawing anything, wrote the page, ran the template's tests, built and deployed. At the
end it said what it had checked and what it had not (it never opened the app in a browser).

## 2. Ask for a change

```text
Nice. Now add a second chart under it: revenue by month for 2026. Then deploy again.
```

## Tips

- Say where the numbers come from (the model and the workspace, by name). The agent finds the ids.
- Ask it to deploy and to give you the link, or it stops when the code is written.
- Tell it not to open a browser. Mine tried to test the page that way and landed on a sign-in page.
- Check the numbers against your report before you trust the page. Mine matched: revenue 2026 = $9,561,827.
