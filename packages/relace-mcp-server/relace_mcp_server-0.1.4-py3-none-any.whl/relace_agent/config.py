from pathlib import Path
from typing import ClassVar, Self, TypedDict

from pydantic import BaseModel, ConfigDict
from pydantic_yaml import parse_yaml_file_as

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config"
EVAL_CONFIG_ROOT = CONFIG_ROOT / "evals"
API_CONFIG_ROOT = CONFIG_ROOT / "api"


class ChatMessage(TypedDict):
    role: str
    content: str


class BaseConfig(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class FileConfig(BaseConfig):
    @classmethod
    def load(cls, path: Path) -> Self:
        return parse_yaml_file_as(cls, path)


class LiteralPrompt(BaseModel):
    system_prompt: str
    user_prompt: str


class AgentConfigOverrides(BaseModel):
    prompts: LiteralPrompt
    tools: list[str] | None = None
    model_name: str | None = None
    max_tokens: int | None = None
    max_turns: int | None = None
    prompt_timeout: int | None = None  # seconds
    prompt_retries: int | None = None


class AgentConfig(BaseConfig):
    name: str
    prompts: LiteralPrompt
    tools: list[str]

    model_name: str = "relace-search"
    max_tokens: int = 8192
    max_turns: int = 200
    prompt_timeout: int = 180  # 3 minutes
    prompt_retries: int = 1

    def with_overrides(self, overrides: AgentConfigOverrides) -> Self:
        return self.model_validate(
            self.model_dump() | overrides.model_dump(exclude_none=True),
            strict=True,
        )
