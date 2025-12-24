import logging
from pathlib import Path

from relace_toolbox.errors import (
    InvalidToolName,
    ToolError,
    ToolExecutionError,
    ToolExecutionTimeout,
)
from relace_toolbox.tools import Tool, ToolContext
from relace_toolbox.types import ToolResult, ToolSpec

logger = logging.getLogger(__name__)


class ToolboxClient:
    async def tool_specs(self) -> dict[str, ToolSpec]:
        return {
            tool.schema.tool_name: ToolSpec(
                tool_name=tool.schema.tool_name,
                tool_schema=tool.schema.openai(),
                requires_chat_history=tool.requires_chat_history,
            )
            for tool in Tool.all_tools()
        }

    async def tool_spec(self, tool_name: str) -> ToolSpec:
        tool_specs = await self.tool_specs()
        try:
            return tool_specs[tool_name]
        except KeyError as e:
            raise InvalidToolName(tool_name) from e

    async def tool_call(
        self,
        tool_name: str,
        tool_input: str,
        workdir: Path,
        chat_history: str | None = None,
    ) -> ToolResult:
        tool = Tool.from_name(tool_name)
        try:
            tool_result = await tool.execute(
                tool_input=tool.schema.from_json_str(tool_input),
                context=ToolContext(
                    workdir=workdir,
                    chat_history=chat_history,
                ),
            )
            return tool_result
        except ToolError as exc:
            logger.warning("Explicit tool error", exc_info=True)
            raise exc
        except TimeoutError as exc:
            raise ToolExecutionTimeout("Tool execution timed out") from exc
        except Exception as exc:
            logger.warning(f"Unexpected tool error: {exc}", exc_info=True)
            raise ToolExecutionError(f"{exc.__class__.__name__}: {exc!s}") from exc
