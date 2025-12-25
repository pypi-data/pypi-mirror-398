# Meeting Notes

- ### Meeting Date: _5/12/2025_

- ### Meeting Recording: [Link](https://drive.google.com/file/d/1n4kdSzdpVg8T2kN9L3cO1Qjyn96nTI0r/view?usp=drive_link)

---

## Meeting Summary

Our team demonstrated recent improvements to the CLI, including support for configuring any OpenAI-compatible model and ongoing work toward PyPI distribution. The customer confirmed that this model-configuration approach is convenient and aligns with expectations.

A major part of the discussion focused on improving the **quality and usefulness of the generated summaries**. The current outputs are not specific enough and not-telling, especially for commits that are close together. The customer recommended experimenting with alternative prompts that prioritise:
- New features  
- Deprecated/removed functionality  
- Breaking changes  
- High-level changes only  

He also encouraged providing multiple prompting modes based on different user intents.

The customer explained that **CLI and API are conceptually equivalent**, meaning the CLI should be fully testable just like an API. This reinforces the importance of maintaining strong tests for commands, error cases, and malformed input.

Another key conversation topic was improving the **commit-selection workflow**. Instead of asking users to manually copy commit hashes from `git log`, the customer suggested:
- A "latest vs X" comparison mode  
- Searching commits by comment text  
- Using the LLM to filter logs for matching commits  

Finally, we discussed **analytics and value metrics**. Grafana is optional; the real requirement is collecting basic usage data such as command inputs, errors, response times, and outputs. This supports a hypothesis-driven approach for evaluating how users interact with the tool and which prompts or features create real value.

---

## Action Points for Next Iteration

| General Meeting Outcome                                         | Actionable Item (WHO, WHAT, WHEN)                                                                                                 |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Improve summary quality with new prompt variations              | **Team Members** to design and test multiple prompt templates (new features only, breaking changes, doc deltas) by **next meeting**. |
| Add simple analytics/logging                                    | **Team Members** to record command usage, responses, timing, and errors.                  |
| Enhance commit-selection workflow                               | **Team Members** to implement "latest vs X" mode and investigate LM-assisted commit search by **next weekly meeting**.            |           |
| Document prompting hypotheses and user intent modes             | **Team Members** to summarise identified user intents and associated prompts in the docs.
---

## Meeting Speakers

- **Speaker 1:** The Customer 
- **Speaker 2:** Alyona Artemova
- **Speaker 3:** Ghadeer Akleh