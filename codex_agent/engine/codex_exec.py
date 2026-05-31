"""Small subprocess wrapper for `codex exec --json`."""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CodexExecConfig:
    codex_bin: str = "codex"
    cwd: Path | str | None = None
    model: str | None = None
    profile: str | None = None
    sandbox: str | None = None
    output_schema: Path | str | None = None
    output_last_message: Path | str | None = None
    extra_config: tuple[str, ...] = ()
    ephemeral: bool = False
    skip_git_repo_check: bool = False
    prompt_via_stdin: bool = False
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class CodexEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CodexExecResult:
    returncode: int
    events: list[CodexEvent]
    stdout: str
    stderr: str
    last_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def build_exec_command(config: CodexExecConfig, prompt: str) -> list[str]:
    cmd = [config.codex_bin, "exec", "--json"]
    if config.cwd is not None:
        cmd.extend(["--cd", str(config.cwd)])
    if config.model:
        cmd.extend(["--model", config.model])
    if config.profile:
        cmd.extend(["--profile", config.profile])
    if config.sandbox:
        cmd.extend(["--sandbox", config.sandbox])
    if config.output_schema is not None:
        cmd.extend(["--output-schema", str(config.output_schema)])
    if config.output_last_message is not None:
        cmd.extend(["--output-last-message", str(config.output_last_message)])
    if config.ephemeral:
        cmd.append("--ephemeral")
    if config.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    for item in config.extra_config:
        cmd.extend(["--config", item])
    cmd.append("-" if config.prompt_via_stdin else prompt)
    return cmd


def run_codex_exec(config: CodexExecConfig, prompt: str) -> CodexExecResult:
    if config.output_last_message is not None:
        return _run_codex_exec(config, prompt, Path(config.output_last_message))

    with tempfile.TemporaryDirectory() as tmp:
        output_last_message = Path(tmp) / "last_message.txt"
        return _run_codex_exec(
            replace(config, output_last_message=output_last_message),
            prompt,
            output_last_message,
        )


def _run_codex_exec(
    config: CodexExecConfig,
    prompt: str,
    output_last_message: Path,
) -> CodexExecResult:
    try:
        if config.prompt_via_stdin:
            proc = subprocess.run(
                build_exec_command(config, prompt),
                input=prompt,
                text=True,
                capture_output=True,
                check=False,
                timeout=config.timeout_seconds,
            )
        else:
            proc = subprocess.run(
                build_exec_command(config, prompt),
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=False,
                timeout=config.timeout_seconds,
            )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        message = f"codex exec timed out after {config.timeout_seconds}s"
        return CodexExecResult(
            returncode=124,
            events=parse_jsonl_events(stdout),
            stdout=stdout,
            stderr=(stderr + "\n" + message).strip(),
            last_message=None,
        )
    events = parse_jsonl_events(proc.stdout)
    last_message = _read_last_message(output_last_message) or _last_message(events)
    return CodexExecResult(
        returncode=proc.returncode,
        events=events,
        stdout=proc.stdout,
        stderr=proc.stderr,
        last_message=last_message,
    )


def parse_jsonl_events(text: str) -> list[CodexEvent]:
    events: list[CodexEvent] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            events.append(CodexEvent(type="raw", data={"line": line}))
            continue
        if isinstance(payload, dict):
            event_type = str(payload.get("type", "unknown"))
            events.append(CodexEvent(type=event_type, data=payload))
        else:
            events.append(CodexEvent(type="raw", data={"value": payload}))
    return events


def _last_message(events: list[CodexEvent]) -> str | None:
    for event in reversed(events):
        data = event.data
        for key in ("last_message", "message", "content", "text"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _read_last_message(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text().strip()
    return text or None
