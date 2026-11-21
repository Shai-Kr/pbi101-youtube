# Fabric Activator for Beginners: Step by Step

Video: https://youtu.be/R2eB3odh-OQ

A beginner's walk through **Activator** in Microsoft Fabric: the item that watches your events and acts when a
condition comes true. Two rules are built by clicking, with no code: a message in Teams for every big order, and a
message when a whole region stops ordering.

## What you need
- A Fabric workspace on a capacity (a trial works), with Contributor rights or more.
- An **Eventstream** with events flowing through it. The video uses the orders of a pretend store; the notebook that
  sends them and the Eventstream itself are in [`../14-eventstream-basics`](../14-eventstream-basics).
- Microsoft Teams, for the messages. (Email works the same way.)

Every order is one small JSON message with these fields: `OrderNumber`, `OrderTime`, `Product`, `Category`, `Region`,
`City`, `Quantity`, `UnitPrice`, `SalesAmount`, `PaymentMethod`, `Channel`.

## The steps of the video
1. **Create the Activator.** In the workspace: **New item**, type `activator`, click the card. The item is created at
   once, named *Activator* plus the date and the time.
2. **Connect the stream.** **Get data**, and in *Streams* click the name of your stream. *Preview data* shows the
   events: **Next**, **Connect**, **Finish**. (Fabric adds the Activator as one more destination of the Eventstream.)
3. **Rename it.** **Home** tab, **Settings**, type a name (the video uses `Aurora Alerts`), close the panel.
4. **Look around.** The *Explorer* on the left lists the Eventstream and its stream; the chart shows the events over
   time; the grid below lists them. Set **Time** (top right) to *Last 30 minutes* to see a new stream.
5. **Rule 1: a big order.** Above the chart click **New rule**. The rule is created at once and its *Definition*
   opens on the right. Fill it in as in the first table below, then **Save and start**. Rename the rule with the pencil
   beside its name.
6. **Create an object.** Click the stream in the Explorer, then **New object** (beside *Event details*):
   Object name `Region`, Unique Identifier `Region`, tick the properties `City` and `SalesAmount`, **Create**. The chart
   now has one row per region.
7. **Rule 2: a region went quiet.** On the object's page click **New rule**, fill it in as in the second table,
   **Save and start**, and rename it.
8. **History.** Each rule has a *History* tab that counts its activations (today, yesterday, this week).
9. **Stop.** A running rule uses capacity. **Stop** (in the ribbon) the rules you no longer need.

### Rule 1: Big order (on the stream)
| Section | Setting | Value |
|---|---|---|
| Monitor | Event | the stream of orders |
| Condition | Operation | Numeric state, **Is greater than** |
| Condition | Column | `SalesAmount` |
| Condition | Value | `1000` |
| Action | Action | Teams, **Message to individuals** |
| Action | Recipient(s) | yourself (people inside your organization only) |
| Action | Headline | `Big order` |
| Action | Message | `A customer just placed an order above 1,000 dollars.` |
| Action | Context | `Product`, `City`, `SalesAmount` |
| Advanced settings | Wait time for late-arriving events | 2 Minutes (the default) |

**Edit action** shows a preview of the message before you start the rule.

### Rule 2: Region went quiet (on the object `Region`)
| Section | Setting | Value |
|---|---|---|
| Monitor | Event | the stream of orders (of the object) |
| Condition | Operation | Heartbeat, **No presence of data** |
| Condition | Time elapsed | **5 minutes** |
| Action | Action | Teams, **Message to individuals** |
| Action | Headline | `Orders stopped: ` followed by the property **Region** (click the tag beside the box, type `Reg`, pick it) |
| Action | Message | `No orders from this region for 5 minutes.` |

## How to test
- **Rule 1.** Give a new rule a few minutes after **Save and start**, then wait for an order above 1,000. With the
  store notebook of video 14 that is 2 or 3 big tents in one order: about one order in a hundred. In the video the
  message reached Teams 7 seconds after the order (15 seconds in an earlier test); an order sent 15 seconds after the
  rule was started was missed.
- **Rule 2.** Stop the store notebook. After the quiet time you get one message for every region: in the video, 8
  minutes after the last order (5 minutes of silence, the 2 minute wait for late events, about one more on the way).

## Good to know
- Activator uses capacity while rules are running. Stopping all rules stops that, but the events keep arriving in the
  Activator until you remove the stream from it.
- Messages and emails go only to people inside your organization, and a rule can send only a limited number of them to
  one person in an hour. Build rules that fire rarely.
- Other ways in: **Set alert** on a tile of a Real-Time Dashboard (only tiles that use a predefined time range), on a
  KQL queryset, or on a visual of a Power BI report. Each one ends up as a rule inside an Activator.
- An action can also run a Fabric item (a pipeline, a notebook, a dataflow) instead of sending a message.
- The store is simulated: the products, cities and amounts are made up.

MIT license, like the rest of this repository.
