from codex_agent import CodexExecConfig, CodexLLM, LLMResult, SkillRunner
from codex_agent.engine.codex_exec import CodexExecResult


def test_codex_llm_maps_exec_result(monkeypatch):
    calls = {}

    def fake_run_codex_exec(config, prompt):
        calls["config"] = config
        calls["prompt"] = prompt
        return CodexExecResult(
            returncode=0,
            events=[],
            stdout='{"type":"event"}\n',
            stderr="",
            last_message="final answer",
        )

    monkeypatch.setattr("codex_agent.core.llm.run_codex_exec", fake_run_codex_exec)
    config = CodexExecConfig(codex_bin="/bin/codex")

    result = CodexLLM(config).complete("do work")

    assert result.ok
    assert result.text == "final answer"
    assert result.stdout == '{"type":"event"}\n'
    assert result.raw.last_message == "final answer"
    assert calls == {"config": config, "prompt": "do work"}


def test_skill_runner_uses_model_and_prompt_builder():
    calls = {}

    class FakeModel:
        def complete(self, prompt: str) -> LLMResult:
            calls["prompt"] = prompt
            return LLMResult(returncode=0, text="done")

    runner = SkillRunner(
        model=FakeModel(),
        prompt_builder=lambda command: f"prompt for {command}",
    )

    result = runner.run("report")

    assert result.text == "done"
    assert calls["prompt"] == "prompt for report"
