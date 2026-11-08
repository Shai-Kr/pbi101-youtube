# PBI101 · Data + AI, minus the boring part

Materials for the **[PBI101 YouTube channel](https://www.youtube.com/@pbi101)**: hands-on Power BI, Microsoft Fabric, AI agents and AI skills.

Every video gets its own folder with what you need to rebuild the demo yourself:
- the Power BI project (PBIP);
- the sample data and the script that generates it;
- the code from the video (TMDL, DAX, SQL, Python);
- notebooks, when there are any.

```sql
SELECT magic FROM your_data;
```

## Videos

| # | Video | Topic | Materials |
|---|---|---|---|
| 02 | [Power BI Object-Level Security (OLS) in Under 8 Min: Zero Errors](https://youtu.be/6vz2SXUkJ68) | OLS setup in TMDL view + 3 ways to fix the broken visuals (separate reports, field parameters + RLS, role detector) | [videos/02-ols-deep-dive](videos/02-ols-deep-dive) |
| 03 | AI Skills for Power BI: One Prompt Redesigned My Report | Microsoft's Skills for Fabric in Claude Code: redesign a report with one prompt, make the model AI-ready, and see why business context matters (episode 1 of a series) | [videos/03-ai-skills-intro](videos/03-ai-skills-intro) |

## How to use the materials

1. Download or clone this repo, then open the video's folder.
2. Power BI projects are in **PBIP** format (plain-text files). Open the `.pbip` file in Power BI Desktop, then **Refresh**: the sample data loads straight from this repo on GitHub, so there's nothing to point at.
3. Scripts can be copied as-is: TMDL goes into TMDL view, DAX into a measure or DAX query view, notebooks into a Fabric workspace.

## Folder layout

```
videos/
  NN-short-topic/
    README.md        what the video shows, the steps, links
    pbip/            Power BI project (PBIP)
    data/            synthetic sample data
    build_report.py  regenerates the data and the whole PBIP
    scripts/         TMDL / SQL / Python from the video
    dax/             the DAX from the video
    notebooks/       Fabric notebooks (when relevant)
```

## Safe to share

All data here is **synthetic**. Before anything is published, it is scanned and cleaned of accounts, emails, tenant/workspace ids, Fabric/OneLake addresses, connection strings, local paths and keys. If you ever spot something that looks sensitive, please open an issue.

## Find me

- 🎬 YouTube: [@pbi101](https://www.youtube.com/@pbi101)
- 🌐 Consulting: [pbi101.com](https://pbi101.com)
- ✍️ Articles: [Data Ninja AI Lab](https://shai-kr.github.io/data-ninja-ai-lab)
- 💼 LinkedIn: [Shai Karmani](https://www.linkedin.com/in/shai-kr)

Code and samples are under the [MIT license](LICENSE).
