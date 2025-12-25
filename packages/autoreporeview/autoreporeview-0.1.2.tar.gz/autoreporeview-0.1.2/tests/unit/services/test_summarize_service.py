from unittest.mock import Mock, patch
from uuid import uuid4
import pytest
from app.services.summarize_service import SummarizeService, SummaryMode


def test_formulating_prompt(
    summarize_service: SummarizeService,
) -> None:
    """Test that prepare_prompt generates correct prompt for GENERAL mode."""
    diff = str(uuid4())
    prompt = summarize_service.prepare_prompt(diff, None, SummaryMode.GENERAL)

    assert (
        "Analyze the git diff below and provide a concise summary of the changes."
        in prompt
    )
    assert "Main purpose and high-level changes" in prompt
    assert "**Summary:**" in prompt
    assert "**Key Changes:**" in prompt
    assert diff in prompt


def test_prepare_prompt_all_modes(summarize_service: SummarizeService) -> None:
    """Test prepare_prompt yields key text for each summary mode."""
    diff = "some-diff"
    assert (
        "documentation changes"
        in summarize_service.prepare_prompt(
            diff, mode=SummaryMode.DOCUMENTATION
        ).lower()
    )
    assert (
        "features that were added or removed"
        in summarize_service.prepare_prompt(diff, mode=SummaryMode.FEATURES).lower()
    )
    assert (
        "breaking changes that may affect"
        in summarize_service.prepare_prompt(
            diff, mode=SummaryMode.BREAKING_CHANGES
        ).lower()
    )
    assert (
        "concise summary"
        in summarize_service.prepare_prompt(diff, mode=SummaryMode.GENERAL).lower()
    )


def test_summarize_calls_agent_in_all_modes(
    summarize_service: SummarizeService,
) -> None:
    """Ensure the agent is invoked for each summary mode using the fixture-provided service."""
    service = summarize_service
    for mode in SummaryMode:
        with patch.object(
            service.agent, "invoke", return_value=f"result: {mode}"
        ) as mock_invoke:
            result = service.summarize("diff-content", None, mode)
            assert result == f"result: {mode}"
            assert mock_invoke.call_count == 1
            called_prompt = mock_invoke.call_args[0][0]
            assert "diff-content" in called_prompt
            # Should mention mode-specific text
            if mode == SummaryMode.GENERAL:
                assert "concise summary" in called_prompt.lower()
            elif mode == SummaryMode.DOCUMENTATION:
                assert "documentation changes" in called_prompt.lower()
            elif mode == SummaryMode.FEATURES:
                assert "features that were added or removed" in called_prompt.lower()
            elif mode == SummaryMode.BREAKING_CHANGES:
                assert "breaking changes that may affect" in called_prompt.lower()


def test_get_token_count_mode_passthrough(summarize_service: SummarizeService) -> None:
    """Verify that the mode is passed through to prepare_prompt and token encoder is used."""
    service = summarize_service
    with (
        patch.object(service, "prepare_prompt", return_value="prompt") as mock_prepare,
        patch(
            "app.services.summarize_service.config.get_model_config", return_value=None
        ),
        patch(
            "app.services.summarize_service.tiktoken.encoding_for_model",
            return_value=Mock(encode=lambda x: [1, 2, 3]),
        ),
    ):
        assert service.get_token_count("diff", None, SummaryMode.FEATURES) == 3
        mock_prepare.assert_called_with("diff", None, SummaryMode.FEATURES)


def test_prepare_prompt_with_contributors_info(
    summarize_service: SummarizeService,
) -> None:
    """Test that prepare_prompt includes contributors information when provided."""
    diff = str(uuid4())
    contributors_info = "- Alice: 2 commit(s)\n- Bob: 1 commit(s)"
    prompt = summarize_service.prepare_prompt(
        diff, contributors_info, SummaryMode.GENERAL
    )

    assert "**Contributors Information:**" in prompt
    assert contributors_info in prompt
    assert "Please include a **Contributors** section" in prompt
    assert diff in prompt


def test_prepare_prompt_without_contributors_info(
    summarize_service: SummarizeService,
) -> None:
    """Test that prepare_prompt works without contributors information."""
    diff = str(uuid4())
    prompt = summarize_service.prepare_prompt(diff)

    assert "**Contributors Information:**" not in prompt
    assert diff in prompt


def test_summarize(
    summarize_service: SummarizeService,
) -> None:
    diff = "diff --git a/file.txt b/file.txt\nindex 83db48f..f735c2d 100644\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1,2 @@\n-Hello World\n+Hello, World!\n+This is a new line."
    with patch.object(
        summarize_service.agent,
        "invoke",
        return_value="Summary of changes",
    ) as mock_invoke:
        summary = summarize_service.summarize(diff, None, SummaryMode.GENERAL)
        # Verify the prompt was passed correctly (it will be the full prompt string)
        call_args = mock_invoke.call_args[0][0]
        assert diff in call_args

    assert isinstance(summary, str)
    assert len(summary) > 0


def test_get_token_count_with_valid_model(
    summarize_service: SummarizeService,
) -> None:
    """Test get_token_count with a valid model name."""
    diff = "test diff content"
    with patch(
        "app.services.summarize_service.config.get_model_config"
    ) as mock_get_config:
        mock_get_config.return_value = {"model_name": "gpt-4"}
        with patch(
            "app.services.summarize_service.tiktoken.encoding_for_model"
        ) as mock_encoding:
            mock_encoder = Mock()
            mock_encoder.encode.return_value = [1, 2, 3, 4, 5]
            mock_encoding.return_value = mock_encoder

            token_count = summarize_service.get_token_count(diff)

            assert token_count == 5
            mock_get_config.assert_called_once()
            mock_encoding.assert_called_once_with("gpt-4")
            mock_encoder.encode.assert_called_once()


def test_get_token_count_with_default_model(
    summarize_service: SummarizeService,
) -> None:
    """Test get_token_count uses default model when config is None."""
    diff = "test diff content"
    with patch(
        "app.services.summarize_service.config.get_model_config"
    ) as mock_get_config:
        mock_get_config.return_value = None
        with patch(
            "app.services.summarize_service.tiktoken.encoding_for_model"
        ) as mock_encoding:
            mock_encoder = Mock()
            mock_encoder.encode.return_value = [1, 2, 3]
            mock_encoding.return_value = mock_encoder

            token_count = summarize_service.get_token_count(diff)

            assert token_count == 3
            mock_encoding.assert_called_once_with("gpt-4")


def test_get_token_count_with_model_name_in_config(
    summarize_service: SummarizeService,
) -> None:
    """Test get_token_count uses model_name from config when available."""
    diff = "test diff content"
    with patch(
        "app.services.summarize_service.config.get_model_config"
    ) as mock_get_config:
        mock_get_config.return_value = {"model_name": "gpt-3.5-turbo"}
        with patch(
            "app.services.summarize_service.tiktoken.encoding_for_model"
        ) as mock_encoding:
            mock_encoder = Mock()
            mock_encoder.encode.return_value = [1, 2, 3, 4]
            mock_encoding.return_value = mock_encoder

            token_count = summarize_service.get_token_count(diff)

            assert token_count == 4
            mock_encoding.assert_called_once_with("gpt-3.5-turbo")


def test_get_token_count_with_contributors_info(
    summarize_service: SummarizeService,
) -> None:
    """Test get_token_count includes contributors_info in prompt."""
    diff = "test diff"
    contributors_info = "- Alice: 2 commit(s)"
    with patch(
        "app.services.summarize_service.config.get_model_config"
    ) as mock_get_config:
        mock_get_config.return_value = {"model_name": "gpt-4"}
        with patch(
            "app.services.summarize_service.tiktoken.encoding_for_model"
        ) as mock_encoding:
            mock_encoder = Mock()
            mock_encoder.encode.return_value = [1, 2, 3, 4, 5, 6, 7]
            mock_encoding.return_value = mock_encoder

            token_count = summarize_service.get_token_count(
                diff, contributors_info, SummaryMode.GENERAL
            )

            assert token_count == 7
            # Verify the prompt includes contributors info
            call_args = mock_encoder.encode.call_args[0][0]
            assert contributors_info in call_args


def test_get_token_count_with_invalid_model(
    summarize_service: SummarizeService,
) -> None:
    """Test get_token_count handles invalid model name by falling back to cl100k_base."""
    # get_token_count should not raise an error for invalid model names,
    # instead it falls back to cl100k_base encoding
    with patch(
        "app.services.summarize_service.config.get_model_config",
        return_value={"model_name": "invalid-model"},
    ):
        result = summarize_service.get_token_count("test diff")
        assert isinstance(result, int)
        assert result > 0


def test_get_token_count_handles_keyerror_fallback(
    summarize_service: SummarizeService,
) -> None:
    """Test get_token_count falls back to cl100k_base encoding on KeyError."""
    diff = "test diff content"
    with patch(
        "app.services.summarize_service.config.get_model_config"
    ) as mock_get_config:
        mock_get_config.return_value = {"model_name": "unknown-model"}
        with patch(
            "app.services.summarize_service.tiktoken.encoding_for_model"
        ) as mock_encoding:
            mock_encoding.side_effect = KeyError("Unknown model")
            with patch(
                "app.services.summarize_service.tiktoken.get_encoding"
            ) as mock_get_encoding:
                mock_encoder = Mock()
                mock_encoder.encode.return_value = [1, 2, 3, 4, 5, 6]
                mock_get_encoding.return_value = mock_encoder

                token_count = summarize_service.get_token_count(diff)

                assert token_count == 6
                mock_encoding.assert_called_once_with("unknown-model")
                mock_get_encoding.assert_called_once_with("cl100k_base")
                mock_encoder.encode.assert_called_once()


def test_summarize_handles_connection_error(
    summarize_service: SummarizeService,
) -> None:
    """Test that APIConnectionError is converted to ConnectionError."""
    diff = "test diff"

    class APIConnectionError(Exception):
        pass

    connection_error = APIConnectionError("Failed to connect")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=connection_error,
    ):
        with pytest.raises(ConnectionError) as exc_info:
            summarize_service.summarize(diff)

        assert "Failed to connect to API" in str(exc_info.value)
        assert "API URL is correct" in str(exc_info.value)


def test_summarize_handles_connection_error_by_type_name(
    summarize_service: SummarizeService,
) -> None:
    """Test that exceptions with 'Connection' in type name are converted to ConnectionError."""
    diff = "test diff"

    class ConnectionTimeoutError(Exception):
        pass

    connection_error = ConnectionTimeoutError("Connection failed")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=connection_error,
    ):
        with pytest.raises(ConnectionError) as exc_info:
            summarize_service.summarize(diff)

        assert "Failed to connect to API" in str(exc_info.value)


def test_summarize_handles_authentication_error(
    summarize_service: SummarizeService,
) -> None:
    """Test that AuthenticationError is converted to ValueError."""
    diff = "test diff"

    class AuthenticationError(Exception):
        pass

    auth_error = AuthenticationError("Invalid key")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=auth_error,
    ):
        with pytest.raises(ValueError) as exc_info:
            summarize_service.summarize(diff)

        assert "Authentication failed" in str(exc_info.value)
        assert "Use 'configure' command" in str(exc_info.value)


def test_summarize_handles_401_error(summarize_service: SummarizeService) -> None:
    """Test that 401 error is converted to ValueError."""
    diff = "test diff"
    auth_error = Exception("401 Unauthorized")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=auth_error,
    ):
        with pytest.raises(ValueError) as exc_info:
            summarize_service.summarize(diff)

        assert "Authentication failed" in str(exc_info.value)


def test_summarize_handles_403_error(summarize_service: SummarizeService) -> None:
    """Test that 403 error is converted to ValueError."""
    diff = "test diff"
    auth_error = Exception("403 Forbidden")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=auth_error,
    ):
        with pytest.raises(ValueError) as exc_info:
            summarize_service.summarize(diff)

        assert "Authentication failed" in str(exc_info.value)


def test_summarize_handles_api_error(summarize_service: SummarizeService) -> None:
    """Test that APIError is converted to RuntimeError."""
    diff = "test diff"

    class APIError(Exception):
        pass

    api_error = APIError("Bad request")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=api_error,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            summarize_service.summarize(diff)

        assert "API error occurred" in str(exc_info.value)
        assert "API URL and model name are correct" in str(exc_info.value)


def test_summarize_handles_400_error(summarize_service: SummarizeService) -> None:
    """Test that 400 error is converted to RuntimeError."""
    diff = "test diff"
    api_error = Exception("400 Bad Request")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=api_error,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            summarize_service.summarize(diff)

        assert "API error occurred" in str(exc_info.value)


def test_summarize_handles_429_error(summarize_service: SummarizeService) -> None:
    """Test that 429 error is converted to RuntimeError."""
    diff = "test diff"
    api_error = Exception("429 Too Many Requests")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=api_error,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            summarize_service.summarize(diff)

        assert "API error occurred" in str(exc_info.value)


def test_summarize_reraises_value_error(summarize_service: SummarizeService) -> None:
    """Test that ValueError is re-raised as-is."""
    diff = "test diff"
    value_error = ValueError("Original value error")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=value_error,
    ):
        with pytest.raises(ValueError, match="Original value error"):
            summarize_service.summarize(diff)


def test_summarize_handles_other_errors(summarize_service: SummarizeService) -> None:
    """Test that other errors are converted to RuntimeError."""
    diff = "test diff"
    other_error = KeyError("Something went wrong")

    with patch.object(
        summarize_service.agent,
        "invoke",
        side_effect=other_error,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            summarize_service.summarize(diff)

        assert "An error occurred while generating summary" in str(exc_info.value)
        assert "Something went wrong" in str(exc_info.value)
