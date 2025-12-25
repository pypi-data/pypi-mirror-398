# Context Diagram

```mermaid

graph TD
    subgraph "System"
        CLI
        Model
        API
    end

    subgraph "External Actors"
        User
    end

    User -->|Give 2 commits and get the summary| CLI
    CLI -->|Ask for summary based on 2 given commits| API
    API -->|Ask for summary based on 2 given commits| Model

    Model -->|Give the result| API
    API -->|Postprocess the result and return it as a response to client| CLI
    CLI -->|Print the result| User
```

## External Actors

| Actor | Description |
|---|---|
|User|An individual that uses this project|
|CLI|A program that is used by user in terminal to interact with the system|
|API|A program that is used by CLI to use core of the system|
|LLM model|An LLM model that gives the summary of changes between 2 commits|

# Use Case Diagram

```mermaid
graph TD
    User -->|help| CLI
    CLI -->|give all possible operations| User
```

```mermaid
graph TD
    User -->|give 2 commits| CLI
    CLI -->|give a summary of diff| API
    API -->|give a summary of diff using a specific model| Model
    Model -->|return the result| API
    API -->|preprocess result and return it| CLI
    CLI -->|print the result| User
```

# Component Diagram

```mermaid
graph TD
    CLI --> API
    API --> Model
    Model --> API
    API --> CLI
```

| Components | Description |
|---|---|
|CLI|A program that is used by user in terminal to interact with the system|
|API|A program that is used by CLI to use core of the system|
|LLM model|An LLM model that gives the summary of changes between 2 commits|

# Sequence Diagram

## User story PBI-004

As a code reviewer, I want an AI-generated summary of each commit posted as a PR comment so that I can quickly understand changes without reading full diff

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant API
    participant Model

User ->> CLI: Give 2 commits
CLI ->> API: Give the diff of 2 commits
API ->> Model: Preprocess the input and give the diff to model
Model ->> API: Return the result
API ->> CLI: Preprocess the result and return it
CLI ->> User: Return the result
```

### Test

Steps:

1. User gives 2 commits and he/she wants to know the summary of diff between them.

Expected result: system gives comprehensive summary about the changes between 2 commits

## User story PBI-013

Add error handling and retry logic

```mermaid
sequenceDiagram
    participant User
    participant CLI

User ->> CLI: Give 2 commits
CLI ->> User: Fail to fetch diff between 2 commits due to Git error, return the error message
```

### Test

Steps:

1. User gives 2 not existing commits.

Expected result: system gives comprehensive error.

