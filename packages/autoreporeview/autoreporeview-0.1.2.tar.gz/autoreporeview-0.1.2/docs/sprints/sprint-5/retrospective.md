# Sprint Retrospective

## What Went Well

1. Our team improved the CLI model-configuration flow, allowing users to plug in any OpenAI-compatible model with minimal setup.

2. Feedback from the customer helped clarify how summaries should focus on user intent (e.g., new features, breaking changes), giving us a clearer direction for prompt experimentation.

3. Our team refined the product scope by identifying simple, meaningful analytics to collect (requests, errors, timings), making future evaluation more structured.

---

## Problems Encountered & Root Causes

### 1. Summaries Too Noisy

- **Root cause:** Current prompts try to cover all change types at once, leading to verbose and unfocused outputs.
- **Status:** Partially addressed. Our team discussed introducing intent-specific prompts but has not yet implemented them.

### 2. Commit Selection Still Unintuitive for Users

- **Root cause:** Users must manually inspect git logs and copy hashes; the CLI offers no assistance in finding commits.
- **Status:** Identified solutions (search by comment, “latest vs X”), but they are not yet implemented.

### 3. Difficulty Identifying Clear Value Metrics

- **Root cause:** The project has many possible use cases, and our team has not yet captured real usage data to validate assumptions.
- **Status:** Customer clarified minimal analytics needed. The implementation is done in this sprint.

---

## Changes for Next Sprint

### **High Impact**

1. **Implement intent-specific prompt modes** (e.g., new features only, breaking changes, documentation mismatches) to improve summary usefulness.
2. **Add basic analytics logging** (command input, response, duration, errors) to support hypothesis-driven development.
3. **Prompt experimentation** to cover output issues or improvements (related to the first change).

### **Medium Impact**

3. **Add “latest vs X” comparison mode** to simplify commit selection for users.

### **Low Impact**

4. **Experiment with markdown-friendly CLI rendering** to improve output readability.
