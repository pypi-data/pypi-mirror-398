import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import keyring

from app.config import Config


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Creates a temporary config directory for testing."""
    return tmp_path / ".config" / "autoreporeview"


@pytest.fixture
def config_instance(temp_config_dir: Path) -> Config:
    """Creates a Config instance with temporary directory."""
    with patch.object(Config, "CONFIG_DIR", temp_config_dir):
        with patch.object(Config, "CONFIG_FILE", temp_config_dir / "config.json"):
            return Config()


@pytest.fixture
def sample_api_url() -> str:
    """Sample API URL for testing."""
    return "https://api.openai.com/v1"


@pytest.fixture
def sample_api_key() -> str:
    """Sample API key for testing."""
    return "test-api-key"


@pytest.fixture
def sample_model_name() -> str:
    """Sample model name for testing."""
    return "gpt-4"


def test_config_init_creates_directory(config_instance: Config) -> None:
    """Test that Config.__init__ creates the config directory."""
    assert config_instance.CONFIG_DIR.exists()
    assert config_instance.CONFIG_FILE.exists()


def test_get_model_config_returns_none_when_file_not_exists(
    config_instance: Config,
) -> None:
    """Test that get_model_config returns None when config file doesn't exist."""
    config_instance.CONFIG_FILE.unlink()
    assert config_instance.get_model_config() is None


def test_get_model_config_returns_none_when_file_empty(config_instance: Config) -> None:
    """Test that get_model_config returns None when config file is empty."""
    config_instance.CONFIG_FILE.write_text("")
    assert config_instance.get_model_config() is None


def test_get_model_config_returns_none_when_invalid_json(
    config_instance: Config,
) -> None:
    """Test that get_model_config returns None when config file has invalid JSON."""
    config_instance.CONFIG_FILE.write_text("{ invalid json }")
    assert config_instance.get_model_config() is None


def test_get_model_config_returns_none_when_no_api_url(config_instance: Config) -> None:
    """Test that get_model_config returns None when api_url is missing."""
    config_instance.CONFIG_FILE.write_text(json.dumps({"model_name": "test"}))
    assert config_instance.get_model_config() is None


@patch("app.config.keyring.get_password")
def test_get_model_config_returns_config(
    mock_get_password: Mock,
    config_instance: Config,
    sample_api_url: str,
    sample_api_key: str,
    sample_model_name: str,
) -> None:
    """Test that get_model_config returns correct configuration."""
    api_url = sample_api_url
    api_key = sample_api_key
    model_name = sample_model_name

    config_instance.CONFIG_FILE.write_text(
        json.dumps({"api_url": api_url, "model_name": model_name})
    )
    mock_get_password.return_value = api_key

    result = config_instance.get_model_config()

    assert result is not None
    assert result["api_url"] == api_url
    assert result["api_key"] == api_key
    assert result["model_name"] == model_name
    mock_get_password.assert_called_once_with(Config.SERVICE_NAME, api_url)


@patch("app.config.keyring.get_password")
def test_get_model_config_returns_empty_model_name_when_not_set(
    mock_get_password: Mock,
    config_instance: Config,
    sample_api_url: str,
    sample_api_key: str,
) -> None:
    """Test that get_model_config returns empty string for model_name when not set."""
    api_url = sample_api_url
    api_key = sample_api_key

    config_instance.CONFIG_FILE.write_text(json.dumps({"api_url": api_url}))
    mock_get_password.return_value = api_key

    result = config_instance.get_model_config()

    assert result is not None
    assert result["model_name"] == ""


def test_set_model_config_raises_error_on_empty_url(config_instance: Config) -> None:
    """Test that set_model_config raises ValueError for empty API URL."""
    with pytest.raises(ValueError, match="API URL cannot be empty"):
        config_instance.set_model_config("", "test-key")


def test_set_model_config_raises_error_on_invalid_url(config_instance: Config) -> None:
    """Test that set_model_config raises ValueError for invalid API URL."""
    with pytest.raises(ValueError, match="Invalid API URL"):
        config_instance.set_model_config("invalid-url", "test-key")


def test_set_model_config_removes_trailing_slash(
    config_instance: Config, sample_api_url: str, sample_api_key: str
) -> None:
    """Test that set_model_config removes trailing slashes from API URL."""
    api_url = f"{sample_api_url}/"
    api_key = sample_api_key

    with patch("app.config.keyring.set_password") as mock_set_password:
        config_instance.set_model_config(api_url, api_key)

        config_data = json.loads(config_instance.CONFIG_FILE.read_text())
        assert config_data["api_url"] == sample_api_url
        mock_set_password.assert_called_once_with(
            Config.SERVICE_NAME, sample_api_url, api_key
        )


@patch("app.config.keyring.set_password")
def test_set_model_config_saves_config(
    mock_set_password: Mock,
    config_instance: Config,
    sample_api_url: str,
    sample_api_key: str,
    sample_model_name: str,
) -> None:
    """Test that set_model_config saves configuration correctly."""
    api_url = sample_api_url
    api_key = sample_api_key
    model_name = sample_model_name

    config_instance.set_model_config(api_url, api_key, model_name)

    config_data = json.loads(config_instance.CONFIG_FILE.read_text())
    assert config_data["api_url"] == api_url
    assert config_data["model_name"] == model_name
    mock_set_password.assert_called_once_with(Config.SERVICE_NAME, api_url, api_key)


@patch("app.config.keyring.set_password")
def test_set_model_config_strips_whitespace(
    mock_set_password: Mock,
    config_instance: Config,
    sample_api_url: str,
    sample_api_key: str,
    sample_model_name: str,
) -> None:
    """Test that set_model_config strips whitespace from inputs."""
    api_url = f"  {sample_api_url}  "
    api_key = sample_api_key
    model_name = f"  {sample_model_name}  "

    config_instance.set_model_config(api_url, api_key, model_name)

    config_data = json.loads(config_instance.CONFIG_FILE.read_text())
    assert config_data["api_url"] == "https://api.openai.com/v1"
    assert config_data["model_name"] == "gpt-4"


@patch("app.config.keyring.set_password")
def test_set_model_config_with_empty_model_name(
    mock_set_password: Mock,
    config_instance: Config,
    sample_api_url: str,
    sample_api_key: str,
) -> None:
    """Test that set_model_config handles empty model_name."""
    api_url = sample_api_url
    api_key = sample_api_key

    config_instance.set_model_config(api_url, api_key, "")

    config_data = json.loads(config_instance.CONFIG_FILE.read_text())
    assert config_data["model_name"] == ""


@patch("app.config.keyring.get_password")
@patch("app.config.keyring.delete_password")
def test_clear_config_deletes_password_and_file(
    mock_delete_password: Mock,
    mock_get_password: Mock,
    config_instance: Config,
    sample_api_url: str,
    sample_api_key: str,
) -> None:
    """Test that clear_config deletes password from keyring and removes config file."""
    api_url = sample_api_url
    api_key = sample_api_key

    config_instance.CONFIG_FILE.write_text(json.dumps({"api_url": api_url}))
    mock_get_password.return_value = api_key

    config_instance.clear_config()

    assert not config_instance.CONFIG_FILE.exists()
    mock_delete_password.assert_called_once_with(Config.SERVICE_NAME, api_url)


@patch("app.config.keyring.get_password")
@patch("app.config.keyring.delete_password")
def test_clear_config_handles_password_delete_error(
    mock_delete_password: Mock,
    mock_get_password: Mock,
    config_instance: Config,
    sample_api_url: str,
) -> None:
    """Test that clear_config handles PasswordDeleteError gracefully."""
    api_url = sample_api_url

    config_instance.CONFIG_FILE.write_text(json.dumps({"api_url": api_url}))
    mock_get_password.return_value = "test-key"
    mock_delete_password.side_effect = keyring.errors.PasswordDeleteError()

    config_instance.clear_config()

    assert not config_instance.CONFIG_FILE.exists()


def test_clear_config_when_file_not_exists(config_instance: Config) -> None:
    """Test that clear_config handles non-existent config file."""
    if config_instance.CONFIG_FILE.exists():
        config_instance.CONFIG_FILE.unlink()

    config_instance.clear_config()


def test_set_model_config_accepts_http_url(
    config_instance: Config, sample_api_key: str
) -> None:
    """Test that set_model_config accepts http:// URLs."""
    api_url = "http://localhost:8000/v1"
    api_key = sample_api_key

    with patch("app.config.keyring.set_password"):
        config_instance.set_model_config(api_url, api_key)

        config_data = json.loads(config_instance.CONFIG_FILE.read_text())
        assert config_data["api_url"] == api_url


@patch("app.config.os.chmod")
def test_ensure_config_dir_handles_existing_directory(
    mock_chmod: Mock, config_instance: Config
) -> None:
    """Test _ensure_config_dir when directory already exists."""
    config_instance.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_instance._ensure_config_dir()
    mock_chmod.assert_called_once_with(config_instance.CONFIG_FILE, 0o600)


@patch("app.config.os.chmod")
def test_ensure_config_dir_handles_permission_error(
    mock_chmod: Mock, config_instance: Config
) -> None:
    """Test _ensure_config_dir when permission error occurs."""
    with patch("app.config.Path.mkdir", side_effect=PermissionError):
        with pytest.raises(PermissionError):
            config_instance._ensure_config_dir()
