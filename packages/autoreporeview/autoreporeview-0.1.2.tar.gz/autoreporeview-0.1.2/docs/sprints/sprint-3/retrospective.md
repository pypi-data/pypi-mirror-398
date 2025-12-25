# Sprint 3 – Retrospective

## What Went Well

1. The research on the impact of context on diff summary quality was shared with the customer. Despite the summary quality being similar with or without context and currently not very good without preprocessing, the customer appreciated the findings as valuable for future work.
2. The team decided to simplify the CLI tool by having it directly interact with the language model instead of building a separate API layer. This change was made to improve usability, avoiding the need to run an additional server.
3. The first Minimum Viable Product was completed successfully, enabling users to install and run the CLI tool using provided instructions.

---

## Problems Encountered & Root Causes

#### 1. Token Limit Challenge with Large Code Diffs  
   - **Root cause:** Code diffs often exceed the 10,000 token limit, making it hard to process full diffs without truncation or preprocessing.  
   - **Solution:** Currently analyzing and working only with small commits that fit within the token limits as a temporary workaround. Researching and planning implementation of preprocessing techniques such as truncation, chunking, and optimization of inputs for future sprints to mitigate this fundamental issue.

#### 2. Model Usage Cost and Quality Concerns  
   - **Root cause:** Running out of free tokens limits usage; local model alternatives are considered but feared to be less capable, risking summary quality degradation.  
   - **Solution:** Planning to search for local models or other free language model options to reduce token cost without sacrificing quality. Customer suggested local model hosting (e.g., Ollama, Granite), but the team is cautious and will evaluate carefully.

#### 3. Architectural Shift in CLI and API Design  
   - **Root cause:** Initial plan to develop an API to decouple CLI from the LLM model was changed to simplify usage by allowing CLI to interact directly with the model, which may reduce flexibility.  
   - **Solution:** This change was implemented to improve simplicity and user experience by avoiding having to run a server. Documentation is maintained to track this decision, with openness to revisit if needed.

---

## Changes for Next Sprint (Prioritised)

#### **High Impact**

1. Develop and integrate a preprocessing pipeline to reduce code diff size while preserving essential content.

#### **Medium Impact**

2. Evaluate alternative language models or local model hosting solutions to address token usage costs without sacrificing summary quality.

#### **Low Impact**

3. Implement internal logging of tokens consumed per request, including prompt and completion tokens. Use these insights to improve prompt efficiency and manage model usage costs without hard enforcement of limits.

