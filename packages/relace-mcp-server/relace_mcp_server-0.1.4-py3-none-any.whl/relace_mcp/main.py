import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path

from fastmcp import Context as MCPContext
from fastmcp import FastMCP

from relace_agent.agents import Agent
from relace_agent.config import AgentConfig, LiteralPrompt
from relace_agent.context import ChatHistory, Context, EventStream
from relace_agent.server.types import AgentEvent, ToolEvent
from relace_toolbox.local_client import ToolboxClient
from relace_toolbox.tools import ReportBackToolSchema

REQUIRED_ENV_VARS = ["RELACE_API_KEY"]

missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing)}. "
        f"Set these in your MCP server config or shell environment."
    )

# Check for ripgrep availability
if not shutil.which("rg"):
    raise RuntimeError(
        "ripgrep (rg) is not installed or not available in PATH. "
        "See installation instructions at https://github.com/BurntSushi/ripgrep?tab=readme-ov-file#installation"
    )

logging.basicConfig(
    level=logging.WARNING,  # Root logger at WARNING to suppress dependencies
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Set first-party loggers to DEBUG/INFO
for logger_name in [
    "relace_mcp",
    "relace_agent",
    "relace_toolbox",
]:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

mcp = FastMCP("Relace MCP Server")

FAS_TOOLS = [
    "view_file",
    "view_directory",
    "grep_search",
    "bash",
    "report_back",
]

FAS_SYSTEM_PROMPT = """
You are an AI agent whose job is to explore a code base with the provided tools and thoroughly understand the problem.
You should use the tools provided to explore the codebase, read files, search for specific terms, and execute bash
commands as needed. Once you have a good understanding of the problem, use the `report_back` tool share your findings.
Make sure to only use the `report_back` tool when you are confident that you have gathered enough information to make
an informed decision. Your objective is speed and efficiency so call multiple tools at once where applicable to reduce
latency and reduce the number of turns. You are given a limited number of turns so aim to call 4-12 tools in parallel.
You are suggested to explain your reasoning for the tools you choose to call before calling them.
"""

FAS_USER_PROMPT = """
I have uploaded a code repository in the ${{ context.workdir }} directory.

Now consider the following user query:

<user_query>
${{ inputs.query }}
</user_query>

You need to resolve the <user_query>.

To do this, follow the workflow below:

---
Your job is purely to understand the codebase.
### 1. Explore and Understand the Codebase

You **must first build a deep understanding of the relevant code**.
Use the available tools to:

- Locate and examine all relevant parts of the codebase.
- Understand how the current code works, including expected behaviors, control flow, and edge cases.
- Identify the potential root cause(s) of the issue or the entry points for the requested feature.
- Review any related unit tests to understand expected behavior.

---

### 2. Report Back Your Understanding

Once you believe you have a solid understanding of the issue and the relevant code:

- Use the `report_back` tool to report you findings.
    - File paths should be relative to the working directory; failure to comply will result in deductions.
    - Only report the relevant files within the repository. You may speculate that a file or folder may be added in your explaination, but it must not be put within you reported files.

---

### Success Criteria

A successful resolution means:

- The specific issue in the <user_query> is well understood.
- Your explain clearly the reasoning behind marking code as relavent.
- The files comprehensively covers all the key files needed to address the query.
    - Relevant files can be any of three types:
    - Files needing edits
    - Files providing needed provide the required edits


<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Prioritize calling tools simultaneously whenever the actions can be done in parallel rather than sequentially. For example, when reading 3 files, run 3 tool calls in parallel to read all 3 files into context at the same time. Maximize use of parallel tool calls where possible to increase speed and efficiency. However, if some tool calls depend on previous calls to inform dependent values like the parameters, do NOT call these tools in parallel and instead call them sequentially. Never use placeholders or guess missing parameters in tool calls.
Parallel tool calls can be made using the following schema:
<tool_call>
<function=example_function_name_1>
<parameter=example_parameter_1>
value_1\n</parameter>
<parameter=example_parameter_2>
</parameter>
</function>
<function=example_function_name_2>
<parameter=example_parameter_1>
value_1
</parameter>
<parameter=example_parameter_2>
</parameter>
</function>
</tool_call>
Where you can place as many <function=...>...</function> tags as you want within the <tool_call>...</tool_calls> tags for parallel tool calls.
</use_parallel_tool_calls>
</use_parallel_tool_calls>
"""


@mcp.tool
async def relace_search(
    query: str,
    workdir: str,
    ctx: MCPContext,
) -> dict[str, list[tuple[int, int]]]:
    """Agentic codebase search powered by Relace. Use when finding files to modify or answering questions requiring deep search.

    Args:
        query: Specific, human-readable search query (avoid minimal keywords).
            Examples:
            - "Find where user authentication tokens are validated"
            - "How does the payment processing flow work?"
            - "Where are database migrations defined and executed?"
        workdir: Absolute path to search directory.
    """

    workdir_path = Path(workdir)
    if not workdir_path.is_dir():
        raise NotADirectoryError(f"Workdir is not a directory: {workdir}")

    event_stream = EventStream()

    async def _run_agent() -> None:
        try:
            agent = Agent(
                config=AgentConfig(
                    name="relace-search",
                    model_name="relace-search",
                    prompts=LiteralPrompt(
                        system_prompt=FAS_SYSTEM_PROMPT,
                        user_prompt=FAS_USER_PROMPT,
                    ),
                    tools=FAS_TOOLS,
                ),
            )
            agent_context = Context(
                prompt_cache_key=f"fas-{uuid.uuid4()}",
                toolbox=ToolboxClient(),
                toolbox_workdir=workdir_path,
                inputs={
                    "query": query,
                },
                history=ChatHistory(max_messages=None),
                events=event_stream,
            )
            await agent.run_loop(agent_context)
        finally:
            await event_stream.close()

    agent_task = asyncio.create_task(_run_agent())

    # Process events concurrently with agent execution
    final_result: dict[str, list[tuple[int, int]]] | None = None
    try:
        tool_call_count = 0
        async for event in event_stream:
            logger.info("Event: %s", event)

            # Emit tool calls as progress notifications to make them visible in Cursor
            if isinstance(event, ToolEvent):
                tool_call_count += 1

                # Format tool call information for progress notification
                tool_info = f"🔧 {event.name}"
                if event.path:
                    tool_info += f": {event.path}"
                elif event.query:
                    query_preview = (
                        event.query[:50] + "..."
                        if len(event.query) > 50
                        else event.query
                    )
                    tool_info += f": {query_preview}"
                elif event.command:
                    cmd_preview = (
                        event.command[:50] + "..."
                        if len(event.command) > 50
                        else event.command
                    )
                    tool_info += f": {cmd_preview}"

                # Report progress to make tool calls visible in Cursor's chat
                await ctx.report_progress(
                    progress=tool_call_count,
                    message=tool_info,
                )
                await ctx.info(message=tool_info)

                # Check if this is the final report_back event
                if event.name == ReportBackToolSchema.tool_name:
                    if not event.files:
                        raise RuntimeError("Missing files in report back event")
                    final_result = event.files
            elif isinstance(event, AgentEvent):
                # Show agent messages as progress
                content_preview = (
                    event.content[:100] + "..."
                    if len(event.content) > 100
                    else event.content
                )
                await ctx.report_progress(
                    progress=0,
                    message=f"💭 {content_preview}",
                )
                await ctx.info(message=f"💭 Agent: {content_preview}")
    except Exception as e:
        await ctx.error(message=f"Error processing events: {e}")
        raise
    finally:
        if not agent_task.done():
            agent_task.cancel()

    if final_result is not None:
        return final_result

    raise RuntimeError("No report back event emitted")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
