"""Generic LLM facade backed by local Codex."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from codex_agent.engine.codex_exec import (
    CodexExecConfig,
    CodexExecResult,
    run_codex_exec,
)


@dataclass(frozen=True)
class LLMResult:
    returncode: int
    text: str | None
    stdout: str = ""
    stderr: str = ""
    raw: Any | None = None

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @classmethod
    def from_codex_exec(cls, result: CodexExecResult) -> "LLMResult":
        return cls(
            returncode=result.returncode,
            text=result.last_message,
            stdout=result.stdout,
            stderr=result.stderr,
            raw=result,
        )


class LanguageModel(Protocol):
    def complete(self, prompt: str) -> LLMResult:
        """Run a prompt and return the model result."""


@dataclass(frozen=True)
class CodexLLM:
    config: CodexExecConfig = field(default_factory=CodexExecConfig)

    def complete(self, prompt: str) -> LLMResult:
        return LLMResult.from_codex_exec(run_codex_exec(self.config, prompt))
