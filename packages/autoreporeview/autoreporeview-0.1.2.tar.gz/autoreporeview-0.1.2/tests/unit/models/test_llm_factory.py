from unittest.mock import Mock, patch

import pytest
from pydantic import SecretStr

from app.models.llm_factory import LLMFactory


def test_create_llm_raises_error_when_config_not_set() -> None:
    """Test that create_llm raises ValueError when model is not configured."""
    with patch("app.models.llm_factory.config.get_model_config", return_value=None):
        with pytest.raises(ValueError, match="Model is not configured"):
            LLMFactory.create_llm()


def test_create_llm_raises_error_when_api_key_missing() -> None:
    """Test that create_llm raises ValueError when API key is missing."""
    config = {"api_url": "https://api.openai.com/v1", "api_key": None}

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        with pytest.raises(ValueError, match="API key not found"):
            LLMFactory.create_llm()


def test_create_llm_raises_error_when_api_key_empty() -> None:
    """Test that create_llm raises ValueError when API key is empty."""
    config = {"api_url": "https://api.openai.com/v1", "api_key": ""}

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        with pytest.raises(ValueError, match="API key not found"):
            LLMFactory.create_llm()


def test_create_llm_with_unsupported_api_url() -> None:
    """Test create_llm raises error for unsupported API URLs."""
    config = {"api_url": "https://unsupported.api.com", "api_key": "test-key"}
    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        with pytest.raises(ValueError, match="Unsupported API URL"):
            LLMFactory.create_llm()


def test_create_llm_with_missing_configuration() -> None:
    """Test create_llm raises error for missing configuration."""
    with patch("app.models.llm_factory.config.get_model_config", return_value=None):
        with pytest.raises(ValueError, match="Model is not configured"):
            LLMFactory.create_llm()


@patch("app.models.llm_factory.GigaChat")
def test_create_llm_creates_gigachat_model(mock_gigachat: Mock) -> None:
    """Test that create_llm creates GigaChat model for GigaChat API URL."""
    config = {
        "api_url": "https://gigachat.devices.sberbank.ru/api/v1",
        "api_key": "test-key",
        "model_name": "GigaChat-2-Max",
    }

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        LLMFactory.create_llm()

    mock_gigachat.assert_called_once_with(
        model="GigaChat-2-Max",
        credentials="test-key",
        verify_ssl_certs=False,
    )


@patch("app.models.llm_factory.GigaChat")
def test_create_llm_creates_gigachat_with_default_model(mock_gigachat: Mock) -> None:
    """Test that create_llm uses default model name for GigaChat when not specified."""
    config = {
        "api_url": "https://gigachat.devices.sberbank.ru/api/v1",
        "api_key": "test-key",
        "model_name": "",
    }

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        LLMFactory.create_llm()

    mock_gigachat.assert_called_once_with(
        model="GigaChat-2-Max",
        credentials="test-key",
        verify_ssl_certs=False,
    )


@patch("app.models.llm_factory.GigaChat")
def test_create_llm_creates_gigachat_case_insensitive(mock_gigachat: Mock) -> None:
    """Test that create_llm detects GigaChat URL case-insensitively."""
    config = {
        "api_url": "https://GIGACHAT.devices.sberbank.ru/api/v1",
        "api_key": "test-key",
        "model_name": "test-model",
    }

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        LLMFactory.create_llm()

    mock_gigachat.assert_called_once()


@patch("app.models.llm_factory.ChatOpenAI")
def test_create_llm_creates_openai_model(mock_chat_openai: Mock) -> None:
    """Test that create_llm creates ChatOpenAI model for OpenAI API URL."""
    config = {
        "api_url": "https://api.openai.com/v1",
        "api_key": "test-key",
        "model_name": "gpt-4",
    }

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        LLMFactory.create_llm()

    mock_chat_openai.assert_called_once_with(
        model="gpt-4",
        api_key=SecretStr("test-key"),
        base_url="https://api.openai.com/v1",
    )


@patch("app.models.llm_factory.ChatOpenAI")
def test_create_llm_creates_openai_with_default_model(mock_chat_openai: Mock) -> None:
    """Test that create_llm uses default model name for OpenAI when not specified."""
    config = {
        "api_url": "https://api.openai.com/v1",
        "api_key": "test-key",
        "model_name": "",
    }

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        LLMFactory.create_llm()

    mock_chat_openai.assert_called_once_with(
        model="gpt-4",
        api_key=SecretStr("test-key"),
        base_url="https://api.openai.com/v1",
    )


@patch("app.models.llm_factory.ChatOpenAI")
def test_create_llm_creates_openai_for_custom_url(mock_chat_openai: Mock) -> None:
    """Test that create_llm creates ChatOpenAI for custom API URLs."""
    config = {
        "api_url": "https://custom-api.example.com/v1",
        "api_key": "test-key",
        "model_name": "custom-model",
    }

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        LLMFactory.create_llm()

    mock_chat_openai.assert_called_once_with(
        model="custom-model",
        api_key=SecretStr("test-key"),
        base_url="https://custom-api.example.com/v1",
    )


@patch("app.models.llm_factory.ChatOpenAI")
def test_create_llm_returns_llm_instance(mock_chat_openai: Mock) -> None:
    """Test that create_llm returns the created LLM instance."""
    mock_llm = Mock()
    mock_chat_openai.return_value = mock_llm

    config = {
        "api_url": "https://api.openai.com/v1",
        "api_key": "test-key",
        "model_name": "gpt-4",
    }

    with patch("app.models.llm_factory.config.get_model_config", return_value=config):
        result = LLMFactory.create_llm()

    assert result is mock_llm
