from unittest.mock import Mock, patch
import pytest

from app.agents.agent import Agent
from app.services.git_service import GitService
from app.services.summarize_service import SummarizeService
from langchain_core.language_models import LanguageModelLike


@pytest.fixture(scope="session")
def summarize_service() -> SummarizeService:
    mock_llm = Mock(spec=LanguageModelLike)
    with patch(
        "app.services.summarize_service.LLMFactory.create_llm", return_value=mock_llm
    ):
        return SummarizeService()


@pytest.fixture(scope="session", autouse=True)
def git_service() -> GitService:
    return GitService()


@pytest.fixture
def mock_model() -> Mock:
    return Mock(spec=LanguageModelLike)


@pytest.fixture
def agent(mock_model: Mock) -> Agent:
    return Agent(model=mock_model, tools=[])


@pytest.fixture(scope="session")
def cloned_repo(git_service: GitService) -> str:
    repo = "https://github.com/ilnarkhasanov/AiToHuman"
    clone_path = "/tmp/repo"
    git_service.clone(repo, clone_path)
    return clone_path
