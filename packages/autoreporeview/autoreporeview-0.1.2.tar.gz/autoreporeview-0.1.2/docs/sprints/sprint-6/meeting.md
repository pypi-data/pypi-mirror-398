# Meeting Notes

- ### Meeting Date: _12/12/2025_

- ### Meeting Recording: [Link](https://drive.google.com/file/d/1l6vS2fqlZ_rM-bQ39rt7C-BgA5VWuGVk/view?usp=drive_link)

---

## Meeting Summary

Our team demonstrated recent improvements to the CLI tool, focusing on **token estimation before summarisation** and **clearer, more compact summary output**. The customer appreciated the ability to preview estimated input token usage before sending data to the LLM, noting that this shifts responsibility and control to the user when handling large diffs.

Our team confirmed that **Gemini** remains the default LLM, while still supporting alternative OpenAI-compatible models as shown in previous weeks. Formatting improvements to the summary output (highlighting files, functions, and structured sections) were positively received.

A key discussion point was **summary content and intent**. The customer explicitly stated that summaries should include **who made the changes**, highlighting the importance of showing **contributors** directly in the summary output. This was seen as an essential part of understanding changes, especially when reviewing work done by multiple people.

The customer reiterated interest in having summaries tailored to specific questions, such as:

- What was added vs deleted
- What functionality changed
- What documentation was updated

Related to this, the customer suggested improving **commit selection** by allowing users to specify **date ranges** (e.g., “last week”, “last month” or between two dates) instead of commit hashes. He also proposed using the LLM itself to interpret natural-language time ranges or intents, making the CLI more user-friendly.

Our team raised concerns about large contexts when using date ranges, but the customer agreed this is acceptable as long as token estimation and user confirmation are in place.

Finally, outside the core product discussion, the customer suggested using the tool to **summarise another team’s project and write a short report**. This would both demonstrate real-world usability and help improve grading by showing applied analysis. This was noted as a course-related recommendation rather than a product requirement.

---

## Action Points for Next Week

| General Meeting Outcome                  | Actionable Item (WHO, WHAT, WHEN)                                                                                   |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Include contributor information          | **Our team** to **add contributor details to summaries** (who made the changes) by **next sprint**.                 |
| Make commit selection more user-friendly | **Our team** to **implement date-range based diff selection** (e.g., last week/month) by **next sprint**.           |
| Improve summary relevance                | **Our team** to **introduce intent-based summaries** (e.g., added, deleted, documentation-only) by **next sprint**. |

---

## Meeting Speakers

- **Speaker 1:** The Customer
- **Speaker 2:** Alyona Artemova
- **Speaker 3:** Ghadeer Akleh
- **Speaker 4:** Ilnar Khasanov
