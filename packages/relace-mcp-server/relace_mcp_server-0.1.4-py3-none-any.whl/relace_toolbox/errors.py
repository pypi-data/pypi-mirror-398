from __future__ import annotations

from typing import ClassVar


class ToolError(Exception):
    """Base class for custom errors in relace-toolbox."""

    error_code: ClassVar[str] = "unknown_tool_error"

    _error_lookup: dict[str, type[ToolError]] = {}

    def __init_subclass__(cls) -> None:
        if cls.error_code in cls._error_lookup:
            raise ValueError(f"Duplicate error code: {cls.error_code}")
        cls._error_lookup[cls.error_code] = cls
        return super().__init_subclass__()

    def to_json(self) -> dict[str, str]:
        return {
            "error_code": self.error_code,
            "message": str(self),
        }

    @classmethod
    def from_json(cls, data: dict[str, str]) -> ToolError:
        error_code = data.get("error_code", "unknown_tool_error")
        error_class = cls._error_lookup.get(error_code, ToolError)
        message = data.get("message", "")
        return error_class(message)


class InvalidToolName(ToolError):
    """The provided tool name is not recognized."""

    error_code = "invalid_tool_name"


class InvalidToolInput(ToolError):
    """The provided tool input does not conform to the tool's schema, or is otherwise invalid/forbidden."""

    error_code = "invalid_tool_input"


class ToolExecutionError(ToolError):
    """An error occurred while the tool was executing."""

    error_code = "tool_execution_error"


class ToolExecutionTimeout(ToolError):
    """The tool execution, or one of its dependencies, exceeded the allowed time limit."""

    error_code = "tool_execution_timeout"


class ExitAgentLoop(ToolError):
    """Signal for the agent to exit its loop."""

    error_code = "exit_agent_loop"
