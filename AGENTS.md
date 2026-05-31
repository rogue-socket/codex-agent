# Repository Guidelines

## Project Structure & Module Organization

`codex-agent` is a small Python package that wraps local `codex exec --json` behind a pluggable LLM interface.

- `codex_agent/core/`: public-facing model abstractions, including `LanguageModel`, `LLMResult`, `CodexLLM`, and `SkillRunner`.
- `codex_agent/engine/`: low-level subprocess integration for building and running Codex CLI commands.
- `tests/`: pytest coverage for the core facade and Codex subprocess wrapper. Tests use fakes and monkeypatching, not real Codex calls.
- `docs/USAGE.md`: integration guidance and usage examples.
- `README.md`: project overview, install instructions, API summary, and quick-start examples.

## Build, Test, and Development Commands

- `python3 -m pip install -e ".[dev]"`: install the package locally with pytest.
- `python3 -m pytest tests`: run the test suite.
- `python3 -m compileall -q codex_agent tests`: check that package and test files compile.

There is no dedicated build, lint, or formatting command configured in `pyproject.toml`; do not invent one without adding the corresponding tooling.

## Coding Style & Naming Conventions

Target Python 3.10 or newer. Use four-space indentation, `snake_case` for functions and modules, `CamelCase` for classes, and descriptive dataclass field names. Keep imports grouped as standard library first, then local package imports.

Prefer small dataclasses and typed functions, matching the existing style in `codex_agent/core/llm.py` and `codex_agent/engine/codex_exec.py`. Keep changes minimal and avoid speculative abstractions around the subprocess layer.

## Testing Guidelines

Use pytest. Name tests `test_<behavior>` and place them in `tests/test_*.py`. Tests that touch Codex execution should monkeypatch `subprocess.run` or higher-level wrappers so they do not require Codex to be installed or authenticated.

Run the narrowest relevant test first, then `python3 -m pytest tests` before finishing code changes.

## Commit & Pull Request Guidelines

The current history uses short, sentence-case commit subjects such as `Clarify project purpose` and `Initial commit`. Keep commit messages concise and imperative.

Pull requests should include a brief summary, the verification commands run, and any behavior changes. Link related issues when available. Add screenshots only when changing user-facing documentation rendering or visual assets.

## Security & Configuration Tips

Do not commit local credentials, Codex profiles, or machine-specific paths. Real Codex calls require the Codex CLI on `PATH` and local authentication, but tests should remain independent of that environment.

## Session docs

- `handoffs/*` - folder with dated handoff files
- `backlog.md` - living TODO. Tags: `[active]`, `[next]`, `[blocked: <reason>]`, no tag = someday.
- Both gitignored.
