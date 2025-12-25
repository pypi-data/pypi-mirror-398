from unittest.mock import Mock, patch
from app.agents.agent import Agent
import pytest


def test_invoke_returns_string(agent: Agent) -> None:
    with patch.object(agent.agent, "invoke") as mock_invoke:
        mock_invoke.return_value = {
            "messages": [Mock(content="Hello! I'm doing well, thank you for asking.")]
        }

        response = agent.invoke("Hello, how are you?")

    assert response == "Hello! I'm doing well, thank you for asking."


def test_invoke_raises_error_when_response_not_string(agent: Agent) -> None:
    """Test that invoke raises ValueError when agent response is not a string."""
    with patch.object(agent.agent, "invoke") as mock_invoke:
        # Return a non-string response (e.g., a dict or list)
        mock_invoke.return_value = {
            "messages": [Mock(content={"error": "not a string"})]
        }

        with pytest.raises(ValueError, match="Agent response is not a string"):
            agent.invoke("Hello, how are you?")
