# codex-agent

`codex-agent` is a small Python library for using the local Codex CLI as a
pluggable language model inside other tools, agents, and workflow runners.

It wraps `codex exec --json` behind a minimal Python interface so application
code can depend on `LanguageModel` instead of subprocess details. That keeps
workflow code easy to test with fake models while still allowing production
wiring to call local Codex.

It is useful when you want a product, prototype, or internal test harness to use
your authenticated local Codex setup without hard-coding Codex CLI subprocess
calls throughout the application.

## What This Is

- A thin Python adapter around local `codex exec --json`.
- A provider-style `LanguageModel` protocol with a `complete(prompt)` method.
- A generic `LLMResult` response object for text, stdout, stderr, and raw data.
- A lightweight `SkillRunner` helper for turning user commands into prompts.
- A reusable core intended to be embedded in other projects.

## What This Is Not

- Not a hosted service.
- Not a standalone agent runtime.
- Not a prompt framework.
- Not specific to any one workflow or application.
- Not a replacement for the Codex CLI. It expects Codex to be installed and
  authenticated when making real model calls.

## Why It Exists

Agent and workflow projects often need a model interface, but they should not
hard-code `subprocess.run(["codex", ...])` everywhere. This package puts the
Codex CLI integration in one place and gives the rest of the application a small
interface that is easy to mock in tests.

## Install

From this repository:

```bash
python3 -m pip install -e .
```

For local development and tests:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest tests
```

Runtime dependencies: none beyond the Python standard library.

For real Codex calls, you also need the Codex CLI available on `PATH` and
authenticated locally. Unit tests should keep using fakes or monkeypatching so
they do not consume local Codex access.

## Quick Start

```python
from codex_agent import CodexExecConfig, CodexLLM

model = CodexLLM(
    CodexExecConfig(
        model="gpt-5.5",
        sandbox="workspace-write",
        skip_git_repo_check=True,
        timeout_seconds=120,
    )
)

result = model.complete("Summarize this repository in three bullets.")

if result.ok:
    print(result.text)
else:
    print(result.stderr)
```

## Core API

### `LanguageModel`

The protocol application code should depend on:

```python
def complete(self, prompt: str) -> LLMResult:
    ...
```

### `CodexLLM`

The Codex-backed implementation. It calls `codex exec --json` using a
`CodexExecConfig`.

### `LLMResult`

The generic response shape:

- `ok`: true when the process returned `0`.
- `text`: final assistant message, when available.
- `stdout`: raw JSONL output from Codex.
- `stderr`: raw standard error.
- `raw`: provider-specific result object for advanced callers.

### `SkillRunner`

A small helper that combines a command, a prompt builder, and a model:

```python
from codex_agent import CodexLLM, SkillRunner


def build_prompt(command: str) -> str:
    return f"Complete this workflow request:\n{command}"


runner = SkillRunner(model=CodexLLM(), prompt_builder=build_prompt)
result = runner.run("summarize the current project")
```

## Package Layout

```text
codex_agent/
  core/
    llm.py       # LanguageModel, LLMResult, CodexLLM
    skills.py    # generic SkillRunner
  engine/
    codex_exec.py # low-level codex exec --json subprocess wrapper
docs/
  USAGE.md       # detailed guide for agents and developers
tests/
```

## Testing

The tests do not call real Codex. They use fakes and monkeypatching around the
subprocess layer.

```bash
python3 -m pytest tests
```

## Development

```bash
python3 -m pytest tests
python3 -m compileall -q codex_agent tests
```

See [docs/USAGE.md](docs/USAGE.md) for a fuller integration guide with workflow
examples.
