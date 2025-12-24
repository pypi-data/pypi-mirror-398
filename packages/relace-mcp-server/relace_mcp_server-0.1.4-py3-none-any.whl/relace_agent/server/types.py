from __future__ import annotations

from typing import ClassVar

from pydantic import (
    BaseModel,
)
from sse_starlette import ServerSentEvent


class BaseEvent(BaseModel):
    event_type: ClassVar[str | None] = None

    def to_sse(self) -> ServerSentEvent:
        return ServerSentEvent(
            event=self.event_type,
            data=self.model_dump_json(exclude_none=True),
        )


class AgentEvent(BaseEvent):
    event_type: ClassVar[str | None] = "agent"

    name: str
    content: str


class ToolEvent(BaseEvent):
    event_type: ClassVar[str | None] = "tool"

    name: str
    path: str | None = None
    query: str | None = None
    command: str | None = None

    # Report back tool
    explanation: str | None = None
    files: dict[str, list[tuple[int, int]]] | None = None
