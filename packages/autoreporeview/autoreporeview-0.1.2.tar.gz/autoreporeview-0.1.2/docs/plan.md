# AutoRepoReview – Strategic Plan

## Project Goals
Develop a lightweight, AI-powered CLI tool that:
- Summarizes **single-file GitHub commit diffs** using an LLM.
- Outputs **clear, human-readable summaries** of what changed and why.
- Runs locally or via simple command-line input.
- Supports **Python and JavaScript** (primary focus).

> *Ambitious but achievable within the course timeline: focus on core summarization, not full repo analysis.*

---

## Threshold of Success (SMART Goals)

| Criteria | Target |
|--------|--------|
| **Specific** | Summarize single-file commits from public GitHub repos |
| **Measurable** | ≥80% of 10 test commits are accurately summarized (manual review) |
| **Achievable** | Use existing LLM APIs (e.g., OpenAI, Ollama) + GitHub API |
| **Relevant** | Delivers working MVP with CLI interface |
| **Time-bound** | Fully functional by **final course deadline** |

Success = CLI tool that:
1. Takes a GitHub commit URL
2. Fetches diff
3. Returns a summary in <60 seconds
4. Works on Linux/macOS via `pip install`
5. Diff can be taken either by providing 2 commits, or by specifying time range.

---

## Feature Roadmap

### Implemented
- [x] Fetch commit diff via GitHub API
- [x] Basic prompt engineering for LLM summarization
- [x] CLI command: `autoreporeview summarize <commit-url>`
- [x] Unit tests for diff parsing and CLI

### In Progress
- [ ] Improve summary clarity (change type, impact, components)
- [ ] Add error handling (rate limits, invalid URLs)
- [ ] Support local `.diff` files as input

### Planned (MVP Scope)
- [ ] Config file for API keys and model selection
- [ ] Output formatting: plain text + optional JSON

### Future (Post-MVP)
- [ ] Multi-file commit support
- [ ] PDF report export
- [ ] Contributor pattern analysis

---

## Progress Monitoring

We track progress weekly using:
- **GitHub Project Board** (Kanban):
  - Columns: `Backlog → To Do → In Progress → Review → Done`
  - All tasks linked to issues
- **Weekly Check-ins** (15 mins):
  - What was completed?
  - Blockers?
  - Next steps?
- **MVP Milestone**:
  - Tagged in GitHub: `mvp-v1.0`
  - Must include working CLI + 3 example summaries
- **Demo Readiness**:
  - Record 2-minute demo video by **Week 10**

> *Success = MVP demo works end-to-end on at least 3 real commits.*

---

## Contingency Plans

| Risk | Contingency |
|------|-------------|
| **LLM API rate limits or cost** | Fall back to **Ollama** (local LLM) or pre-generate summaries for demo |
| **GitHub API authentication issues** | Use **unauthenticated public endpoint** + cache sample diffs |
| **Summaries are vague or incorrect** | Manually refine 1–2 prompts; add few-shot examples |
| **Team member unavailable** | Cross-train on CLI + API calls; keep tasks <4 hours each |
| **Time running out** | Cut non-essential output (no JSON/PDF); focus on **CLI + 1 language** |

> *MVP fallback*: Ship with **3 pre-summarized commits** if live API fails during demo.

---

*Last updated: December 13, 2025*
