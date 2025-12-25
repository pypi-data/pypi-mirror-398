# Meeting Notes

- ### Meeting Date: _14/11/2025_

- ### Meeting Recording: [Link](https://drive.google.com/file/d/1sfVLEy6ue7QoULxfvKbZ2MnD6YMbbNKG/view?usp=drive_link)

## Meeting Summary

The team demonstrated the initial prototype, showing how UV currently runs the script and explaining that the tool is intended to summarise changes between commits. The customer (also from his perspective as a developer) suggested improving usability by allowing the CLI to run without explicitly typing `uv run`, enabling a cleaner interface such as `./cli <command>`.

A major part of the discussion focused on how to obtain and summarise diffs. The customer emphasised that before involving an LLM, the tool must be able to:

1. Retrieve files that have changed between two points in time (e.g., using a date or commit reference).
2. Package those files into a “context file” for later LLM processing.
3. Experiment with different approaches:
   - Sending full file versions to the LLM.
   - Sending git diff lines only.
   - Comparing which yields better summaries.

We discussed potential limitations with large diffs and file sizes. We agreed on applying safeguards such as token/line limits (e.g., warning at ~10,000 tokens) before sending content to the LLM. The customer confirmed that users will supply their own Gemini or other LLM provider tokens, which the tool will save locally and use for API calls.

On backlog structure, the customer introduced backlog grooming practices: ordering smaller, clearer tasks at the top, splitting large unclear tasks, and using relative estimation (small/medium/large before translating to story points). He suggested reorganising the backlog to become more actionable and to reflect realistic development priorities.

Finally, the customer outlined next-week directions: manually test LLM summarisation by giving it diffs or pairs of Python files, evaluate which approach produces the most meaningful summaries, and explore whether providing additional examples or context improves responses. The goal for next week is to validate assumptions about how the LLM handles diff data and to identify what kind of input leads to high-quality change summaries.

---

## Action Points for Next Week

| General Meeting Outcome                                                             | Actionable Item (WHO, WHAT, WHEN)                                                                                                                                                               |
| :---------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| We need to test whether LLMs can summarise diffs effectively.                       | **Team Members** to **Run manual experiments** by providing both raw Git diffs and full-file inputs to an LLM, then **evaluate summary quality**, by **next weekly meeting**.                   |
| We need to understand input-size limitations when sending context to LLMs.          | **Team Members** to **Measure token sizes** of sample diffs and full-file inputs and **define initial safe token limits** (e.g., ~10k tokens) by **next sprint planning**.                      |
| We need an early validation of the future CLI workflow (diff → context → LLM call). | **Team Members** to **Prototype simple CLI commands** (e.g., list-changed-files-since-date) without LLM integration yet, by **end of upcoming sprint**.                                         |
| The backlog requires grooming and better task sizing before future iterations.      | **Team Members** to **Refine the product backlog** by re-evaluating story points and splitting large items into smaller tasks, ensuring top items are actionable, by **next grooming session**. |

---

