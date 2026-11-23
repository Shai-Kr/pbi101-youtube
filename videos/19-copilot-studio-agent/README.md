# Copilot Studio Agent for Beginners: Fabric Data in Teams

Video: coming soon on the PBI101 channel.

A beginner's walk through **Microsoft Copilot Studio**: an agent that sits in Microsoft Teams and answers from your data
in Microsoft Fabric. It is built by clicking, with no code: instructions, one tool, a test, a channel, Publish.

## What you need
- A Copilot Studio environment where you can create agents, with billing set up (a plan, or pay as you go).
- A **published** Fabric data agent. The one in the video answers questions about the orders of a pretend store; it is
  built step by step in [`../18-data-agent-basics`](../18-data-agent-basics).
- Microsoft Teams.

## The steps of the video
1. **Create the agent.** Copilot Studio home, the **Agent** card. Type a name (the video uses
   `Aurora Orders Assistant`).
2. **Instructions.** Click the Instructions box and type [`agent_instructions.txt`](agent_instructions.txt), without its
   last two sentences for now (they are added in step 7).
3. **Remove the defaults.** In the panel on the right, remove the tool *Work IQ* and the knowledge
   *Search all websites*. The agent should answer from your data only.
4. **A first test.** The **Preview** tab is a chat for testing. With no tool the agent says it has nothing to call, and
   does not invent a number.
5. **Add the tool.** **Build** tab, the plus next to *Tools*, search `Fabric`, choose **Fabric IQ Data MCP**, **Add**.
   Pick your data agent in the list (only published data agents are listed), **Connect**.
6. **Test again.** **Preview**, **New chat**, the same question.
7. **One fix.** With the first instructions the agent rewrote the question, called the tool five times and took almost
   two and a half minutes. Add the last two sentences of the instructions file ("Send each question to the tool once,
   in the user's own words. Do not rewrite it, and do not add dates or time zones."), open a new chat and ask again:
   one call, about 25 seconds.
8. **Look at the call.** The line *Used tool* above an answer opens the tool's description (the text you wrote when you
   published the data agent), the input (your question) and the time it took.
9. **Add a channel.** The plus next to *Channels*, **Teams + Microsoft 365**, *Microsoft Teams only* (this choice cannot
   be changed after publishing), **About info** for the short description people see, **Add channel**.
10. **Publish.** **Publish**, **Publish agent**. The label next to the name changes from *Draft* to *Published*. Every
    later change stays a draft until you publish again.
11. **Open it in Teams.** The channel, **Use and share**, **View in Microsoft Teams**; in Teams click **Add**, then
    **Open**, and ask.

## What the agent answered in the video (2026-11-21)
| Where | Question | Answer |
|---|---|---|
| Preview, no tool | How many orders did we get in the last hour, by region? | "I can't give you [the] counts ... the tool isn't connected ... I won't estimate the numbers." |
| Preview, tool connected | the same question | 1,053 orders by region, right (checked with a direct query), after five calls and almost 2.5 minutes |
| Preview, after the added sentence | the same question | 461 / 304 / 187 / 106 by region, right, one call, about 25 seconds, about 1.4 Copilot credits |
| Preview | What is the weather in Toronto today? | "I can only help with questions about ... orders and sales" |
| Teams | How are sales today compared to yesterday? | today 6,092,594 against 5,388,372, about 13% up, the same hours of both days: right |
| Teams | Which region is leading today? | North America (right), with a sales figure of 81 million that the agent itself flagged: "That figure doesn't add up ... I wouldn't trust that sales number yet." The real number was 2,614,820 |

## Good to know
- An agent is instructions, tools, knowledge and channels. It decides when to call a tool from the tool's description.
- Sharing the agent does not give anybody access to the data: each person also needs access to the Fabric data agent
  and to the data behind it. The agent answers with the permissions of the person who asks.
- Cost: Copilot credits for the agent, plus Fabric capacity on every call to the data agent.
- An answer in Teams took 30 to 40 seconds: the question goes through the agent, the tool, the data agent and the
  database, and back.
- The agent keeps the description of a tool from the moment you added it. If you change the data agent in Fabric,
  check that this agent still knows what it can ask.
- The store is simulated: the products, cities and amounts are made up.

MIT license, like the rest of this repository.
