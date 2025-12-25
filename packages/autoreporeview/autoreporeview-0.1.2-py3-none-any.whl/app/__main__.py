from datetime import datetime
import getpass

import typer
from opentelemetry import trace
from rich.console import Console
from rich.markdown import Markdown

from .config import config
from .services.git_service import GitService
from .services.summarize_service import SummarizeService, SummaryMode
from .telemetry import setup_telemetry

# Initialize telemetry
setup_telemetry()

tracer = trace.get_tracer(__name__)

app = typer.Typer()
console = Console()

git_service = GitService()


def prompt_for_summary_mode() -> SummaryMode:
    """Prompt the user to select a summary mode interactively."""
    console.print("\n[bold cyan]Choose diff summary prompt:[/bold cyan]\n")

    options = [
        ("1", "General summary", "blue"),
        ("2", "Documentation changes", "green"),
        ("3", "Features add/removed", "yellow"),
        ("4", "Breaking changes", "red"),
    ]

    for num, desc, color in options:
        console.print(f"  [bold {color}]{num}.[/bold {color}] [bold]{desc}[/bold]")

    console.print()

    while True:
        choice = typer.prompt("\nEnter your choice (1-4)", default="1")
        try:
            choice_num = int(choice)
            if choice_num == 1:
                return SummaryMode.GENERAL
            elif choice_num == 2:
                return SummaryMode.DOCUMENTATION
            elif choice_num == 3:
                return SummaryMode.FEATURES
            elif choice_num == 4:
                return SummaryMode.BREAKING_CHANGES
            else:
                console.print(
                    "[bold red]✗[/bold red] Invalid choice. Please enter a number between 1 and 4."
                )
        except ValueError:
            console.print(
                "[bold red]✗[/bold red] Invalid input. Please enter a number between 1 and 4."
            )


@app.command()
def summary(
    path: str,
    start_commit: str,
    end_commit: str,
    contributors: bool = typer.Option(
        False,
        "--contributors",
        "-c",
        help="Include contributors information in the summary",
    ),
) -> None:
    """Creates a summary of changes between two commits."""
    with tracer.start_as_current_span("summary_command") as span:
        span.set_attribute("path", path)
        span.set_attribute("start_commit", start_commit)
        span.set_attribute("end_commit", end_commit)

        summarize_service = SummarizeService()
        try:
            with tracer.start_as_current_span("get_diff"):
                diff = git_service.get_diff(path, start_commit, end_commit)

            contributors_info = None
            if contributors:
                contributors_info = git_service.get_contributors_by_commits(
                    path, start_commit, end_commit
                )

            summary_mode = prompt_for_summary_mode()

            token_count = summarize_service.get_token_count(
                diff, contributors_info, summary_mode
            )
            typer.echo(f"\nEstimated input token count: {token_count}", err=True)

            if not typer.confirm(
                "Do you want to proceed with summarization?", default=True
            ):
                typer.echo("Summarization cancelled by user.", err=True)
                raise typer.Exit(0)

            with tracer.start_as_current_span("summarize") as summarize_span:
                summarize_span.set_attribute("token_count", token_count)
                summarize_span.set_attribute("summary_mode", summary_mode.value)
                result = summarize_service.summarize(
                    diff, contributors_info, summary_mode
                )
                console.print("\n")
                console.print(Markdown(result))
                span.set_attribute("summary_length", len(result))
        except ValueError as e:
            typer.echo(f"Configuration error: {e}", err=True)
            raise typer.Exit(1)
        except ConnectionError as e:
            typer.echo(f"Connection error: {e}", err=True)
            raise typer.Exit(1)
        except RuntimeError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            raise typer.Exit(1)


@app.command()
def summary_by_time(
    path: str,
    start_time: datetime,
    end_time: datetime,
    contributors: bool = typer.Option(
        False,
        "--contributors",
        "-c",
        help="Include contributors information in the summary",
    ),
) -> None:
    """Creates a summary of changes between two datetimes."""

    diff = git_service.get_diff_by_time(path, start_time, end_time)

    contributors_info = None
    if contributors:
        contributors_info = git_service.get_contributors_by_time(
            path, start_time, end_time
        )

    summarize_service = SummarizeService()

    summary_mode = prompt_for_summary_mode()

    token_count = summarize_service.get_token_count(
        diff, contributors_info, summary_mode
    )
    typer.echo(f"\nEstimated input token count: {token_count}", err=True)

    if not typer.confirm("Do you want to proceed with summarization?", default=True):
        typer.echo("Summarization cancelled by user.", err=True)
        raise typer.Exit(0)

    result = summarize_service.summarize(diff, contributors_info, summary_mode)
    console.print("\n")
    console.print(Markdown(result))


@app.command()
def configure(
    api_url: str = typer.Option(
        ...,
        prompt="API URL",
        help="API URL (e.g., https://api.openai.com/v1)",
    ),
    model_name: str = typer.Option(
        "",
        prompt="Model name (optional)",
        help="Specific model name (e.g., gpt-4)",
    ),
) -> None:
    """Configures the API model and securely saves the key."""
    api_key = getpass.getpass("Enter API key: ")

    if not api_key:
        typer.echo("Error: API key cannot be empty", err=True)
        raise typer.Exit(1)

    try:
        config.set_model_config(api_url, api_key, model_name)
        typer.echo("Configuration saved successfully!")
    except Exception as e:
        typer.echo(f"Error saving configuration: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def show_config() -> None:
    """Shows the current model configuration."""
    model_config = config.get_model_config()
    if model_config is None:
        typer.echo("Model is not configured. Use the 'configure' command to set up.")
        return

    typer.echo(f"API URL: {model_config['api_url']}")
    if model_config.get("model_name"):
        typer.echo(f"Model name: {model_config['model_name']}")


if __name__ == "__main__":
    app()
