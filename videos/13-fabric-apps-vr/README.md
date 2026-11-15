# Fabric Apps, step by step, and a Power BI dashboard you can stand inside

**Video:** [I Put My Power BI Dashboard in VR (Fabric Apps Guide)](https://youtu.be/wNoeba0Glvs)
**Article:** [the story and the thinking behind it](https://shai-kr.github.io/data-ninja-ai-lab/blog/2026-11-15-power-bi-dashboard-in-vr-fabric-apps.html)

A **Fabric App** is a new kind of item in a Fabric workspace (preview): your own web application, hosted by Fabric,
with the Fabric sign-in in front of it and your data behind it. The video has two parts, and so does this folder:

1. **The how.** A simple app, built by an AI coding agent from one prompt: three numbers and two charts on a Power BI
   semantic model. The prompts are in [prompts.md](prompts.md).
2. **The extreme.** The same idea taken as far as I could: a room in VR (it also runs in a normal browser) where the
   boards, a basket, a pair of scales, Saturn and a guide all read the same semantic model. The whole project is in
   [vr-room/](vr-room).

## What you need

| | |
|---|---|
| A workspace on a Fabric capacity | a trial capacity is fine |
| The admin switch | Admin portal > Tenant settings > **Enable Fabric App items (preview)** (a Fabric admin turns it on) |
| A region that has the feature | it is a preview and not everywhere yet |
| On your computer | [Node.js](https://nodejs.org) (LTS) |
| For part one | an AI coding agent. I used Claude Code; others work too |
| For part two in VR | a headset with a browser (I used a Quest 3). Without one, the room runs in any desktop browser |

## Part one: a simple app from one prompt

1. In a terminal: `npm create @microsoft/rayfin@latest aurora-pulse`, and press Enter for the default template.
   The new project brings its own instructions for AI agents (the `.agents/skills` folder), so there is nothing to
   download separately.
2. `cd aurora-pulse`, start your AI coding agent, and give it the first prompt from [prompts.md](prompts.md)
   (change the model and workspace names to yours).
3. The agent connects the app to the model, checks its DAX against the real numbers, writes the page and deploys it.
   On my machine that took 14 minutes; a change request ("add a chart, deploy again") took 5.
4. The first time the command line tool runs, it opens a browser and asks you to sign in to Fabric. That is normal.

The model I used is **Aurora Sales**, a small synthetic sales model. It is in [../09-copilot-build-report](../09-copilot-build-report) as a
Power BI project: open the `.pbip` file in Power BI Desktop, refresh, and publish it to your workspace.

## Part two: install the VR room on your own workspace

The room asks the model **one DAX query** when it opens and works out everything else in the browser. It expects the
Aurora Sales model (tables `Date`, `Regions`, `Products`; measures `Revenue`, `Cost`, `Orders`, `Units`).

1. Publish the Aurora Sales model to your workspace (see above), if it is not there yet.
2. Download this repository and open a terminal in `videos/13-fabric-apps-vr/vr-room`.
3. `npm install`
4. Tell the app where your model is. Open `rayfin/rayfin.yml` and replace the two placeholders:
   - `YOUR_WORKSPACE_ID` and `YOUR_SEMANTIC_MODEL_ID`. Both are in the address bar when the semantic model is open in
     Fabric: `.../groups/<workspace id>/datasets/<semantic model id>/...`
5. `npx rayfin up` and pick your workspace when it asks. It signs you in, creates the App item, uploads the room and
   prints the app's address.
6. Open that address in a browser and sign in. In a headset: open the same address in the headset's browser, sign in,
   and press **ENTER VR** at the bottom of the page.

To change the name of the item in your workspace, edit `name` at the top of `rayfin/rayfin.yml` before step 5.

**Only want a look?** `npm run dev:frontend` in `vr-room`, then open `http://localhost:5173/preview.html`: the room
with a saved copy of the numbers, no Fabric and no sign-in.

### Optional: let the guide ask a Fabric data agent

The guide answers a few quick questions from the numbers that are already in the room. The green button sends any
question to a **published Fabric data agent**:

1. In Fabric, open your data agent > Settings > Model Context Protocol, and copy the MCP server address.
2. Paste it into `vr-room/packages/functions/src/agent_endpoint.ts`.
3. `npx rayfin up` again.

The function calls the agent as the owner of the App item, so that person needs access to the agent. An answer took
30 to 45 seconds for me. (Building a data agent on this model is in [../06-fabric-data-agent](../06-fabric-data-agent).)

## The controls

| | Headset | PC |
|---|---|---|
| Move | left stick: glide slowly | W A S D |
| Turn | right stick: turn slowly | Q E, or drag to look |
| Pick, press, cut, filter | trigger | click |
| Grab a ball or a board | grip (a ball flies to your hand: point at the basket or the scales and let go) | hold the right mouse button |
| Go inside what you point at | A or X | F |
| One step back | B or Y | B |
| Menu | A or X while pointing at nothing | M |
| Hide the corner box | | H |

## What is in the room

- **Three boards**: revenue by region, by month, by product. Pull the trigger on a bar and the whole room is filtered.
- **Saturn**: the planet is the company, its ring is the year, one piece per month. The light in the sky is this year
  against last year.
- **Region planets**: size is the region's share, speed is its growth. Go inside one and the room becomes that region.
- **The basket**: throw in a measure and a few members (Revenue + Europe + Asia Pacific) and it builds the answer.
- **The scales**: one member on each pan, a measure on top.
- **The cut**: one block for everything; each cut goes a level deeper (region, category, product).
- **A guessing game**, and **a guide** who answers quick questions and can pass a question to a Fabric data agent.

## What it costs, and what to know

- There is no separate price for a Fabric App. It runs on the capacity of its workspace, and it only works while that
  capacity is running. Every time the room opens it sends one DAX query, like a report page would.
- People who open the app sign in with their Fabric account, and the model's own permissions decide what they get.
- This is a preview: expect things to change. The app's files can be up to 100 MB; there is no deployment pipeline
  for apps yet.

## What was tested, and what was not

- The room in this folder is the one in the video: deployed to a Fabric workspace from my machine many times, used on a
  Quest 3 and in Chrome.
- This public copy (with the placeholders) was installed and built from a clean folder. It was **not** deployed to a
  second tenant, so steps 4 and 5 are written from how my own first deploy went.
- The room was built for the Aurora Sales model. On another model it needs a different DAX query and labels
  (`packages/frontend/src/queries/aurora-cube.dax`, `packages/frontend/src/vr/data.ts`).

## Credits

The app project is built on Microsoft's Fabric App template (MIT license, in `vr-room/LICENSE`). The room uses
[three.js](https://threejs.org) and the fonts Exo 2 and Orbitron. The guide's picture is mine: put your own in
`vr-room/packages/frontend/public/guide.png`.

More from me: [the PBI101 channel](https://www.youtube.com/@pbi101) · [pbi101.com](https://pbi101.com)
