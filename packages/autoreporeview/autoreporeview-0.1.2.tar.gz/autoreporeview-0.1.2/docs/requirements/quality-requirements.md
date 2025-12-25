# Table of contents

1. [Priority matrix](#priority-matrix)
2. [Quality attributes](#quality-attribute)

# Priority matrix <a name="priority-matrix"></a>

| Technical Risk → <br> Business Importance ↓ | `L` | `M`     | `H`         |
| ------------------------------------------- | --- | ------- | ----------- |
| **`L`**                                     | | 003, 004 | 005 |
| **`M`**                                     | | 002 | |
| **`H`**                                     | | 001 | |

# Quality attributes <a name="quality-attribute"></a>

## Performance scenario

### QAS001: Response time

**Source of Stimulus**: User is trying to get the response of the system

**Stumulus**: Request to the system

**Environment**: System under normal load

**Response**: System returns the result of the processing the request

**Response Measure**:

- Process results returned within 30 seconds for 99% of the requests (most of the time LLM will be processing)
- Results are accurate

#### QAST001-1

Steps:

1. User make 10 requests to the system

Expected result: At least 9 out of 10 simultaneous requests should still be able to finish within 30 seconds.

## Maintainability scenarios

### QAS002: Deployment time

**Source of Stimulus**: Developer is trying to deploy the system on machine

**Stimulus**: System deployment

**Environment**: Any machine that supports Docker with at least 2 CPUs and 4 GB of RAM

**Response**: System is deployed

**Response Measure**:

- System is fully deployed within 2 minutes and fully accessible

#### QAST002-1

Steps:

1. Developer starts building and running and system containers

Expected result:

- System is fully deployed within 2 minutes and fully accessible

## Testability scenarios

### QAS003: Automated testing

**Source of stimulus**: Development team

**Stimulus**: System must be tested to make sure it works correctly

**Environment**: Codebase

**Response**: Tests are run and comprehensive feedback is given

**Response Measure**:

Feedback is based on the following criterias:

- All tests should be passed

- Unit test coverage is more than 80%

#### QAST003-1

Steps:

1. Developer tries to merge the feature branch to the main one

Expected result:

Continuous integration gives the feedback based on QAS003 response measure

### QAS004: Integration testing

**Source of Stimulus**: Development team

**Stimulus**: System must be tested in terms of combining all internal components

**Environment**: Development environment

**Response**: System supports integration of all internal components

**Response Measure**:

- Feedback is given based on testing

#### QAST004-1

Steps:

1. Developer runs the integration test

Expected result:

1. System given comprehensive feedback

2. Integration test should be succeeded

## Reliability Scenarios

### QAS005: Data Consistency

**Source of Stimulus**: User is trying to get the summary between 2 Git commits

**Stimulus**: Request to get the summary

**Environment**: System

**Response**: System gets the expected summary from the LLM

**Response Measure**:

1. LLM returns the summary that is expected by system

#### QAST005-1

Steps:

1. Users sends 100 different "diff"s

Expected result:

LLM returns the result in the such structure that is expected by the system

