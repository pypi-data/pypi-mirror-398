# Meeting Script and Notes

## Meeting Questions

### Functional and Non-Functional Requirements

- Does the functional requirements table look good? Should we pay attention to something else at this stage?
- For quality requirements (security, performance, usability, etc.), which aspects matter most currently?
- Should we start on local repo parsing and analysis first, then in the future consider integrations (e.g., GitHub/GitLab APIs)?

### Prototype Plan

- Considering that our plan is a CLI tool, are there any visual elements that you would prefer to have?
- What kind of visual summaries or metrics would you find most useful to see?

### Strategic Plan

- What would you consider a successful first prototype by the end of the current sprint?

### Constraints

- Are there any technical constraints or constraints in general?

### Clarification

- In the assignment high-level architecture section, it asks for an interactive prototype. How should our protoypte look like?

---

## Meeting Taken Notes

- Take open-source project → use tool → see what changes without reading code.
- Goal: avoid manually finding where the version or something changed. Add a possibility to find what other changes this contributor made.
- Ask user what LLM provider to use — must feature.
- Use **Gemini** as default; it should fit most contexts or show a warning about too large changes (e.g., over 50,000 lines).
- For now, create one summary from all commits; in the future, combine changes into related topics and have “summary of summaries.”
- For stack: **Python** if possible, **uv** for versioning.
- Work on **local repos** for now.
- Output: text displayed directly in the CLI.
- Build a **CLI prototype** using some Python/JS library (Denis promised to send some options).
- For prototype: show command and output, include a help section.
- Add command for user to provide LLM provider and key.
