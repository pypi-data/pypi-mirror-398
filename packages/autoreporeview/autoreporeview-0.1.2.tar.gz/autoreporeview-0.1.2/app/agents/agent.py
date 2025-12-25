from typing import Sequence
from uuid import uuid4
from opentelemetry import trace
from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

tracer = trace.get_tracer(__name__)


class Agent:
    def __init__(self, model: LanguageModelLike, tools: Sequence[BaseTool]) -> None:
        self.model = model
        self.agent = create_react_agent(
            model,
            tools,
            checkpointer=InMemorySaver(),
        )
        self.config: RunnableConfig = {"configurable": {"thread_id": uuid4().hex}}

    def invoke(self, content: str, temperature: float = 0.1) -> str:
        with tracer.start_as_current_span("agent.invoke") as span:
            span.set_attribute("temperature", temperature)
            span.set_attribute("content_length", len(content))

            message = {
                "role": "user",
                "content": content,
            }

            invocation = self.agent.invoke(
                {
                    "messages": [message],
                    "temperature": temperature,
                },
                config=self.config,
            )

            response = invocation["messages"][-1].content

            if not isinstance(response, str):
                raise ValueError("Agent response is not a string")

            span.set_attribute("response_length", len(response))
            return response
