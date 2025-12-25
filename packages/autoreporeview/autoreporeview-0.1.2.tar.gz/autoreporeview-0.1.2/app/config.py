import json
import os
import platform
from pathlib import Path
from typing import Optional

import keyring


class Config:
    """Configuration management and secure API key storage."""

    SERVICE_NAME = "autoreporeview"
    CONFIG_DIR = Path.home() / ".config" / "autoreporeview"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    def __init__(self) -> None:
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Creates configuration directory if it doesn't exist."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.CONFIG_FILE.touch(exist_ok=True)
        # Set file permissions to owner-only
        if platform.system() != "Windows":
            os.chmod(self.CONFIG_FILE, 0o600)

    def get_model_config(self) -> Optional[dict[str, str]]:
        """Gets the current model configuration."""
        if not self.CONFIG_FILE.exists() or self.CONFIG_FILE.stat().st_size == 0:
            return None

        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "api_url" in config:
                    api_key = keyring.get_password(self.SERVICE_NAME, config["api_url"])
                    return {
                        "api_url": config["api_url"],
                        "api_key": api_key,
                        "model_name": config.get("model_name", ""),
                    }
        except (json.JSONDecodeError, FileNotFoundError):
            return None

        return None

    def set_model_config(
        self, api_url: str, api_key: str, model_name: str = ""
    ) -> None:
        """Saves model configuration."""
        # Clean and validate API URL
        api_url = api_url.strip()
        if not api_url:
            raise ValueError("API URL cannot be empty")

        # Remove trailing slashes
        api_url = api_url.rstrip("/")

        # Basic URL validation
        if not api_url.startswith(("http://", "https://")):
            raise ValueError("Invalid API URL: must start with http:// or https://")

        config = {
            "api_url": api_url,
            "model_name": model_name.strip() if model_name else "",
        }

        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        keyring.set_password(self.SERVICE_NAME, api_url, api_key)

    def clear_config(self) -> None:
        """Clears configuration."""
        if self.CONFIG_FILE.exists():
            config = self.get_model_config()
            if config and config.get("api_url"):
                try:
                    keyring.delete_password(self.SERVICE_NAME, config["api_url"])
                except keyring.errors.PasswordDeleteError:
                    pass
            self.CONFIG_FILE.unlink()


config = Config()
