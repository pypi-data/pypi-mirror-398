# Tech Stack

## CLI

For the CLI development we decided to use Typer (https://typer.tiangolo.com/) since this is easy-to-use library on Python that allows to build CLIs fast.

## Model

For the connection to the LLM model we decided to use LangChain (https://www.langchain.com/) since this is easy-to-use library for building AI agents.

## Static analysis

### Ruff

[Ruff](https://docs.astral.sh/ruff/) was chosen for its efficiency (written on Rust) and simplicity. It works as both linter and formatter.

### Mypy

[Mypy](https://github.com/python/mypy) was chosen for its proven reliability in type check.

## Testing

### Pytest

[Pytest](https://docs.pytest.org/en/stable/) was chosed for its easiness to use and fixtures functionality.

## Analytics

We use Grafana since this instrument allows to easily do the analytics for any application.

### Observability

We use OpenTelemetry since this is powerful tool that also is easy to install. Specifically, now we can see which methods take the time.
