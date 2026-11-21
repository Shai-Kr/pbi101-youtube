# Fabric Data Agent for Beginners: Step by Step

Video: https://youtu.be/aBbjOcO4z0Y

A beginner's walk through the **data agent** in Microsoft Fabric: you ask a question in plain English, the agent writes
the query, runs it on your data and answers. The video builds one on a table of orders, catches it guessing and catches
it being wrong, and then teaches it with three kinds of text. All of them are in this folder.

## What you need
- A Fabric workspace on a **paid** capacity (F2 or higher), and the tenant setting *Users can use Copilot and other
  features powered by Azure OpenAI* turned on by your admin.
- Some data. The video uses the orders of a pretend store in a KQL database (an Eventhouse); the notebook that sends
  them and the table are in [`../14-eventstream-basics`](../14-eventstream-basics) and
  [`../15-eventhouse-kql`](../15-eventhouse-kql). A lakehouse, a warehouse, a SQL database or a Power BI semantic model
  works too.

The table has one row per order: `OrderNumber`, `OrderTime` (text, UTC), `Product`, `Category`, `Region`, `City`,
`Quantity`, `UnitPrice`, `SalesAmount`, `PaymentMethod`, `Channel`.

## The steps of the video
1. **Create the agent.** In the workspace: **New item**, type `data agent`, click the card, give it a name, **Create**.
2. **Add a data source.** Click **Add a data source**. The OneLake catalog lists everything you may use, from every
   workspace: open the small **Explorer** on the left of the dialog, click your workspace under *Quick access*, pick
   the database, **Add**. One agent can have up to five sources.
3. **Choose the tables.** In the *Sources* tab, tick the table the agent may use (until you do, a note says
   *No tables selected yet*).
4. **Ask a question** in the chat, then open **1 step completed** under the answer. It shows how the agent understood
   the question, and **Show input** shows the query it wrote.
5. **Agent instructions** (the button in the ribbon). Click inside the box, select all, and paste
   [`agent_instructions.txt`](agent_instructions.txt).
6. **Clear chat**, and ask the same question again.
7. **Setup** tab, **Data source instructions**: paste [`data_source_description.txt`](data_source_description.txt) into
   the first box and [`data_source_instructions.txt`](data_source_instructions.txt) into the second.
8. **Setup** tab, **Example queries**, **Add example**: the question `How are sales today compared to yesterday?` and
   the query [`example_today_vs_yesterday.kql`](example_today_vs_yesterday.kql).
9. **Publish** (it asks for a description of what the agent can answer). From then on there is a *Draft* and a
   *Published* version.
10. **Share**: a person you add can ask the published agent questions. Sharing the agent does **not** give access to
    the data: on a KQL database they also need at least the Reader role.

Change the names in the texts to your own table and columns. In the example query, `OrdersLive` is the table.

## What the agent answered in the video (2026-11-21)
| Setup | Question | Answer |
|---|---|---|
| nothing yet | How many orders did we get in the last hour, by region? | right (checked with a direct query); it converted the text time column by itself |
| nothing yet | What is our best-selling product this week? | Glacier Water Bottle, by **units** |
| + agent instructions | the same question | Basecamp 6P Tent, 7,495,746 dollars, "last 7 days": by **dollars**, as the instructions say |
| + agent instructions | How are sales today compared to yesterday? | "about 38% lower ... comparing the same hours": **wrong**. The query compared all of yesterday with today so far |
| + data source instructions + the example query | the same question | yesterday 3,451,603, today 3,832,166, about 11% higher: the same as a direct query |
| everything, published | Which city had the most big orders today? | Denver, 922: **wrong** (no city had more than 18) |

So: instructions and examples help a lot, and the agent can still be wrong. Test it with questions whose answers you
already know, and keep opening the steps.

## Good to know
- Agent instructions go along with every question (up to 15,000 characters). Data source instructions hold facts about
  one source. Example queries are pairs of a question and a query; the agent looks up the closest ones for each
  question and follows them. Semantic models do not take example queries.
- A published agent can be used from Copilot Studio, Teams and Microsoft 365 Copilot, Azure AI Foundry, or any AI tool
  through its MCP address.
- You pay in capacity for the tokens that go in and come out; long instructions and long chats cost more.
- An answer shows up to 25 rows. English only. It only reads data. It is not built for "why" questions.
- The store is simulated: the products, cities and amounts are made up.

MIT license, like the rest of this repository.
