from enum import Enum
from opentelemetry import trace
import tiktoken

from ..agents.agent import Agent
from ..models.llm_factory import LLMFactory
from ..config import config

tracer = trace.get_tracer(__name__)


class SummaryMode(str, Enum):
    """Enumeration of available summary prompt modes."""

    GENERAL = "general"
    DOCUMENTATION = "documentation"
    FEATURES = "features"
    BREAKING_CHANGES = "breaking_changes"


class SummarizeService:
    def __init__(self) -> None:
        llm = LLMFactory.create_llm()
        self.agent = Agent(
            llm,
            tools=[],
        )

    def prepare_prompt(
        self,
        diff: str,
        contributors_info: str | None = None,
        mode: SummaryMode = SummaryMode.GENERAL,
    ) -> str:
        contributors_instruction = ""
        if contributors_info:
            contributors_instruction = f"""

**Contributors Information:**
{contributors_info}

Please include a **Contributors** section in your summary showing who contributed what changes.
"""

        base_prompt = self._get_mode_prompt(mode)
        return f"""{base_prompt}
{contributors_instruction}
------------
{diff}
------------"""

    def _get_mode_prompt(self, mode: SummaryMode) -> str:
        """Get the mode-specific prompt template."""
        if mode == SummaryMode.GENERAL:
            return """Analyze the git diff below and provide a concise summary of the changes.

Focus on:
- Main purpose and high-level changes (what was done and why)
- Key functional changes (new features, bug fixes, refactorings)
- Breaking changes or important updates (if any)

Keep it brief and structured. Do NOT list every file or line change - focus on the big picture.

Format the response as:
**Summary:** [1-2 sentences about the main purpose]

**Key Changes:**
- [Brief bullet points of important changes]

**Breaking Changes:** [Only if there are any, otherwise omit this section]"""

        elif mode == SummaryMode.DOCUMENTATION:
            return """Analyze the git diff below and provide a detailed summary focusing specifically on documentation changes.

Focus ONLY on:
- Documentation files (README, docs/, *.md, *.rst, comments in code, docstrings)
- What documentation was added, modified, or removed
- Changes to API documentation, guides, tutorials, or inline code comments
- Improvements to code clarity through documentation

IGNORE code changes, features, bug fixes, or refactoring unless they directly relate to documentation.

Format the response as:
**Documentation Summary:** [1-2 sentences about the documentation changes]

**Documentation Changes:**
- [bullet points of what documentation was changed, added, or removed]
- [Include file paths for documentation files]
- [Note any new documentation patterns or standards introduced]

**Impact:** [Brief note on how these documentation changes help users/developers]"""

        elif mode == SummaryMode.FEATURES:
            return """Analyze the git diff below and provide a detailed summary focusing specifically on features that were added or removed.

Focus ONLY on:
- New implementation features, functionality, or capabilities that were added
- Features that were removed or deprecated
- Enhancements to existing implemented features
- New APIs, functions, classes, or modules introduced

IGNORE bug fixes, refactoring, documentation, and configuration changes.

For each feature:
- Describe briefly what the feature does
- Where it was added (files/modules/classes)
- Why it might be important or what problem it solves

Format the response as:
**Features Summary:** [1-2 sentences about the overall feature changes]

**New Features:**
- [For each new feature: describe what was added, where, and why it's useful]

**Removed/Deprecated Features:**
- [For each removed feature: describe what was removed and why (if evident)]

**Feature Enhancements:**
- [For existing features that were improved: describe what was enhanced]"""

        elif mode == SummaryMode.BREAKING_CHANGES:
            return """Analyze the git diff below and provide a detailed summary focusing specifically on breaking changes that may affect existing code or users.

Focus ONLY on:
- Removed or renamed APIs, functions, classes, or modules
- Changed method/function signatures (parameters, return types)
- Deprecated features that will be removed
- Database schema changes that require migrations
- Configuration format changes
- Changes to public interfaces or contracts
- Changes that would break backward compatibility

IGNORE non-breaking changes, bug fixes, documentation, and new features that don't affect existing code.

For each breaking change:
- Identify what was changed or removed
- Explain how it impacts existing code or usage

Format the response as:
**Breaking Changes Summary:** [1-2 sentences about the overall impact]

**Breaking Changes:**
- [For each breaking change: describe what changed, how it impacts existing code, and migration steps if applicable]

"""

        else:
            # Fallback to general mode
            return self._get_mode_prompt(SummaryMode.GENERAL)

    def get_token_count(
        self,
        diff: str,
        contributors_info: str | None = None,
        mode: SummaryMode = SummaryMode.GENERAL,
    ) -> int:
        prompt = self.prepare_prompt(diff, contributors_info, mode)

        model_config = config.get_model_config()
        model_name = (
            model_config.get("model_name", "gpt-4") if model_config else "gpt-4"
        )

        try:
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(prompt))
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(prompt))

    def summarize(
        self,
        diff: str,
        contributors_info: str | None = None,
        mode: SummaryMode = SummaryMode.GENERAL,
    ) -> str:
        with tracer.start_as_current_span("summarize_service.summarize") as span:
            span.set_attribute("diff_length", len(diff))
            span.set_attribute("summary_mode", mode.value)
            prompt = self.prepare_prompt(diff, contributors_info, mode)
            try:
                with tracer.start_as_current_span("agent.invoke"):
                    result = self.agent.invoke(prompt)
                    span.set_attribute("result_length", len(result))
                    return result
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)

                # Extract meaningful error message
                if "APIConnectionError" in error_type or "Connection" in error_type:
                    raise ConnectionError(
                        f"Failed to connect to API. Please check:\n"
                        f"  - Your internet connection\n"
                        f"  - API URL is correct (use 'show-config' to check)\n"
                        f"  - API server is accessible\n\n"
                        f"Error details: {error_msg}"
                    ) from None
                elif (
                    "AuthenticationError" in error_type
                    or "401" in error_msg
                    or "403" in error_msg
                ):
                    raise ValueError(
                        f"Authentication failed. Please check your API key.\n"
                        f"Use 'configure' command to update your API key.\n\n"
                        f"Error details: {error_msg}"
                    ) from None
                elif (
                    "APIError" in error_type or "400" in error_msg or "429" in error_msg
                ):
                    raise RuntimeError(
                        f"API error occurred. Please check:\n"
                        f"  - API URL and model name are correct\n"
                        f"  - You have sufficient API credits/quota\n"
                        f"  - The model name is valid for your API provider\n\n"
                        f"Error details: {error_msg}"
                    ) from None
                elif isinstance(e, ValueError):
                    raise
                else:
                    # For any other error, show a clean message
                    raise RuntimeError(
                        f"An error occurred while generating summary: {error_msg}"
                    ) from None
