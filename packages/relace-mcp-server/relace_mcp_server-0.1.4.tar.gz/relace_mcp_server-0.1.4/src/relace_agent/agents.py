from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import cast, override

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
)

from relace_agent.config import AgentConfig, AgentConfigOverrides
from relace_agent.context import (
    AssistantMessage,
    Context,
    ToolUse,
    UserMessage,
)
from relace_agent.errors import AgentError, AgentStop
from relace_agent.server.types import (
    AgentEvent,
    ToolEvent,
)
from relace_toolbox.errors import ExitAgentLoop, ToolError
from relace_toolbox.tools import ToolSchema
from relace_toolbox.types import ToolResult

logger = logging.getLogger(__name__)


class Agent:
    def __init__(
        self,
        config: AgentConfig,
        config_overrides: AgentConfigOverrides | None = None,
    ) -> None:
        if config_overrides is not None:
            logger.info("Applying config overrides: %s", config_overrides)
            config = config.with_overrides(config_overrides)

        self.config: AgentConfig = config
        self.inference_provider: InferenceProvider = RelaceInferenceProvider(config)

    async def format_tool_definitions(
        self, context: Context
    ) -> list[ChatCompletionToolParam]:
        tool_specs = await context.toolbox.tool_specs()
        return [
            tool_spec.tool_schema
            for tool_spec in tool_specs.values()
            if tool_spec.tool_name in self.config.tools
        ]

    def format_system_prompt(
        self, context: Context
    ) -> ChatCompletionSystemMessageParam:
        return {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": context.interpolate(self.config.prompts.system_prompt),
                }
            ],
        }

    def format_history(self, context: Context) -> list[ChatCompletionMessageParam]:
        return context.history.as_params()

    async def generate_response(self, context: Context) -> ChatCompletion:
        return await self.inference_provider.generate_response(
            context=context,
            config=self.config,
            messages=[
                self.format_system_prompt(context),
                *self.format_history(context),
            ],
            tools=await self.format_tool_definitions(context),
        )

    async def handle_response(
        self,
        context: Context,
        response: ChatCompletion,
    ) -> None:
        logger.info("Agent response: %s", response)
        context.history.record_usage(response.usage)

        # Configured for one choice only
        choice = response.choices[0]
        if choice.message.tool_calls:
            logger.info("Agent performing tool calls")
            if choice.message.content:
                await context.events.emit(
                    AgentEvent(
                        name=self.config.name,
                        content=choice.message.content,
                    )
                )
            # Execute all tool calls concurrently
            tool_call_tasks = [
                self.handle_tool_call(
                    context=context,
                    tool_call=cast(ChatCompletionMessageToolCall, tool_call),
                )
                for tool_call in choice.message.tool_calls
            ]
            # NOTE: AgentStop may cause cancellation of other tool calls
            results = await asyncio.gather(*tool_call_tasks)
            tool_results = {
                tool_call.id: result
                for tool_call, result in zip(
                    choice.message.tool_calls, results, strict=True
                )
            }
            context.history.append(
                ToolUse(message=choice.message, results=tool_results)
            )
        elif choice.finish_reason == "stop":
            logger.info("Agent stopped naturally: %s", choice.finish_reason)
            if choice.message.content:
                await context.events.emit(
                    AgentEvent(name=self.config.name, content=choice.message.content)
                )
                context.history.append(AssistantMessage(content=choice.message.content))
            raise AgentStop(choice.finish_reason)
        else:
            logger.error("Agent stopped unexpectedly: %s", choice.finish_reason)
            raise AgentError(f"Agent stopped unexpectedly: {choice.finish_reason}")

    async def handle_tool_call(
        self,
        context: Context,
        tool_call: ChatCompletionMessageToolCall,
    ) -> ToolResult:
        try:
            tool_schema = ToolSchema.from_name(tool_call.function.name)
            tool_input = tool_schema.model_validate_json(tool_call.function.arguments)
            tool_event = tool_input.event_data()
        except Exception as exc:
            # NOTE: This may happen due to a mismatch between the schema version in
            # the agent runtime and toolbox. We try to process the tool call in this
            # case - if the input is actually malformed, we will get a ToolError below.
            # We may want to delegate event data construction to the toolbox later to
            # avoid this issue.
            logger.warning("Failed to parse tool event: %s", exc)
            tool_event = {}

        try:
            await context.events.emit(
                ToolEvent(
                    name=tool_call.function.name,
                    **tool_event,
                )
            )
            tool_spec = await context.toolbox.tool_spec(tool_call.function.name)
            return await context.toolbox.tool_call(
                tool_name=tool_call.function.name,
                tool_input=tool_call.function.arguments,
                workdir=context.toolbox_workdir,
                chat_history=context.history.tokenize()
                if tool_spec.requires_chat_history
                else None,
            )
        except ExitAgentLoop as exit_signal:
            raise AgentStop("Tool emitted exit signal") from exit_signal
        except ToolError as error:
            logger.warning("Tool error: %s", error)
            return ToolResult(message=f"Error: {error}")

    async def run_loop(self, context: Context) -> None:
        """Run the agent with the given query."""
        user_prompt = self.config.prompts.user_prompt

        context.history.append(UserMessage(content=context.interpolate(user_prompt)))
        turn = 0
        while turn < self.config.max_turns:
            turn += 1
            response = await self.generate_response(context)

            try:
                await self.handle_response(context, response)
            except AgentStop:
                break
        else:
            logger.warning("Agent reached turn limit: %s", self.config.max_turns)


class InferenceProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        context: Context,
        config: AgentConfig,
        messages: list[ChatCompletionMessageParam],
        tools: list[ChatCompletionToolParam],
    ) -> ChatCompletion:
        """Generate a response from the model."""
        ...


class RelaceInferenceProvider(InferenceProvider):
    def __init__(self, config: AgentConfig) -> None:
        self.client = AsyncOpenAI(
            api_key=os.environ["RELACE_API_KEY"],
            base_url="https://search.endpoint.relace.run/v1/search",
            timeout=config.prompt_timeout,
            max_retries=config.prompt_retries,
        )

    @override
    async def generate_response(
        self,
        context: Context,
        config: AgentConfig,
        messages: list[ChatCompletionMessageParam],
        tools: list[ChatCompletionToolParam],
    ) -> ChatCompletion:
        response = await self.client.chat.completions.create(
            prompt_cache_key=context.prompt_cache_key,  # results in sticky routing by key
            messages=messages,
            model=config.model_name,
            tools=tools,
            max_tokens=config.max_tokens,
        )
        if not response.choices:
            raise RuntimeError("Received empty choices")
        return response
