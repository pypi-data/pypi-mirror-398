from typing import Awaitable, Callable
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
    ModelCallResult,
)

from gynews3.agent.news_finder.prompt import main_instruction


class PromptState(AgentState):
    location: str


class PromptMiddleware(AgentMiddleware):
    state_schema = PromptState

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        system_prompt = main_instruction.format(location=request.state["location"])
        request.system_prompt = (
            system_prompt + "\n\n" + request.system_prompt
            if request.system_prompt
            else system_prompt
        )
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        system_prompt = main_instruction.format(location=request.state["location"])
        request.system_prompt = (
            system_prompt + "\n\n" + request.system_prompt
            if request.system_prompt
            else system_prompt
        )
        return await handler(request)
