# Meeting Script

## Prepared Questions

- What do you think about the prototype?
- Will payment be through an inputted Gemini token?
- Should we have a context file before we send to LLM?
- How do we handle large diffs?
- Does the product backlog look valid to use
- What should we have ready for next week? (further steps)

## Taken Notes
- With UV you can have a script that can simulate the environment without using uv (reduce command)
- Using an LLM: here is file a and here is file b and show me the difference.
- We can build a first step by using a command that fetches all the files that changed in a specific period or by using dates.
- We use the fetched information to build a context file that we can later send to the LLM
- Initial task (manual testing without CLI): Using python build two versions of a file and see how can the LLM summarise the diff.
- Large files: check number of lines/tokens before sending to LLM (up to 10000 token) and we get a warning exceeding it.
- We take a workable token from the user and store it locally to use
- Product backlog feedback: Grooming backlog
Another direction for our project: research summarization methods (more LLM related)