import subprocess
from pathlib import Path
from types import SimpleNamespace

from codex_agent.engine.codex_exec import (
    CodexExecConfig,
    build_exec_command,
    parse_jsonl_events,
    run_codex_exec,
)


def test_build_exec_command_includes_core_flags():
    cmd = build_exec_command(
        CodexExecConfig(
            codex_bin="/bin/codex",
            cwd=Path("/tmp/project"),
            model="gpt-test",
            sandbox="workspace-write",
            ephemeral=True,
            skip_git_repo_check=True,
        ),
        "do work",
    )

    assert cmd == [
        "/bin/codex",
        "exec",
        "--json",
        "--cd",
        "/tmp/project",
        "--model",
        "gpt-test",
        "--sandbox",
        "workspace-write",
        "--ephemeral",
        "--skip-git-repo-check",
        "do work",
    ]


def test_parse_jsonl_events_keeps_raw_lines():
    events = parse_jsonl_events('{"type":"start"}\nnot json\n{"message":"done"}\n')

    assert [event.type for event in events] == ["start", "raw", "unknown"]
    assert events[1].data == {"line": "not json"}


def test_run_codex_exec_reads_output_last_message_file(monkeypatch):
    def fake_run(cmd, stdin, text, capture_output, check, timeout):
        out_path = Path(cmd[cmd.index("--output-last-message") + 1])
        out_path.write_text("final answer")
        assert stdin is not None
        assert timeout is None
        return SimpleNamespace(
            returncode=0,
            stdout='{"type":"event"}\n',
            stderr="",
        )

    monkeypatch.setattr("codex_agent.engine.codex_exec.subprocess.run", fake_run)

    result = run_codex_exec(CodexExecConfig(codex_bin="/bin/codex"), "do work")

    assert result.ok
    assert result.last_message == "final answer"


def test_run_codex_exec_can_send_prompt_via_stdin(monkeypatch):
    def fake_run(cmd, input, text, capture_output, check, timeout):
        out_path = Path(cmd[cmd.index("--output-last-message") + 1])
        out_path.write_text("json answer")
        assert cmd[-1] == "-"
        assert input == "do work"
        return SimpleNamespace(
            returncode=0,
            stdout='{"type":"event"}\n',
            stderr="",
        )

    monkeypatch.setattr("codex_agent.engine.codex_exec.subprocess.run", fake_run)

    result = run_codex_exec(
        CodexExecConfig(codex_bin="/bin/codex", prompt_via_stdin=True),
        "do work",
    )

    assert result.ok
    assert result.last_message == "json answer"


def test_run_codex_exec_reports_timeout(monkeypatch):
    def fake_run(cmd, stdin, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=timeout,
            output='{"type":"event"}\n',
            stderr="partial stderr",
        )

    monkeypatch.setattr("codex_agent.engine.codex_exec.subprocess.run", fake_run)

    result = run_codex_exec(
        CodexExecConfig(codex_bin="/bin/codex", timeout_seconds=5),
        "do work",
    )

    assert result.returncode == 124
    assert [event.type for event in result.events] == ["event"]
    assert "timed out after 5s" in result.stderr
