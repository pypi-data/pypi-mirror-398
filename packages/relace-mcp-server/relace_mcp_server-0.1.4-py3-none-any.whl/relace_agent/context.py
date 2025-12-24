from __future__ import annotations

import asyncio
import logging
import re
from abc import ABCMeta, abstractmethod
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Literal, override

from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
)
from pydantic import BaseModel

from relace_agent.server.types import (
    BaseEvent,
)
from relace_toolbox.local_client import ToolboxClient
from relace_toolbox.types import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ShellOutput:
    exit_code: int
    stdout: str
    stderr: str


class BaseChatItem(BaseModel, metaclass=ABCMeta):
    @abstractmethod
    def as_message_params(self) -> list[ChatCompletionMessageParam]: ...


class UserMessage(BaseChatItem):
    role: Literal["user"] = "user"
    content: str

    @override
    def as_message_params(self) -> list[ChatCompletionMessageParam]:
        return [
            {
                "role": self.role,
                "content": [
                    {
                        "type": "text",
                        "text": self.content,
                    }
                ],
            }
        ]


class AssistantMessage(BaseChatItem):
    role: Literal["assistant"] = "assistant"
    content: str

    @override
    def as_message_params(self) -> list[ChatCompletionMessageParam]:
        return [
            {
                "role": self.role,
                "content": self.content,
            }
        ]


class ToolUse(BaseChatItem):
    message: ChatCompletionMessage
    results: dict[str, ToolResult]

    @override
    def as_message_params(self) -> list[ChatCompletionMessageParam]:
        messages: list[ChatCompletionMessageParam] = [
            self.message.model_dump(mode="json", exclude_none=True)  # type: ignore
        ]
        for tool_call_id, result in self.results.items():
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": [
                        {
                            "type": "text",
                            "text": result.message,
                        }
                    ],
                }
            )
            if result.image_url is not None:
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": result.image_url},
                            }
                        ],
                    }
                )
        return messages


# Discriminated union needed for serialization to work correctly
ChatItem = UserMessage | AssistantMessage | ToolUse


# TODO: Intelligent file context (one copy at a time, not written to disk)
# TODO: Intelligent truncation/summarization of history
# TODO: Encapsulate tool definitions and system prompt
class ChatHistory:
    def __init__(
        self,
        max_messages: int | None = 100,
        max_tokens: int = 140_000,
    ) -> None:
        self.messages: deque[ChatItem] = deque(maxlen=max_messages)
        self.max_tokens: int = max_tokens
        self.last_tokens: int = 0

    def append(self, item: ChatItem) -> None:
        self.messages.append(item)

    def as_params(self) -> list[ChatCompletionMessageParam]:
        return [
            param for message in self.messages for param in message.as_message_params()
        ]

    def record_usage(
        self, usage: CompletionUsage | None, auto_clean: bool = True
    ) -> None:
        if usage is not None:
            self.last_tokens = usage.total_tokens
        # Truncate history if we're over our limit
        if auto_clean and self.last_tokens > self.max_tokens:
            self.clean()

    # TODO (eborgnia): This is the simplest solution, but we should consider more sophisticated approaches.
    # - Remove unecessary file reads that pollute the context window.
    # - Delete the center messages instead to not lose the original user intent.
    # - Maintain only summary messages or some kind of markdown log of the changes.
    def clean(self) -> None:
        """
        Simple conversation cleaning by removing the oldest non-user message.
        This helps manage token limits by gradually removing old context.
        """
        logger.info("Cleaning conversation history")
        messages_list = list(self.messages)
        for i, message in enumerate(messages_list[:]):
            if not isinstance(message, UserMessage):
                del messages_list[i]
                self.messages.clear()
                self.messages.extend(messages_list)
                logger.info("Removed message: %s", message)
                break
        else:
            logger.info("No messages to remove from conversation history")

    def tokenize(self) -> str:
        chunks: list[str] = []
        for message in self.messages:
            if isinstance(message, UserMessage):
                chunks.append(f"<user>{message.content}</user>")
            elif isinstance(message, AssistantMessage):
                chunks.append(f"<assistant>{message.content}</assistant>")
            elif isinstance(message, ToolUse) and message.message.tool_calls:
                chunks.extend(
                    f"<tool_call>{tool_call.function.name}</tool_call>"  # type: ignore
                    for tool_call in message.message.tool_calls
                )
        return "\n".join(chunks)


class EventStream:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[BaseEvent | None] = asyncio.Queue()
        self._closed: bool = False

    async def emit(self, event: BaseEvent) -> None:
        if self._closed:
            raise RuntimeError(f"{self.__class__.__name__} is closed")

        await self._queue.put(event)

    async def close(
        self,
        drain: bool = True,
    ) -> None:
        self._closed = True
        self._queue.put_nowait(None)

        if drain:
            await self._queue.join()

    async def __aiter__(self) -> AsyncIterator[BaseEvent]:
        while True:
            event = await self._queue.get()
            try:
                if event is None:
                    break
                yield event
            finally:
                self._queue.task_done()


@dataclass
class Context:
    prompt_cache_key: str
    toolbox: ToolboxClient
    toolbox_workdir: Path = field(default_factory=Path.cwd)
    inputs: dict[str, str] = field(default_factory=dict)
    history: ChatHistory = field(default_factory=ChatHistory)
    events: EventStream = field(default_factory=EventStream)

    _interpolate_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"\$\{\{ (?P<namespace>\w+)(\.(?P<key>\w+))? \}\}"
    )

    def interpolate(self, template: str) -> str:
        def handle_match(match: re.Match[str]) -> str:
            namespace = match.group("namespace")
            key = match.group("key")
            match (namespace, key):
                case ("context", "workdir"):
                    return self.toolbox_workdir.as_posix()
                case ("inputs", input_key):
                    return self.inputs[input_key]
                case _:
                    raise ValueError(f"Invalid substitution: {namespace}.{key}")

        return self._interpolate_pattern.sub(handle_match, template)
