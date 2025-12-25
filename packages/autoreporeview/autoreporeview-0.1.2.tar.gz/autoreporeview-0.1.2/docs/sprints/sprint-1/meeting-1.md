# Meeting Notes

- ### Meeting Date: _07/11/2025_

- ### Meeting Recording: [Link](https://drive.google.com/file/d/1CSEhXdarh2dbiwM_1_hlwVPIL82ShLTn/view?usp=drive_link)

## Meeting Summary

### Interactive Prototype

- The prototype can be a CLI simulation/documentation showing commands being typed and the output printed.

### Plan and Goals

- **Primary Goal:** The tool must summarize the code differences (the _diff_) between commits/versions, explaining what changed without requiring the user to read the raw code diff or switching between versions.

- **Short-Term:** The initial focus is on ensuring the tool works with local Git repositories.

- Integration with GitHub or GitLab APIs is a low-priority future goal.

### Assumptions Disucssion

- **LLM Provider:** The LLM is external and must be configurable (currently the LLM should be Gemini). The team must include an option for the user to provide their own **API key/endpoint**.

- **Input/Output:** The tool interacts with a local Git repository folder, and output is a plain text to the CLI with the option to export to a file.

### Requirements

#### Functional Requirements:

- **Core Summary:** Must provide a summary of **code differences** (not commit messages).

- **LLM Configuration:** Must allow the user to input the LLM API key and endpoint URL.

- **Contributor Analysis:** Future feature to identify the person responsible for a specific change and summarize their other contributions.

- **Command Structure:** Must include a basic `help` command.

#### Quality Requirements:

- Need for a **user warning** if the diff data being sent to the LLM is excessive (e.g., over 50,000 lines/tokens), requiring user confirmation due to potential API costs.

- Strong customer preference for the tool to be written in **Python**.

- We should use modern Python dependency management like **`pyproject.toml`**.

### Constraints

- **LLM Dependency:** The project is dependent on the customer providing their own Gemini LLM access/token.

- **Scope:** Focus is limited to local Git interaction for now.

### High-Level Architecture Draft

An architecture that focuses on four main layers:

1. **Command Layer:** Handles user input via the CLI (e.g., `help`, `summarize`).

2. **Git Interaction / Parser Layer:** Extracts the necessary **diffs** and **contributor metadata** from the local repository.

3. **LLM Service Layer:** Manages API configuration, context size warnings, and makes the `POST` request to the external LLM provider.

4. **Output Layer:** Prints the final, summarized text directly to the CLI console.

## Action Points (Draft)

| General Meeting Outcome                                         | Actionable Item (WHO, WHAT, WHEN)                                                                                                                                                  |
| :-------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| We need to figure out how to demonstrate the CLI tool           | **Team Member** to **Research and select a Python library** suitable for creating the CLI simulation prototype by **The end of sprint-2**.                                         |
| We need a parsing component ready before we can summarize.      | **Team Members** to **Implement the Git parsing layer** to extract and format a simple commit **diff range** from a local repo by **End of sprint-3**.                             |
| We should have the ability to identify contributions by author. | **Team Members** to **Draft mock-up text and logic** for the Contributor Analysis feature, showing how user input would trigger the contributor's summary, by **End of sprint 4**. |
