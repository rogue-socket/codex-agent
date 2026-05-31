# Codex Agent Usage Guide

Use this package when you want local Codex to act as a generic LLM inside
another tool, agent, workflow, or test harness.

The key rule: workflow code should depend on `LanguageModel`, not on subprocess
or Codex CLI details. That makes workflows easy to test and keeps Codex as one
pluggable implementation.

Real `CodexLLM` calls use the caller's local Codex CLI authentication. Keep
automated tests on fake models unless you intentionally want an integration run
that exercises local Codex access.

## Main Concepts

`LanguageModel` is the generic protocol:

```python
def complete(self, prompt: str) -> LLMResult:
    ...
```

`CodexLLM` implements that protocol with local `codex exec --json`.

`LLMResult` is the generic response shape:

- `returncode`: provider or process return code.
- `text`: final model response, if available.
- `stdout`: raw standard output.
- `stderr`: raw standard error.
- `raw`: provider-specific result for advanced callers.

`SkillRunner` is a small helper that combines a command, a prompt builder, and a
model.

## Direct Codex LLM Use

```python
from codex_agent import CodexExecConfig, CodexLLM

model = CodexLLM(
    CodexExecConfig(
        codex_bin="codex",
        cwd="/path/to/project",
        model="gpt-5.5",
        profile="default",
        sandbox="workspace-write",
    )
)

result = model.complete("Review the API boundary in this project.")

if not result.ok:
    raise RuntimeError(result.stderr)

print(result.text)
```

`CodexLLM` writes a temporary `--output-last-message` file unless the config
already provides one. The final assistant message is returned as `result.text`.

## CodexExecConfig

Common fields:

- `codex_bin`: command or path for Codex. Default: `codex`.
- `cwd`: working directory passed through `codex exec --cd`.
- `model`: value for `--model`.
- `profile`: value for `--profile`.
- `sandbox`: value for `--sandbox`.
- `output_schema`: optional path passed to `--output-schema`.
- `output_last_message`: optional path passed to `--output-last-message`.
- `extra_config`: tuple of repeated `--config` values.
- `ephemeral`: adds `--ephemeral`.
- `skip_git_repo_check`: adds `--skip-git-repo-check`.
- `prompt_via_stdin`: sends the prompt through stdin and passes `-` to Codex.
- `timeout_seconds`: optional subprocess timeout for real Codex calls.

## Generic Skill Runner

Use `SkillRunner` when a workflow turns a short command into a full prompt.

```python
from codex_agent import CodexLLM, SkillRunner


def build_prompt(command: str) -> str:
    return f"""
You are operating my custom workflow.

Follow the project rules and complete this request:
{command}
"""


runner = SkillRunner(model=CodexLLM(), prompt_builder=build_prompt)
result = runner.run("add validation tests for invalid emails")
print(result.text)
```

## Building A Workflow

Keep the workflow-specific code separate from the model implementation:

```python
from dataclasses import dataclass
from pathlib import Path

from codex_agent import LLMResult, LanguageModel, SkillRunner


@dataclass(frozen=True)
class WorkflowPaths:
    project_dir: Path


def build_workflow_prompt(command: str, paths: WorkflowPaths) -> str:
    return f"""
Project directory: {paths.project_dir.resolve()}

User request:
{command}
"""


def run_workflow(
    command: str,
    paths: WorkflowPaths,
    model: LanguageModel,
) -> LLMResult:
    runner = SkillRunner(
        model=model,
        prompt_builder=lambda text: build_workflow_prompt(text, paths),
    )
    return runner.run(command)
```

Application wiring can then provide Codex:

```python
from pathlib import Path

from codex_agent import CodexExecConfig, CodexLLM

paths = WorkflowPaths(project_dir=Path.cwd())
model = CodexLLM(CodexExecConfig(cwd=paths.project_dir))
result = run_workflow("summarize the current design", paths, model)
```

Tests can provide a fake model:

```python
from codex_agent import LLMResult


class FakeModel:
    def complete(self, prompt: str) -> LLMResult:
        assert "User request:" in prompt
        return LLMResult(returncode=0, text="done")
```

## When To Use The Low-Level Engine

Most workflows should use `CodexLLM`. Import from `codex_agent.engine` only when
you need direct access to raw JSONL events or exact command construction.

```python
from codex_agent.engine.codex_exec import CodexExecConfig, run_codex_exec

result = run_codex_exec(CodexExecConfig(model="gpt-5.5"), "do work")
print(result.events)
```

## Safety Notes

- Do not run real Codex calls in automated tests. Use a fake `LanguageModel` or
  monkeypatch `run_codex_exec`.
- Be explicit when a command will use local Codex authentication or local project
  filesystem access.
- Keep workflow-specific prompts and paths outside this package. This package is
  only the reusable Codex agent core.
