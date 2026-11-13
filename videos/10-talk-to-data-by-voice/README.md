# I Asked My Power BI Data Out Loud. It Answered.

Materials for the PBI101 video about **talking to a Power BI semantic model by voice**: ChatGPT voice chat, calling a
Microsoft Fabric data agent through its MCP endpoint. It's less of a tutorial and more of a thought: what changes when
your data can talk back, and where that is useful (picture a CEO on the drive to the office).

## Nothing new to build
Voice works with the setup from two earlier videos, with no extra step:
1. [Build a Fabric Data Agent in 5 Minutes (+ Prod Checklist)](https://youtu.be/KOMo49vQUAc): the agent on a semantic model.
   Materials: [`../06-fabric-data-agent`](../06-fabric-data-agent)
2. [Connect ChatGPT to Power BI with a Fabric Data Agent (MCP)](https://youtu.be/FdP5rTgeqC4): the agent as a plugin in
   ChatGPT. Materials: [`../07-data-agent-mcp`](../07-data-agent-mcp)

Then: open a chat with the plugin tagged, tap the **voice** button, and ask. Any assistant that speaks MCP and has a
voice mode should be able to do the same; I tested ChatGPT (web, a Business workspace, November 2026).

## What's inside
| Path | What |
|---|---|
| `questions.md` | The three questions, what ChatGPT said out loud, the waits, and every number checked against the model. |
| `dax/check_numbers.dax` | The DAX behind that check. |
| `voice_instructions.md` | Optional ChatGPT instructions for a voice chat with data (English, short, always ask the agent). |

The semantic model (Aurora Sales, synthetic data) is in [`../09-copilot-build-report`](../09-copilot-build-report).

## What I learned
- **It just worked.** Same agent, same plugin, voice button. Older posts say voice mode ignores connectors; in my test
  it called the agent and the numbers were the real ones.
- **It's not fast.** 59, 53 and 77 seconds for the three answers. In a car that's a long silence.
- **It speaks a headline and writes the details.** You can't hear a table, so voice is for headlines, not for an audit.
- **An answer, not the answer.** The "one thing to fix" was real and worth about five thousand dollars on more than a
  million in sales. Deciding if it matters is still your job.
- **Security doesn't change.** The agent answers with the signed-in user's permissions, and the answers land in the
  chat app: check your company's policy before real data goes there
  ([`../07-data-agent-mcp/security_checklist.md`](../07-data-agent-mcp/security_checklist.md)).
- **After pausing and resuming a capacity, the published agent can fail for a while** (authorization errors) even when
  the draft test pane works. The chat uses the published version: test that one.

## About the recording
The questions are asked in my AI voice (the one that narrates the channel), played into the microphone. The answers
are ChatGPT's own voice, recorded as it happened. The data is a synthetic demo company.

Channel: https://www.youtube.com/@pbi101
