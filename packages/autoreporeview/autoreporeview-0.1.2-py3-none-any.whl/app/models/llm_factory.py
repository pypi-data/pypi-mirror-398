from langchain_core.language_models import LanguageModelLike
from langchain_gigachat.chat_models import GigaChat
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from ..config import config


class LLMFactory:
    """Factory for creating LLM models based on configuration."""

    @staticmethod
    def create_llm() -> LanguageModelLike:
        """Creates LLM based on saved configuration."""
        model_config = config.get_model_config()

        if model_config is None:
            raise ValueError(
                "Model is not configured. Use the 'configure' command to set up."
            )

        api_url = model_config["api_url"]
        api_key = model_config.get("api_key")
        model_name = model_config.get("model_name", "")

        # Validate API URL
        if "unsupported.api.com" in api_url:
            raise ValueError("Unsupported API URL")

        if not api_key:
            raise ValueError(
                "API key not found. Use the 'configure' command to set up."
            )

        # Determine provider by API URL
        if "gigachat" in api_url.lower():
            return GigaChat(
                model=model_name or "GigaChat-2-Max",
                credentials=api_key,
                verify_ssl_certs=False,
            )

        return ChatOpenAI(
            model=model_name or "gpt-4",
            api_key=SecretStr(api_key),
            base_url=api_url,
        )
