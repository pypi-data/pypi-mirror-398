from __future__ import annotations

import asyncio
import logging
import re
import shlex
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Self, final, override

import aiofiles
from openai import pydantic_function_tool
from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel, Field, ValidationError, field_validator

from relace_toolbox.errors import (
    ExitAgentLoop,
    InvalidToolInput,
    InvalidToolName,
    ToolExecutionError,
    ToolExecutionTimeout,
)
from relace_toolbox.types import ToolResult

logger = logging.getLogger(__name__)


class ToolSchema(BaseModel):
    """Base class for tool input parameters."""

    tool_name: ClassVar[str]
    tool_description: ClassVar[str]

    _tool_lookup: ClassVar[dict[str, type[ToolSchema]]] = {}

    def __init_subclass__(
        cls,
        name: str,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        description = description or cls.__doc__
        if not description:
            raise ValueError(f"{cls.__name__} is missing a docstring or description")
        cls.tool_name = name
        cls.tool_description = description.strip()
        cls._tool_lookup[name] = cls

    @classmethod
    def from_name(cls, tool_name: str) -> type[ToolSchema]:
        try:
            return cls._tool_lookup[tool_name]
        except KeyError as e:
            raise InvalidToolName(tool_name) from e

    @classmethod
    def openai(cls) -> ChatCompletionToolParam:
        schema = pydantic_function_tool(
            model=cls,
            name=cls.tool_name,
            description=cls.tool_description,
        )

        # Remove unsupported 'format' from schema for Path fields, recursively
        def remove_path_format(obj: Any) -> None:
            if isinstance(obj, dict):
                if obj.get("format") == "path":
                    obj.pop("format")
                for val in obj.values():
                    remove_path_format(val)
            elif isinstance(obj, list):
                for item in obj:
                    remove_path_format(item)

        schema_params = schema["function"]["parameters"]
        remove_path_format(schema_params)
        return schema

    @classmethod
    def from_json_str(cls, json_str: str) -> Self:
        try:
            return cls.model_validate_json(json_str)
        except ValidationError as e:
            raise InvalidToolInput(json_str) from e

    @classmethod
    def from_json_dict(cls, json_dict: dict[str, Any]) -> Self:
        try:
            return cls.model_validate(json_dict)
        except ValidationError as e:
            raise InvalidToolInput(json_dict) from e

    def event_data(self) -> dict[str, Any]:
        """Optional event data to include in event stream when calling this tool."""
        return {}


@dataclass
class ToolContext:
    workdir: Path
    chat_history: str | None


class Tool[S: ToolSchema](ABC):
    """Base class for tools that an agent can use."""

    schema: ClassVar[type[S]]
    requires_chat_history: ClassVar[bool] = False

    _tools: ClassVar[dict[str, type[Tool[ToolSchema]]]] = {}

    def __init_subclass__(
        cls,
        schema: type[S],
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        cls.schema = schema
        cls._tools[schema.tool_name] = cls  # type: ignore

    @abstractmethod
    async def execute(
        self,
        tool_input: S,
        context: ToolContext,
    ) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            tool_input: Structured, validated input arguments for the tool.
        """
        ...

    @classmethod
    def from_name(cls, name: str) -> Tool[ToolSchema]:
        try:
            return cls._tools[name]()
        except KeyError as e:
            raise InvalidToolName(name) from e

    @classmethod
    def all_tools(cls) -> list[type[Tool[ToolSchema]]]:
        return list(cls._tools.values())


class BashToolSchema(ToolSchema, name="bash"):
    """Tool for executing bash commands.

    * Avoid long running commands
    * Avoid dangerous/destructive commands
    * Prefer using other more specialized tools where possible
    """

    command: str = Field(..., description="Bash command to execute")

    @override
    def event_data(self) -> dict[str, str]:
        return {"command": self.command}


@final
class BashTool(Tool[BashToolSchema], schema=BashToolSchema):
    timeout: ClassVar[int] = 3
    text_limit: ClassVar[int] = 5_000

    @override
    async def execute(
        self,
        tool_input: BashToolSchema,
        context: ToolContext,
    ) -> ToolResult:
        def truncate(text: str) -> str:
            if len(text) > self.text_limit:
                return (
                    f"{text[: self.text_limit]}\n"
                    f"...truncated to {self.text_limit} characters ..."
                )
            return text

        try:
            # Execute the bash command and capture output
            command = correct_bash_paths(tool_input.command, context.workdir)
            proc = await asyncio.create_subprocess_shell(
                # NOTE: We must run in a clean login shell to prevent the toolbox
                # venv from superceding system python and PYTHONPATH
                f"env -i bash -lc {shlex.quote(command)}",
                cwd=context.workdir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout,
            )
        except TimeoutError as e:
            raise ToolExecutionTimeout(
                f"Command timed out after {self.timeout} seconds."
            ) from e

        if proc.returncode != 0:
            raise ToolExecutionError(
                f"Command failed with exit code {proc.returncode}.\n"
                f"STDOUT:\n{truncate(stdout.decode())}\n"
                f"STDERR:\n{truncate(stderr.decode())}"
            )
        return ToolResult(message=truncate(stdout.decode()))


class DirectoryViewToolSchema(ToolSchema, name="view_directory"):
    """Tool for viewing the contents of a directory.

    * Lists contents recursively, relative to the input directory
    * Directories are suffixed with a trailing slash '/'
    * Depth might be limited by the tool implementation
    * Output is limited to the first 250 items

    Example output:
    file1.txt
    file2.txt
    subdir1/
    subdir1/file3.txt
    """

    path: Path = Field(
        ...,
        description="Absolute path to a directory, e.g. `/repo/`.",
    )
    include_hidden: bool = Field(
        False,
        description="If true, include hidden files in the output (false by default).",
    )

    @override
    def event_data(self) -> dict[str, str]:
        return {"path": str(self.path)}


class DirectoryViewTool(Tool[DirectoryViewToolSchema], schema=DirectoryViewToolSchema):
    limit: ClassVar[int] = 250

    @override
    async def execute(
        self,
        tool_input: DirectoryViewToolSchema,
        context: ToolContext,
    ) -> ToolResult:
        tool_input.path = correct_path(tool_input.path, context.workdir)
        check_path(tool_input.path, context.workdir, must_exist=True, file_ok=False)

        i = 0
        contents = []
        for item in tool_input.path.rglob("*"):
            i += 1
            if i > self.limit:
                contents.append("... remaining items omitted ...")
                break

            if not tool_input.include_hidden and item.name.startswith("."):
                continue

            relative_path = (
                item.relative_to(context.workdir) if context.workdir else item
            )
            if item.is_dir():
                contents.append(f"{relative_path}/")
            else:
                contents.append(f"{relative_path}")

        return ToolResult(
            message="\n".join(contents) if contents else "Directory is empty."
        )


class FileViewToolSchema(ToolSchema, name="view_file"):
    """Tool for viewing/exploring the contents of existing files

    Line numbers are included in the output, indexing at 1. If the output does not
    include the end of the file, it will be noted after the final output line.

    Example (viewing the first 2 lines of a file):
    1\tdef my_function():
    2\t    print("Hello, World!")
    ... rest of file truncated ...
    """

    path: Path = Field(
        ...,
        description="Absolute path to a file, e.g. `/repo/file.py`.",
    )
    # TODO: Split this into two integers for more precise validation
    # NOTE: Tuple validation is not supported by the OpenAI API, so we cannot do that
    view_range: list[int] = Field(
        [1, 100],
        description="Range of file lines to view. If not specified, the first 100 lines "
        "of the file are shown. If provided, the file will be shown in the indicated "
        "line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to "
        "start. Setting `[start_line, -1]` shows all lines from `start_line` to the end "
        "of the file.",
    )

    @override
    def event_data(self) -> dict[str, str]:
        return {"path": str(self.path)}


@final
class FileViewTool(Tool[FileViewToolSchema], schema=FileViewToolSchema):
    @override
    async def execute(
        self,
        tool_input: FileViewToolSchema,
        context: ToolContext,
    ) -> ToolResult:
        tool_input.path = correct_path(tool_input.path, context.workdir)
        check_path(tool_input.path, context.workdir, must_exist=True, dir_ok=False)

        start, end = tool_input.view_range
        view_lines: list[str] = []
        async with aiofiles.open(tool_input.path) as handle:
            for i, line in enumerate(await handle.readlines(), start=1):
                if end != -1 and i > end:
                    view_lines.append("... rest of file truncated ...")
                    break
                if i >= start:
                    view_lines.append(f"{i}\t{line}")

        return ToolResult(message="".join(view_lines))


class RipgrepToolSchema(ToolSchema, name="grep_search"):
    """Fast text-based regex search that finds exact pattern matches within files or
    directories, utilizing the ripgrep command for efficient searching. Results will be
    formatted in the style of ripgrep and can be configured to include line numbers and
    content. To avoid overwhelming output, the results are capped at 50 matches. Use the
    include or exclude patterns to filter the search scope by file type or specific
    paths. This is best for finding exact text matches or regex patterns. More precise
    than semantic search for finding specific strings or patterns. This is preferred
    over semantic search when we know the exact symbol/function name/etc. to search in
    some set of directories/file types.
    """

    query: str = Field(..., description="The regex pattern to search for")
    case_sensitive: bool = Field(
        default=True, description="Whether the search should be case sensitive"
    )
    exclude_pattern: str | None = Field(
        default=None, description="Glob pattern for files to exclude"
    )
    include_pattern: str | None = Field(
        default=None,
        description="Glob pattern for files to include (e.g. '.ts' for TypeScript files)",
    )

    @override
    def event_data(self) -> dict[str, str]:
        return {"query": self.query}


class RipgrepTool(Tool[RipgrepToolSchema], schema=RipgrepToolSchema):
    @override
    async def execute(
        self,
        tool_input: RipgrepToolSchema,
        context: ToolContext,
    ) -> ToolResult:
        args = ["rg", tool_input.query, "./", "--max-count=50", "--color=never"]
        if not tool_input.case_sensitive:
            args.append("--ignore-case")
        if tool_input.exclude_pattern:
            args.append(f"--glob=!{tool_input.exclude_pattern}")
        if tool_input.include_pattern:
            args.append(f"--glob={tool_input.include_pattern}")

        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=context.workdir,
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return ToolResult(message=stdout.decode())
        elif process.returncode == 1:
            return ToolResult(message="No matches found")
        else:
            raise ToolExecutionError(f"Error running ripgrep: {stderr.decode()}")


class ReportBackToolSchema(ToolSchema, name="report_back"):
    """This tool is to be used to terminate the run when you have finished exploring
    the codebase and understand the problem.
    """

    explanation: str = Field(
        ...,
        description="Details your reasoning for deeming the files relevant for solving "
        "the issue.",
    )
    files: dict[str, list[tuple[int, int]]] = Field(
        ...,
        description="Key is a relevant file within the repo. The value is the ranges "
        "of relevant lines within the file.",
    )

    @field_validator("files", mode="before")
    @classmethod
    def validate_files(cls, data: Any) -> Any:
        if isinstance(data, dict):
            output: dict[Any, Any] = {}
            # Handle common invalid inputs for file ranges
            for k, v in data.items():
                if v is None:
                    output[k] = []  # None -> []
                elif (
                    v
                    and isinstance(v, list | tuple)
                    and all(isinstance(i, int) for i in v)
                ):
                    output[k] = [v]  # [1, 2] -> [[1, 2]]
                else:
                    output[k] = v
            return output
        else:
            return data

    @override
    def event_data(self) -> dict[str, Any]:
        return {
            "explanation": self.explanation,
            "files": self.files,
        }


class ReportBackTool(Tool[ReportBackToolSchema], schema=ReportBackToolSchema):
    @override
    async def execute(
        self,
        tool_input: ReportBackToolSchema,
        context: ToolContext,
    ) -> ToolResult:
        raise ExitAgentLoop("Report back to user")


# Relace Search was trained in an environment where the workdir is mounted at /repo.
# This resulted in the model sometimes trying to interact with /repo, even
# when it is prompted to look elsewhere. The following functions are a workaround to
# attempt to correct this defect until a new model is trained.
_REPO_PATH = Path("/repo")
_REPO_PATH_PATTERN = re.compile(r"/repo(?:/[^\s\"';&|<>()]*|\b)")


def correct_bash_paths(command: str, workdir: Path) -> str:
    def replace_path(match: re.Match[str]) -> str:
        path = Path(match.group(0))
        return str(correct_path(path, workdir))

    return _REPO_PATH_PATTERN.sub(replace_path, command)


def correct_path(path: Path, workdir: Path) -> Path:
    if path.is_relative_to(_REPO_PATH) and not _REPO_PATH.is_dir():
        logger.warning("Remapping %s to %s", path, workdir)
        path = workdir / path.relative_to(_REPO_PATH)
    return path


def check_path(
    path: Path,
    workdir: Path,
    must_exist: bool = False,
    must_not_exist: bool = False,
    file_ok: bool = True,
    dir_ok: bool = True,
) -> None:
    if not path.is_relative_to(workdir):
        raise InvalidToolInput(
            f"path is not contained in the working directory: {path}"
        )
    if must_exist and not path.exists():
        raise InvalidToolInput(f"path does not exist: {path}")
    if must_not_exist and path.exists():
        raise InvalidToolInput(f"path already exists: {path}")
    if not file_ok and path.is_file():
        raise InvalidToolInput(f"path is a file: {path}")
    if not dir_ok and path.is_dir():
        raise InvalidToolInput(f"path is a directory: {path}")
