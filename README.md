# codex-agent

Reusable Python core for calling local Codex as an LLM inside other tools,
agents, and workflow runners.

This package is intentionally generic. It does not include focusgroup-specific
logic. Workflows should depend on the small `LanguageModel` interface and let
application wiring decide whether to use `CodexLLM`, a fake model in tests, or a
future provider.

## Install

From this directory:

```bash
python3 -m pip install -e .
```

## Quick Start

```python
from codex_agent import CodexExecConfig, CodexLLM

model = CodexLLM(
    CodexExecConfig(
        model="gpt-5.5",
        sandbox="workspace-write",
        skip_git_repo_check=True,
    )
)

result = model.complete("Summarize this repository in three bullets.")

if result.ok:
    print(result.text)
else:
    print(result.stderr)
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

## Development

```bash
python3 -m pytest tests
python3 -m compileall -q codex_agent tests
```

See [docs/USAGE.md](docs/USAGE.md) for the full integration guide.
