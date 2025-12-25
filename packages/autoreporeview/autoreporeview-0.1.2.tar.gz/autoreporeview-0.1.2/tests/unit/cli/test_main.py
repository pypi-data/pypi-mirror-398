from unittest.mock import Mock, patch

import pytest
from pytest import CaptureFixture
import typer
from rich.markdown import Markdown
from datetime import datetime

from app import __main__ as main
from app.services.summarize_service import SummaryMode


def test_summary_function_prints_changes(capsys: CaptureFixture[str]) -> None:
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.return_value = "Test summary"
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    try:
        with (
            patch("app.__main__.git_service", mock_git_service),
            patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
            patch("app.__main__.typer.confirm", return_value=True),
            patch("app.__main__.console.print"),
            patch(
                "app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL
            ),
        ):
            main.summary("path", "commitA", "commitB")
    except typer.Exit as e:
        # If exit code is 0, that's fine (user cancelled)
        # If exit code is 1, something went wrong
        if e.exit_code != 0:
            raise
    captured = capsys.readouterr()
    assert type(captured.out) is str
    # Verify summarize was called with the diff as first argument
    mock_summarize_service.summarize.assert_called_once()
    call_args = mock_summarize_service.summarize.call_args
    assert call_args[0][0] == "test diff"
    assert call_args[0][2] == SummaryMode.GENERAL  # mode parameter


def test_summary_with_contributors_calls_get_contributors(
    capsys: CaptureFixture[str],
) -> None:
    """Test that get_contributors is called when contributors flag is True."""
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.return_value = "Test summary with contributors"
    mock_summarize_service.get_token_count.return_value = 150
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"
    mock_git_service.get_contributors_by_commits.return_value = (
        "- Alice: 2 commit(s)\n- Bob: 1 commit(s)"
    )

    try:
        with (
            patch("app.__main__.git_service", mock_git_service),
            patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
            patch("app.__main__.typer.confirm", return_value=True),
            patch("app.__main__.console.print"),
            patch(
                "app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL
            ),
        ):
            main.summary("path", "commitA", "commitB", contributors=True)
    except typer.Exit as e:
        if e.exit_code != 0:
            raise

    # Verify get_contributors was called
    mock_git_service.get_contributors_by_commits.assert_called_once_with(
        "path", "commitA", "commitB"
    )

    # Verify get_token_count was called with contributors_info and mode
    mock_summarize_service.get_token_count.assert_called_once()
    token_call_args = mock_summarize_service.get_token_count.call_args
    assert token_call_args[0][0] == "test diff"
    assert token_call_args[0][1] == "- Alice: 2 commit(s)\n- Bob: 1 commit(s)"
    assert token_call_args[0][2] == SummaryMode.GENERAL  # mode parameter

    # Verify summarize was called with contributors_info and mode
    mock_summarize_service.summarize.assert_called_once()
    summarize_call_args = mock_summarize_service.summarize.call_args
    assert summarize_call_args[0][0] == "test diff"
    assert summarize_call_args[0][1] == "- Alice: 2 commit(s)\n- Bob: 1 commit(s)"
    assert summarize_call_args[0][2] == SummaryMode.GENERAL  # mode parameter


def test_summary_without_contributors_does_not_call_get_contributors(
    capsys: CaptureFixture[str],
) -> None:
    """Test that get_contributors is not called when contributors flag is False."""
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.return_value = "Test summary"
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    try:
        with (
            patch("app.__main__.git_service", mock_git_service),
            patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
            patch("app.__main__.typer.confirm", return_value=True),
            patch("app.__main__.console.print"),
            patch(
                "app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL
            ),
        ):
            main.summary("path", "commitA", "commitB", contributors=False)
    except typer.Exit as e:
        if e.exit_code != 0:
            raise

    # Verify get_contributors was not called
    mock_git_service.get_contributors_by_commits.assert_not_called()

    # Verify get_token_count was called with None for contributors_info and mode
    mock_summarize_service.get_token_count.assert_called_once()
    token_call_args = mock_summarize_service.get_token_count.call_args
    assert token_call_args[0][0] == "test diff"
    assert token_call_args[0][1] is None
    assert token_call_args[0][2] == SummaryMode.GENERAL  # mode parameter

    # Verify summarize was called with None for contributors_info and mode
    mock_summarize_service.summarize.assert_called_once()
    summarize_call_args = mock_summarize_service.summarize.call_args
    assert summarize_call_args[0][0] == "test diff"
    assert summarize_call_args[0][1] is None
    assert summarize_call_args[0][2] == SummaryMode.GENERAL  # mode parameter


def test_summary_prints_markdown_output(capsys: CaptureFixture[str]) -> None:
    """Test that console.print is called with Markdown object."""
    mock_summarize_service = Mock()
    summary_text = "# Summary\n\nThis is a **test** summary."
    mock_summarize_service.summarize.return_value = summary_text
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    try:
        with (
            patch("app.__main__.git_service", mock_git_service),
            patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
            patch("app.__main__.typer.confirm", return_value=True),
            patch("app.__main__.console.print") as mock_console_print,
            patch(
                "app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL
            ),
        ):
            main.summary("path", "commitA", "commitB")
    except typer.Exit as e:
        if e.exit_code != 0:
            raise

    # Verify console.print was called multiple times (newline, prompt display, newline, Markdown)
    assert mock_console_print.call_count >= 2

    # Find the Markdown call
    markdown_call = None
    for call in mock_console_print.call_args_list:
        if len(call[0]) > 0 and isinstance(call[0][0], Markdown):
            markdown_call = call
            break

    assert markdown_call is not None, "Markdown object should be printed"
    assert markdown_call[0][0].markup == summary_text


def test_summary_handles_value_error(capsys: CaptureFixture[str]) -> None:
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.side_effect = ValueError("Config error")
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    with (
        patch("app.__main__.git_service", mock_git_service),
        patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
        patch("app.__main__.typer.confirm", return_value=True),
        patch("app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL),
        pytest.raises(typer.Exit) as exc_info,
    ):
        main.summary("path", "commitA", "commitB")

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Configuration error: Config error" in captured.err


def test_summary_handles_connection_error(capsys: CaptureFixture[str]) -> None:
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.side_effect = ConnectionError("Connection failed")
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    with (
        patch("app.__main__.git_service", mock_git_service),
        patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
        patch("app.__main__.typer.confirm", return_value=True),
        patch("app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL),
        pytest.raises(typer.Exit) as exc_info,
    ):
        main.summary("path", "commitA", "commitB")

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Connection error: Connection failed" in captured.err


def test_summary_handles_runtime_error(capsys: CaptureFixture[str]) -> None:
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.side_effect = RuntimeError("Runtime error")
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    with (
        patch("app.__main__.git_service", mock_git_service),
        patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
        patch("app.__main__.typer.confirm", return_value=True),
        patch("app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL),
        pytest.raises(typer.Exit) as exc_info,
    ):
        main.summary("path", "commitA", "commitB")

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Runtime error" in captured.err


def test_summary_handles_unexpected_error(capsys: CaptureFixture[str]) -> None:
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.side_effect = KeyError("Unexpected error")
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    with (
        patch("app.__main__.git_service", mock_git_service),
        patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
        patch("app.__main__.typer.confirm", return_value=True),
        patch("app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL),
        pytest.raises(typer.Exit) as exc_info,
    ):
        main.summary("path", "commitA", "commitB")

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Unexpected error: 'Unexpected error'" in captured.err


def test_configure_with_empty_api_key(capsys: CaptureFixture[str]) -> None:
    with (
        patch("app.__main__.getpass.getpass", return_value=""),
        pytest.raises(typer.Exit) as exc_info,
    ):
        main.configure("https://api.openai.com/v1", "")

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Error: API key cannot be empty" in captured.err


def test_configure_success(capsys: CaptureFixture[str]) -> None:
    with (
        patch("app.__main__.getpass.getpass", return_value="test-key"),
        patch("app.__main__.config.set_model_config") as mock_set_config,
    ):
        main.configure("https://api.openai.com/v1", "gpt-4")

    mock_set_config.assert_called_once_with(
        "https://api.openai.com/v1", "test-key", "gpt-4"
    )
    captured = capsys.readouterr()
    assert "Configuration saved successfully!" in captured.out


def test_configure_handles_exception(capsys: CaptureFixture[str]) -> None:
    with (
        patch("app.__main__.getpass.getpass", return_value="test-key"),
        patch(
            "app.__main__.config.set_model_config", side_effect=Exception("Save failed")
        ),
        pytest.raises(typer.Exit) as exc_info,
    ):
        main.configure("https://api.openai.com/v1", "")

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Error saving configuration: Save failed" in captured.err


def test_show_config_when_not_configured(capsys: CaptureFixture[str]) -> None:
    with patch("app.__main__.config.get_model_config", return_value=None):
        main.show_config()

    captured = capsys.readouterr()
    assert (
        "Model is not configured. Use the 'configure' command to set up."
        in captured.out
    )


def test_show_config_with_model_name(capsys: CaptureFixture[str]) -> None:
    config = {
        "api_url": "https://api.openai.com/v1",
        "api_key": "test-key",
        "model_name": "gpt-4",
    }
    with patch("app.__main__.config.get_model_config", return_value=config):
        main.show_config()

    captured = capsys.readouterr()
    assert "API URL: https://api.openai.com/v1" in captured.out
    assert "Model name: gpt-4" in captured.out


def test_show_config_without_model_name(capsys: CaptureFixture[str]) -> None:
    config = {
        "api_url": "https://api.openai.com/v1",
        "api_key": "test-key",
    }
    with patch("app.__main__.config.get_model_config", return_value=config):
        main.show_config()

    captured = capsys.readouterr()
    assert "API URL: https://api.openai.com/v1" in captured.out
    assert "Model name:" not in captured.out


def test_summary_handles_git_diff_exception(capsys: CaptureFixture[str]) -> None:
    """Test summary handles exceptions from git_service.get_diff."""
    mock_git_service = Mock()
    mock_git_service.get_diff.side_effect = Exception("git diff failed")
    with patch("app.models.llm_factory.LLMFactory.create_llm", return_value=Mock()):
        with patch("app.__main__.git_service", mock_git_service):
            with pytest.raises(typer.Exit):
                main.summary("path", "commitA", "commitB")


def test_summary_with_invalid_commit_hashes(capsys: CaptureFixture[str]) -> None:
    """Test summary handles invalid commit hashes."""
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = ""
    with patch("app.models.llm_factory.LLMFactory.create_llm", return_value=Mock()):
        with patch("app.__main__.git_service", mock_git_service):
            with patch("app.__main__.typer.confirm", return_value=False):
                with pytest.raises(typer.Exit):
                    main.summary("path", "invalid-hash", "another-invalid-hash")


def test_summary_by_time_function_prints_changes(capsys: CaptureFixture[str]) -> None:
    """Test summary_by_time prints the changes summary."""

    mock_summarize_service = Mock()
    mock_summarize_service.summarize.return_value = "Test summary"
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff_by_time.return_value = "test diff"


def test_summary_user_cancels(capsys: CaptureFixture[str]) -> None:
    """Test that when user cancels via confirmation, summarization is aborted."""
    mock_summarize_service = Mock()
    mock_summarize_service.get_token_count.return_value = 10
    mock_git_service = Mock()
    mock_git_service.get_diff.return_value = "test diff"

    with (
        patch("app.__main__.git_service", mock_git_service),
        patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
        patch("app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL),
        patch("app.__main__.typer.confirm", return_value=False),
        patch("app.__main__.typer.echo"),
    ):
        with pytest.raises(typer.Exit):
            main.summary("path", "commitA", "commitB")

    # Verify summarize was NOT called since user cancelled
    mock_summarize_service.summarize.assert_not_called()


def test_summary_by_time_with_contributors(capsys: CaptureFixture[str]) -> None:
    """Test summary_by_time with contributors option."""
    mock_summarize_service = Mock()
    mock_summarize_service.summarize.return_value = "Test summary"
    mock_summarize_service.get_token_count.return_value = 100
    mock_git_service = Mock()
    mock_git_service.get_diff_by_time.return_value = "test diff"
    mock_git_service.get_contributors_by_time.return_value = "- Alice: 2 commits"

    with (
        patch("app.__main__.git_service", mock_git_service),
        patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
        patch("app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL),
        patch("app.__main__.typer.confirm", return_value=True),
        patch("app.__main__.console.print"),
    ):
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)
        main.summary_by_time("path", start_time, end_time, contributors=True)

    mock_git_service.get_contributors_by_time.assert_called_once_with(
        "path", start_time, end_time
    )
    assert mock_summarize_service.summarize.called


def test_summary_by_time_user_cancels(capsys: CaptureFixture[str]) -> None:
    """Test that summary_by_time aborts when user cancels confirmation."""
    mock_summarize_service = Mock()
    mock_summarize_service.get_token_count.return_value = 5
    mock_git_service = Mock()
    mock_git_service.get_diff_by_time.return_value = "time based diff"

    start_time = datetime(2024, 1, 1)
    end_time = datetime(2024, 1, 2)

    with (
        patch("app.__main__.git_service", mock_git_service),
        patch("app.__main__.SummarizeService", return_value=mock_summarize_service),
        patch("app.__main__.prompt_for_summary_mode", return_value=SummaryMode.GENERAL),
        patch("app.__main__.typer.confirm", return_value=False),
        patch("app.__main__.typer.echo"),
    ):
        with pytest.raises(typer.Exit):
            main.summary_by_time("path", start_time, end_time)

    # Verify summarize was NOT called since user cancelled
    mock_summarize_service.summarize.assert_not_called()
