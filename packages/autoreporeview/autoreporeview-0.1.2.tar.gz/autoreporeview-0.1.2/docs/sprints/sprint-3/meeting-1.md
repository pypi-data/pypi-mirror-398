# Meeting Notes

- ### Meeting Date: _21/11/2025_

- ### Meeting Recording: [Link](https://drive.google.com/file/d/1AIGsLXJG78d2sGdNKZvWDpyx5DIAMzsp/view?usp=drive_link)

---

## Meeting Summary

The team presented the current progress, including a Swagger-based API prototype for generating summaries from diffs. The customer pointed out that requiring users to run a server would make the CLI harder to use. After discussion, the team decided to remove the API layer entirely and keep the tool as a standalone CLI, ensuring easier setup and the flexibility to switch LLM providers in the future.

We demonstrated the results of manual testing where the LLM generated summaries from diffs, both **with** and **without** repository context. The customer noted that the outputs were nearly identical across both cases.

The customer recommended testing local LLM setups, such as **Ollama** or **Granite**, to reduce token costs and improve reproducibility. For now, he advised keeping the product scope minimal which focuses on summarising changes clearly before implementing additional features.

We also briefly reviewed the backlog and discussed simplifying immediate tasks so the team can progress faster. The overall direction for next week is to simplify the prototype further, consolidate test results, and experiment with a minimal diff-to-summary workflow using a chosen model.

---

## Action Points for Next Week

| General Meeting Outcome                                  | Actionable Item (WHO, WHAT, WHEN)                                                                                          |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Keep the CLI independent and remove the API server       | **Team Members** to update architecture and remove API components by **next weekly meeting**.                              |
| Document LLM test results (diff vs repo-context testing) | **Team Members** to add all test inputs, outputs, and analysis into the repository by **next meeting**.                    |
| Explore local model integration (Ollama/Granite)         | **Team Members** to run initial tests with at least one local LLM and compare behaviour by **end of sprint**.              |
| Simplify short-term roadmap                              | **Team Members** to revise backlog and prioritise minimal working features for summarisation by **next grooming session**. |

---
