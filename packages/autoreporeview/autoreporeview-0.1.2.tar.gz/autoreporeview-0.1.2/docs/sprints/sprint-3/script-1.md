# Meeting Script

## Prepared Questions

- What's your suggestions for the current prototype?

- What is your feedback on the the manual diff-based summaries?

- Are there recommendations for future changes to the current CLI approach?

- Should we continue with cloud models for evalution or do we consider local models?

- Which features are the short-term priorities ??

## Notes

- Demonstrated Swagger endpoint for generating summaries.
- Customer highlighted that requiring users to run a server complicates CLI setup.
- Agreed to keep the CLI independent of backend/API to allow easy model swapping.
- Presented manual tests comparing summaries with vs. without repo link context.
- Results were nearly identical; customer requested adding these test cases + outputs to the repository.
- Customer recommended experimenting with local models (Ollama, Granite).
- Agreed to keep the project simple: focus on basic summary-of-changes functionality.
