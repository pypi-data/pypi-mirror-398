# Sprint Retrospective

## What Went Well

1. **Prototype demonstration was clear and functional** – The customer understood the current behaviour and was able to give actionable feedback.
2. **Valuable technical guidance from the customer** – The customer provided concrete next steps (diff-first workflow, context packaging, token size limits, backlog grooming).
3. **Team alignment improved** – The meeting clarified responsibilities and the logical order of development steps (diff → context → LLM experiments).

---

## Problems Encountered & Root Causes

#### 1. Unclear approach to handling diffs vs full files

- **Root cause:** Assumptions were made without experimentation; team hadn’t validated LLM behaviour on diffs vs full-file context.
- **Impact:** Development stalled because it was unclear how to design prompts and context packaging.

#### 2. Backlog lacked grooming and coherent prioritisation

- **Root cause:** Story points were assigned intuitively without relative sizing; the backlog wasn’t sorted by complexity or readiness.
- **Impact:** Harder to select appropriate tasks for the sprint; long-term tasks were mixed with near-term ones.

---

## Changes for Next Sprint (Prioritised)

#### **High Impact**

1. **Perform hands-on experiments with diffs and full files using LLMs**
   - Compare outputs on 2–3 test cases.
   - Establish what “good summary” means using real examples.

#### **Medium Impact**

2. **Define the initial CLI command structure**

   - Draft commands such as `cli changes-since`, `cli ask`, `cli diff`.

3. **Set an internal token usage limit and warning system**
   - Apply a temporary personal token or free-tier LLM with mindful usage.
   - Add a limit (e.g., 10k–20k tokens).

#### **Low Impact**

4. **Introduce backlog grooming sessions before sprint planning**
   - Sort tasks by clarity and size (small → medium → large).
   - Apply relative story points only after grouping.

---
