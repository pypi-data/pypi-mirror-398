## Unit tests

Unit tests are located at `tests/unit`.

How to run unit tests: `uv run tests/unit`

How to adjust the minimum coverage thresholds:
1. Go to `.github/workflows/ci-cd.yml`
2. Go to `test` job
3. Adjust `--cov-fail-under` value

We chose XML coverage report format since its easy to integrate it with other tools.

We chose 80% as a coverage threshold since we should leave some space for code that is hard to test or not important.

We chose services, agent, and CLI modules since they are crucial for user interaction and business logic.

## Quality attribute scenario tests

### QAS001-1

Link: tests/qas_tests/test_qas001.py::test_qas001_1

Implemented: I have done a test that requests system 10 times and allows to only one of them proceed longer that 30 seconds

### QAS001-1

Link: tests/qas_tests/test_qas004.py::test_qas004_1

Implemented: I have done a test that requests system and check that nothing is failed
