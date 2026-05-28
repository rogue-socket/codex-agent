"""Generic skill orchestration primitives."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from codex_agent.core.llm import LLMResult, LanguageModel


@dataclass(frozen=True)
class SkillRunner:
    model: LanguageModel
    prompt_builder: Callable[[str], str]

    def run(self, command: str) -> LLMResult:
        return self.model.complete(self.prompt_builder(command))
