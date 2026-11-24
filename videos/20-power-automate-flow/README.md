# Power Automate for Beginners: Fabric Alert to a Teams Agent

Video: coming soon on the PBI101 channel.

A beginner's walk through **Microsoft Power Automate**, built around one job: when a rule in Microsoft Fabric notices that
a region stopped ordering, a flow posts the alert into a Teams chat with an AI agent, and the agent answers by itself.
Everything is built by clicking. The two messages the flows post are in [`flow_messages.txt`](flow_messages.txt).

## What you need
- Power Automate (make.powerautomate.com) and Microsoft Teams.
- For the second flow: a rule in **Fabric Activator** (the video uses the rule "Region went quiet" from
  [`../17-activator-alerts`](../17-activator-alerts)), and a license that covers premium connectors, or a flow that runs
  on the Copilot Studio plan (see step 7 of flow 2).
- A chat to post into. The video uses the chat of the agent built in
  [`../19-copilot-studio-agent`](../19-copilot-studio-agent); any chat works for learning the tool.

## Three words
- **Flow** = a trigger and then actions: *when this happens, do that*.
- **Connector** = a ready-made plug to one service (Teams, Outlook, Fabric ...), with its own triggers and actions.
  Standard connectors come with a regular Microsoft 365 license; premium ones need a paid plan.
- **Connection** = a connector plus your sign-in. The flow works with the account of the person who built it.

## Flow 1: a button (instant cloud flow)
1. **Create**, **Instant cloud flow**. Name it (`Ask the orders agent`), choose **Manually trigger a flow**, **Create**.
2. Click the trigger card. **Add an input**, **Text**, and name the input `Region`.
3. Click the **+** under the trigger. Search `post message in a chat` and choose Microsoft Teams,
   **Post message in a chat or channel**.
4. **Post as**: `User`. The message then comes from your own account. An agent answers people; it does not answer the
   Flow bot.
5. **Post in**: `Group chat`.
6. **Group chat**: open the list, choose **Enter custom value** at the bottom, and paste the key of the chat.
   Where the key comes from: in Teams, point at any message in that chat, the three dots, **Copy link**. The link looks
   like `https://teams.cloud.microsoft/l/message/19:(letters and digits).spaces/1795...`. The key is the part that
   starts with `19:` and ends with `.spaces`, including both.
7. **Message**: type `How many orders did we get in the last hour in `, click the lightning icon (dynamic content),
   search `region`, pick **Region** under "Manually trigger a flow", then type `?`.
8. **Publish**. Then **Test**, **Manually**, **Test**: check the connection (a green check), **Continue**, type a region
   (the video types `Europe`), **Run flow**, **Done**.
9. The run page shows a green check and a duration on every card. Click a card to see what it received and what it sent.
   When a flow fails, the card that failed is red and says why.

## Flow 2: an event (automated cloud flow, started by Fabric Activator)
1. In Fabric Activator open the rule, **Definition**, the **Action** list, **Create custom action** (at the bottom).
2. Give the action a name (`Tell the orders agent`). Input fields are optional (extra values the rule hands to the flow;
   the video uses none). **Copy** the connection string. Leave the window open.
3. In Power Automate: **Create**, **Automated cloud flow**. Name it (`Quiet region alert`), search the triggers for
   `activator`, choose **When an activator rule is triggered**, **Create**.
4. Click the trigger card and paste the connection string into **Connection String**.
5. Add the same Teams action as in flow 1 (Post as `User`, Post in `Group chat`, the same chat key).
6. **Message**: `Alert from Fabric: orders stopped in ` + dynamic content **Object instance ID** +
   `. Show me the last three orders from ` + **Object instance ID** again + `, with their times.`
7. **Publish**. In the video this answered: "Flow could not be activated because you need a Power Automate Premium
   license ..." (the Activator trigger is a premium connector). The flow is saved, switched off. Two ways on: a premium
   license, or, in an environment that already pays for Copilot Studio credits: the flow's page, **Edit** on the Details
   card, **Plan**, **Copilot Studio**, **Save**, **Confirm** (this choice cannot be changed back). Then switch the flow
   **On**. Ask your admin which way fits your organization.
8. Back in Activator the window now says the custom action is available: **Done**. Open the **Action** list again and
   choose your custom action.
9. **Test action** fires the flow once with sample values (the video's message said "orders stopped in Sample Package").
   It proves the wiring, not the text.
10. **Save and start**. From now on the flow runs whenever the rule fires. The flow's page keeps a run history.

## What happened in the video (2026-11-23)
| Step | What |
|---|---|
| Flow 1, typed `Europe` | the question appeared in the chat as my own message; the agent answered about 25 seconds after Run flow: 343 orders from Europe in the last hour (a direct query on the database for the same hour: 340 to 343) |
| Flow 2, Test action | "Alert from Fabric: orders stopped in Sample Package ..."; the agent answered that "Sample Package" is not a region and asked which region to check |
| Flow 2, a real stop | Europe's last order was at 23:13:30 UTC. The alert reached the chat 7 minutes 45 seconds later (the rule waits for 5 minutes of silence, plus its own wait for late events). The agent answered 52 seconds after that: "The alert looks real. Europe's last order came in at 6:13:30 PM ET, about 8 minutes ago", with the three last orders. The same three orders, to the second, came back from a direct query |

## Good to know
- A flow works with the connections of the person who built it: this one posts as its owner. Give a real flow a second
  owner, or it stops when one person leaves or a sign-in expires.
- Every run of a flow on the Copilot Studio plan uses credits, and so does every answer of the agent. Switch off rules
  and flows you do not need.
- The dynamic content list of the Activator trigger offers: Activation time, Activation ID, Rule ID, Rule name, Rule URL,
  Object instance ID, Object name and Input fields (your own input fields, as one JSON text).
- The store is simulated: the products, cities and amounts are made up.

MIT license, like the rest of this repository.
