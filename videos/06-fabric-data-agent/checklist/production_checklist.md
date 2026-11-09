# Before a Fabric data agent goes to production: 6 checks

From the PBI101 video (folder 06-fabric-data-agent). If any answer is vague, the agent is still a pilot. That's fine;
it just means the platform work isn't finished.

## 1. Its own identity
- [ ] We know whose access runs the query in every channel (in Fabric it's the person asking; in Copilot Studio with
      maker authentication it's whoever set it up, so everyone sees what that person sees).
- [ ] Production uses a dedicated identity (for example a service principal) with only the access this job needs.
      Never one person's account.

## 2. One narrow job
- [ ] One sentence says what it's for. Example: "Regional sales questions for the sales managers."
- [ ] Not "ask anything about our data".

## 3. Known data sources (access inventory)
| Workspace | Item (type) | Access | Business owner | Approved | Next review |
|---|---|---|---|---|---|
| Sales | Aurora Sales (semantic model) | view-only | Sales Ops | 2026-11-09 | 2027-02-09 |
|  |  |  |  |  |  |

- [ ] If nobody can say what the agent can reach, it isn't ready.

## 4. Dev / test / production
- [ ] Separate workspaces (or deployment pipeline stages) for experiments, validation and the supported version.
- [ ] The agent definition is in Git (data agents support Fabric Git integration and deployment pipelines), so changes to
      the instructions and the selected tables get reviewed.

## 5. An audit path
- [ ] We can tell which identity asked, which source answered, who reviews activity and who investigates issues.
- [ ] Usage: the Fabric Capacity Metrics app (operation "AI Query"). Conversations: Microsoft Purview (preview).
- [ ] We can separate an agent issue (instructions, routing) from a model issue (measures, descriptions).

## 6. New sources = a change request
- [ ] Every new source re-checks the identity, the permissions, the audit path and the owner.

## Habit: golden questions
- [ ] A few questions with known answers, asked again after every change (see `agent/golden_questions.md`).
