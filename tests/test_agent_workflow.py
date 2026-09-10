"""Tests for the agent orchestrator: tools and model router.

Only the Bedrock path is exercised end to end (boto3 is available). The
other providers are verified to fail with a clear, actionable error since
their client libraries are not installed in this environment -- that
failure mode is exactly what a user without those extras will see.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from strands import Agent

from strands_sentinel.agent import (
    audit_workspace,
    build_model,
    build_sentinel_agent,
    check_ast_invariants,
    generate_remediation_patch,
    run_test_suite,
    scan_for_secrets,
    select_provider,
)


def test_select_provider_defaults_to_bedrock_with_empty_env() -> None:
    assert select_provider(env={}) == "bedrock"


def test_select_provider_honors_explicit_override() -> None:
    assert select_provider(env={"STRANDS_SENTINEL_MODEL_PROVIDER": "OpenAI"}) == "openai"


def test_select_provider_infers_from_anthropic_key() -> None:
    assert select_provider(env={"ANTHROPIC_API_KEY": "sk-x"}) == "anthropic"


def test_select_provider_explicit_override_wins_over_inference() -> None:
    env = {"STRANDS_SENTINEL_MODEL_PROVIDER": "bedrock", "ANTHROPIC_API_KEY": "sk-x"}
    assert select_provider(env=env) == "bedrock"


def test_build_model_bedrock_succeeds() -> None:
    model = build_model("bedrock")
    assert model is not None


def test_build_model_unknown_provider_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unknown model provider"):
        build_model("not-a-real-provider")


@pytest.mark.parametrize(
    "provider,package",
    [("anthropic", "anthropic"), ("openai", "openai"), ("gemini", "google-genai"), ("ollama", "ollama")],
)
def test_build_model_missing_optional_dependency_raises_clear_runtime_error(provider: str, package: str) -> None:
    with pytest.raises(RuntimeError, match=package):
        build_model(provider)


def test_check_ast_invariants_tool_reports_violation(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def f(x):\n    return x\n", encoding="utf-8")
    result = check_ast_invariants(str(bad_file))
    assert result["critical_count"] >= 1
    assert result["violations"][0]["id"]


def test_scan_for_secrets_tool_reports_finding(tmp_path: Path) -> None:
    secret_file = tmp_path / "config.py"
    secret_file.write_text('key = "AKIAABCDEFGHIJKLMNOP"\n', encoding="utf-8")
    result = scan_for_secrets(str(secret_file))
    assert result["critical_count"] == 1


def test_audit_workspace_combines_both_reports(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.py"
    bad_file.write_text('def f(x):\n    key = "AKIAABCDEFGHIJKLMNOP"\n    return x\n', encoding="utf-8")
    result = audit_workspace(str(tmp_path))
    assert result["critical_count"] >= 2
    assert "invariants" in result
    assert "secrets" in result


def test_run_test_suite_tool_auto_detects_when_command_empty(tmp_path: Path) -> None:
    result = run_test_suite(str(tmp_path), "")
    assert result["passed"] is False
    assert result["command"] == ""


def test_generate_remediation_patch_returns_guidance_for_known_violation(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def f(x):\n    return x\n", encoding="utf-8")
    audit_result = check_ast_invariants(str(bad_file))
    violation_id = audit_result["violations"][0]["id"]
    patch = generate_remediation_patch(violation_id)
    assert patch["found"] is True
    assert patch["suggested_fix"]


def test_generate_remediation_patch_reports_unknown_violation_id() -> None:
    patch = generate_remediation_patch("does-not-exist")
    assert patch["found"] is False
    assert patch["suggested_fix"] is None


def test_build_sentinel_agent_constructs_real_agent() -> None:
    agent = build_sentinel_agent(provider="bedrock")
    assert isinstance(agent, Agent)
    assert len(agent.tool_names) == 5
