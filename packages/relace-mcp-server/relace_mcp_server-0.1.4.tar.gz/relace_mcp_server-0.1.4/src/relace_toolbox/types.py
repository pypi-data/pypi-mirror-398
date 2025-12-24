import base64
from typing import Literal, Self

from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel


class ToolResult(BaseModel):
    message: str
    image_url: str | None = None

    @classmethod
    def from_image_bytes(
        cls,
        message: str,
        image: bytes,
        image_format: Literal["image/jpeg", "image/png", "image/webp", "image/gif"],
    ) -> Self:
        return cls(
            message=message,
            image_url=f"data:{image_format};base64,{base64.b64encode(image).decode()}",
        )


class ToolSpec(BaseModel):
    tool_name: str
    tool_schema: ChatCompletionToolParam
    requires_chat_history: bool
