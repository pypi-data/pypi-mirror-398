# Meeting Summary

- ### Meeting Date: *31/10/2025*

- ### Meeting Recording: [Link](https://drive.google.com/drive/folders/1Z7a76QOU7bgvV4x0Ukmrn_hn37ecI4Gb)

## Purpose and Problem

Discuss building a tool to summarize code changes in open-source repos and provide contribution metrics (who changed what, churn, unchanged lines). Current diffs and commit messages are hard to trust or quickly understand, so a simple summary explaining changes (e.g., “added ability to add private key… why?”) is needed.

## Major Discussed Topics

### Desired Outputs and Implementation Ideas

- Natural-language summaries of code diffs plus metrics like churn, recent contributors, and stable vs. frequently changed modules.
- Start with a CLI interface for ease of installation on Linux and local usage.
- Allow users to supply their own LM endpoint/token for privacy and security.
- Optionally add a dashboard or “wall screen” later for visual highlights.

### Data Sources, Scope, and Priorities

- Begin with local git clones; integrate GitHub/GitLab APIs in future iterations.
- Focus first on generating summaries and basic metrics; visualization and deep integrations come later.

### Course Delivery, Assessment, and Timeline

- The project should be open-source to facilitate demos and inspection.
- Deliverables include repo contents plus consolidated PDFs (docs, meeting notes, peer reviews) uploaded to Moodle—external links are not sufficient.
- Weekly progress check-ins preferred; timeline of about eight weeks.

### Decisions, Risks, and Next Steps

- Build a prototype focusing on text summaries and metrics with CLI interface.
- Support local LM endpoints/tokens to avoid managing credentials.
- Ensure CLI is easy to install and stable.
- Schedule regular weekly offline meetings or through Telegram

---
