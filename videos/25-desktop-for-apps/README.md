# Power BI Desktop for Apps: Build a Fabric App with AI

Video: https://youtu.be/xjxbHfnINy0

**Power BI Desktop for Apps (preview)** is a separate program that opens from Power BI Desktop. You pick a semantic model
that is published in the Power BI service, describe the app you want in plain words, and an agent writes a **Fabric app**
on top of that model. You check it on your own computer, change it, and publish it to a workspace.

This folder holds what I typed and what the agent wrote in the video, including the two mistakes it made.

| File | What it is |
|---|---|
| [`prompts.txt`](prompts.txt) | The four messages I sent to the agent |
| [`queries/top-products.first-build.dax`](queries/top-products.first-build.dax) | The query behind the "top 10" table: `TOPN` with no `ORDER BY`, so the rows came out unsorted |
| [`queries/product-revenue-share.before-fix.dax`](queries/product-revenue-share.before-fix.dax) | The query behind the product panel, with one product name and one year typed into the code |
| [`queries/product-revenue-share.after-fix.dax`](queries/product-revenue-share.after-fix.dax) | The same query after the fix |
| [`queries/kpi-summary.dax`](queries/kpi-summary.dax), [`queries/monthly-revenue.dax`](queries/monthly-revenue.dax), [`queries/monthly-revenue.json`](queries/monthly-revenue.json) | The cards, the trend, and the small file that says how to draw the trend |
| [`queries/filter-args.ts`](queries/filter-args.ts), [`queries/top-products.ts`](queries/top-products.ts) | How the page filters are put into a query |
| [`queries/check-kpis.dax`](queries/check-kpis.dax), [`queries/check-top10.dax`](queries/check-top10.dax) | The two queries I ran on the model myself, to check the app's numbers |

## What you need
1. **Power BI Desktop**, the November 2026 version or newer, on **Windows 11**.
2. A **semantic model that is published to the Power BI service**, and Build permission on it. A model that exists only
   in a file on your computer does not work.
3. A **GitHub account with a GitHub Copilot license**. The agent inside the program is GitHub Copilot (its command-line
   program is part of the installed files).
4. To publish: a **workspace on a Fabric capacity**. Microsoft's documentation says publishing to Pro workspaces is
   coming soon.
5. The tenant setting **Users can use Power BI Desktop for Apps (preview)**, in the admin portal under Copilot and AI.
   It is on by default.

## The steps of the video
1. **Switch it on.** In Power BI Desktop, sign in first: the switch is listed only when you are signed in. Then the gear
   icon, Options, **Preview features**, the last entry **Power BI Desktop for Apps**, OK. No restart. A button
   **New report app** appears on the Home ribbon.
2. **Install.** The first time, Windows asks to install the program (publisher: Microsoft). About a minute.
3. **Two sign-ins** inside the new program: Power BI (your models, publishing) and GitHub (the agent).
   If you work with more than one account: the program signed in with my Windows account, not with the account of
   Power BI Desktop. What fixed it for me: adding the other account to Windows (Settings, Accounts, Email and accounts,
   Add a work or school account).
4. **Choose a model.** The first small icon in the message box is Get data. Search, pick your semantic model.
5. **The menus under the box.** Auto (the AI model: Efficiency, Balance, Intelligence; switch Auto off to pick a model
   yourself) and Interactive (the mode).
6. **Name the app and send the request** (message 1 in `prompts.txt`).
7. **Check the result** in View: use the filters, click a bar, and compare the numbers with a report or a query you trust.
8. **Fix by talking.** Switch to **Edit**, click a part of the app (it becomes a tag above the message box), and say what
   is wrong.
9. **The look.** In Edit, the **Design** pane changes the theme, font, spacing and colors at once, with no agent. Click a
   heading to edit its text.
10. **Publish.** Pick a workspace. Publishing took about 80 seconds. The item gets a name in small letters with dashes.
11. **Share** from the item's page in Fabric (Manage access, Add person or group). People who open the app also need
    permission on the semantic model.

## What I measured (one evening, one model)
| Step | Time |
|---|---|
| First build from the prompt | about 6.5 minutes |
| A small fix (sort the table) | about 35 seconds |
| A new feature (the product panel) | almost 7 minutes |
| The fix of the panel's numbers | right on screen after about a minute |
| Publish | about 80 seconds |

GitHub Copilot usage after the whole evening (two apps, six requests): the usage page showed under 1% of the monthly
premium requests of my plan. That page says the number can lag, so read it as a rough idea.

## The two mistakes, and why this matters
1. **A "top 10, ranked by revenue" table that was not sorted.** The ten products were the right ones; the order was not.
   The query used `TOPN`, which picks rows but does not sort them.
2. **A product panel that showed another product's revenue.** Storm Shell Jacket showed $1,608,314 (the first product in
   the table) instead of $1,237,165. The query still had `"Summit 2P Tent"` and `2026` typed into it, left over from the
   agent's own test.

Neither mistake produced an error. Both looked perfect. So check the numbers against the model every time.

## Good to know
- It is a preview: the screens will change.
- The app never changes your semantic model. It only sends it DAX queries.
- Every query runs with the permissions of the person who is looking (this is how Microsoft documents the semantic model
  connector of Fabric apps). I did not test row-level security in the video.
- What the agent makes is a normal code project in a folder on your computer: a DAX file per visual, a small drawing file
  per chart, and a history with a step for every turn of the agent.
- The project's own configuration file holds the keys of your workspace and model. It is not in this folder, and it
  should not go into a public repository.
- The Aurora Sales model is a demo: the products, regions and amounts are made up.

MIT license, like the rest of this repository.
