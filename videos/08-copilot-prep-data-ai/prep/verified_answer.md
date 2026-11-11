# The verified answer (Prep data for AI, tab 2)

**Visual**: report page *Finance view*, the table "Fiscal year to date vs last year, by region"
(Region, Revenue, Revenue PY, Revenue YoY %, Margin %), model measures only.
**Filter applied to the visual**: Date is on or after 2/1/2026 (the first day of fiscal 2026; the data ends Oct 31, 2026).

How: report in **Editing** > right-click the visual > **Set up a verified answer (preview)** > add the phrases > **Apply**.
It's saved in the semantic model, not in the report.

## Trigger phrases used in the video
1. How are we doing this year compared to last year?
2. How is this fiscal year going so far?
3. This year vs last year
4. Fiscal year to date vs last year
5. How does this year's revenue compare to last year by region? (a Copilot suggestion)

Microsoft suggests 5 to 7 phrases per verified answer (max 15, 500 characters each). Matching is by meaning too:
"Are we ahead of last year?" (not in the list) matched this answer in the video.

## Limits worth knowing (Microsoft Learn, Nov 2026)
- Not returned when **Fabric IQ** is on in the Copilot pane (tested: with Fabric IQ on, Copilot answered by itself).
- No report measures in the visual, no hidden fields, slicers aren't saved (visual filters are), up to 3 filters people can change.
- No Git / deployment pipeline support yet: in this repo's TMDL you'll find the AI instructions, not the verified answer.
- Preview. Verified answers need Q&A turned on for the model.
