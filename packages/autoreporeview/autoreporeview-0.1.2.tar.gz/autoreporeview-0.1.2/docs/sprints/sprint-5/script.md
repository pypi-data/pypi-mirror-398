# Meeting Script

## Prepared Questions

- What’s your feedback on the current list of commands?

- What’s your feedback on the current response output?

- With Grafana, what should we focus on monitoring in the project?

- What value moment metrics would you suggest for the prodcuct?

- What’s the updated scope of the MVP?

## Taken Down Notes

- Improvement Suggestion: Ask the user for a file path and the storage location of tokens and configurations.

- Output Size: The current output is too large Experiment with different prompts to make it shorter.

- More detailed information about the changes (e.g., if the output says "refactoring...", more specifics are needed).

- Formatting Suggestion: Make the output formatting use Markdown (MD).

- **Main Priorities Now:**

  - Make the output smaller.

  - Experiment with different prompts.

- Actionable Example: We can use another team's GitHub account to see their changes between two iterations.

- **Prompt Options:** Have multiple prompt options for the user to choose from (e.g., an option to show documentation change, or an option to show features change).

- Analytics Examples:

  - What kind of commands did the user use (store the user request).

  - If there is an error, show that error.

  - How long did the responses take.

- **Value Moment** example: is when the LLM is able to understand the customer's summary intent (the things the customer wants to see) that the LLM currently doesn't know what it is. (This point can be achieved by experimenting with prompts).

- Less Prioritized Items:

  - The current list of commands is fine, but it would be helpful to have a better way to find commits instead of copying IDs from logs. For example, by using commit comments where the user fills in a partial description and the CLI gives commit suggestions.

  - Potential Feature: Specific outputs to highlight features that might break compatibility in the diff summary.

  - Feature Suggestion: If the CLI is given only one commit, it should default to comparing that commit with the most recent one.
