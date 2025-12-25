# Design decisions

| Driver | Decision | Rationale | Discarded Alternatives |
|--------|----------|-----------|------------------------|
| QA-1: Deployability | Use Docker to deployment | Fast deployment | Writing custom shell script to run application |
| CRN-1: Model independence | System should not depend on LLM | This architecture allows to switch models easily | Being tied to a specific models |
| QA-2: Reliability | Make model return the consistent results | It allows to make sure that data will be collected correctly | - |
| QA-3: Testability | Do unit testing | It makes sure that system works as expected | Manual testing |
| QA-4: Monitorability | Do proper logging | It allows to monitor system easily | Debugging |

