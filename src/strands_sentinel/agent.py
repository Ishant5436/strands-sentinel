"""Core strands-sentinel Agent orchestrator: tools and resilient model router.

Only Bedrock is exercised end to end here (boto3 ships as a strands-agents
transitive dependency). Anthropic, OpenAI, Gemini, and Ollama are wired as
lazy imports that raise a clear, actionable RuntimeError when their
optional client library is missing, rather than being partially
implemented and untested: this environment does not have `anthropic`,
`openai`, `google-genai`, or `ollama` installed, so those code paths
cannot be exercised for real here (see tests/test_agent_workflow.py for
what is and is not verified).
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from strands import Agent, tool

from strands_sentinel.intervention import SentinelInterventionHandler
from strands_sentinel.invariants import Severity, Violation, scan_python_file, scan_repository
from strands_sentinel.secret_scanner import SecretFinding, scan_directory, scan_file
from strands_sentinel.test_runner import TestRunResult
from strands_sentinel.test_runner import run_test_suite as execute_test_suite

_PROVIDER_ENV_VAR = "STRANDS_SENTINEL_MODEL_PROVIDER"
_PROVIDER_DETECTION_ENV_VARS: tuple[tuple[str, str], ...] = (
    ("anthropic", "ANTHROPIC_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
    ("gemini", "GOOGLE_API_KEY"),
    ("ollama", "OLLAMA_HOST"),
)
DEFAULT_PROVIDER = "bedrock"
_MISSING_DEP_MESSAGE = (
    "provider '{provider}' requires the '{package}' package; install it with `uv pip install {package}`"
)

_VIOLATION_REGISTRY: dict[str, dict[str, Any]] = {}
_REMEDIATION_TEMPLATES: dict[str, str] = {
    "power_of_10.rule_4.function_length": "Split the function into smaller helpers, each handling one responsibility.",
    "power_of_10.rule_5.assertion_density": "Add at least two `assert` statements for this function's invariants.",
    "power_of_10.rule_2.bounded_loop": "Replace `while True` with a loop bounded by an explicit, checkable counter.",
    "power_of_10.rule_3.mutable_default_argument": "Replace the mutable default with `None`; build it inside.",
    "power_of_10.banned_pattern.dynamic_execution": "Remove the dynamic-execution/deserialization call.",
    "secret.aws_access_key_id": "Revoke this AWS access key immediately; move it to a secrets manager.",
    "secret.github_pat": "Revoke this GitHub token immediately; move it to a secrets manager.",
    "secret.evm_private_key": "Treat the wallet as compromised; move the key out of source control and rotate it.",
    "secret.mnemonic_seed_phrase": "Treat the wallet as compromised; move the phrase out of source control.",
    "secret.high_entropy_token": "Verify whether this is a credential; if so, move it to a secrets manager.",
}
_DEFAULT_REMEDIATION = "Review this finding manually; no template remediation is registered for this rule."


def select_provider(env: Mapping[str, str] | None = None) -> str:
    assert env is None or isinstance(env, Mapping)
    source = env if env is not None else os.environ
    explicit = source.get(_PROVIDER_ENV_VAR)
    if explicit:
        return explicit.strip().lower()
    for provider, var in _PROVIDER_DETECTION_ENV_VARS:
        if source.get(var):
            return provider
    assert DEFAULT_PROVIDER
    return DEFAULT_PROVIDER


def _build_bedrock_model() -> Any:
    from strands.models.bedrock import BedrockModel

    assert BedrockModel is not None
    model = BedrockModel()
    assert model is not None
    return model


def _build_anthropic_model() -> Any:
    try:
        from strands.models.anthropic import AnthropicModel
    except ImportError as exc:
        raise RuntimeError(_MISSING_DEP_MESSAGE.format(provider="anthropic", package="anthropic")) from exc
    model_id = os.environ.get("ANTHROPIC_MODEL_ID")
    if not model_id:
        raise RuntimeError("provider 'anthropic' requires ANTHROPIC_MODEL_ID to be set")
    max_tokens = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "4096"))
    assert max_tokens > 0
    model = AnthropicModel(model_id=model_id, max_tokens=max_tokens)
    assert model is not None
    return model


def _build_openai_model() -> Any:
    try:
        from strands.models.openai import OpenAIModel
    except ImportError as exc:
        raise RuntimeError(_MISSING_DEP_MESSAGE.format(provider="openai", package="openai")) from exc
    model_id = os.environ.get("OPENAI_MODEL_ID", "gpt-4o")
    assert model_id
    model = OpenAIModel(model_id=model_id)
    assert model is not None
    return model


def _build_gemini_model() -> Any:
    try:
        from strands.models.gemini import GeminiModel
    except ImportError as exc:
        raise RuntimeError(_MISSING_DEP_MESSAGE.format(provider="gemini", package="google-genai")) from exc
    model_id = os.environ.get("GEMINI_MODEL_ID")
    if not model_id:
        raise RuntimeError("provider 'gemini' requires GEMINI_MODEL_ID to be set")
    assert model_id
    model = GeminiModel(model_id=model_id)
    assert model is not None
    return model


def _build_ollama_model() -> Any:
    try:
        from strands.models.ollama import OllamaModel
    except ImportError as exc:
        raise RuntimeError(_MISSING_DEP_MESSAGE.format(provider="ollama", package="ollama")) from exc
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    assert host
    model = OllamaModel(host=host)
    assert model is not None
    return model


_MODEL_BUILDERS: dict[str, Callable[[], Any]] = {
    "bedrock": _build_bedrock_model,
    "anthropic": _build_anthropic_model,
    "openai": _build_openai_model,
    "gemini": _build_gemini_model,
    "ollama": _build_ollama_model,
}


def build_model(provider: str) -> Any:
    assert isinstance(provider, str)
    assert provider
    builder = _MODEL_BUILDERS.get(provider)
    if builder is None:
        raise ValueError(f"unknown model provider '{provider}', expected one of {sorted(_MODEL_BUILDERS)}")
    return builder()


def _violation_id(file: str, line: int, rule: str) -> str:
    assert isinstance(file, str)
    assert line > 0
    digest = hashlib.sha256(f"{file}:{line}:{rule}".encode()).hexdigest()[:16]
    assert len(digest) == 16
    return digest


def _register_violation(file: str, line: int, rule: str, message: str) -> str:
    assert isinstance(rule, str)
    assert isinstance(message, str)
    vid = _violation_id(file, line, rule)
    _VIOLATION_REGISTRY[vid] = {"file": file, "line": line, "rule": rule, "message": message}
    assert vid in _VIOLATION_REGISTRY
    return vid


def _invariant_violation_to_dict(v: Violation) -> dict[str, Any]:
    assert isinstance(v, Violation)
    assert v.file
    return {
        "id": _register_violation(v.file, v.line, v.rule, v.message),
        "file": v.file,
        "line": v.line,
        "rule": v.rule,
        "severity": v.severity.value,
        "message": v.message,
    }


def _secret_finding_to_dict(f: SecretFinding) -> dict[str, Any]:
    assert isinstance(f, SecretFinding)
    assert f.file
    return {
        "id": _register_violation(f.file, f.line, f.rule, f.redacted),
        "file": f.file,
        "line": f.line,
        "rule": f.rule,
        "severity": f.severity.value,
        "redacted": f.redacted,
    }


@tool
def check_ast_invariants(path: str) -> dict[str, Any]:
    """Scan a file or directory for Power of 10 AST safety invariant violations."""
    assert isinstance(path, str)
    assert path
    root = Path(path)
    violations = (
        scan_repository(python_roots=[root])
        if root.is_dir()
        else scan_python_file(root, enforce_function_rules=True)
    )
    records = [_invariant_violation_to_dict(v) for v in violations]
    critical = sum(1 for v in violations if v.severity == Severity.CRITICAL)
    assert isinstance(records, list)
    return {"path": path, "violations": records, "critical_count": critical, "total_count": len(records)}


@tool
def scan_for_secrets(path: str) -> dict[str, Any]:
    """Scan a file or directory for hardcoded secrets using deterministic patterns and entropy."""
    assert isinstance(path, str)
    assert path
    root = Path(path)
    findings = scan_directory(root) if root.is_dir() else scan_file(root)
    records = [_secret_finding_to_dict(f) for f in findings]
    critical = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    assert isinstance(records, list)
    return {"path": path, "findings": records, "critical_count": critical, "total_count": len(records)}


@tool
def audit_workspace(path: str) -> dict[str, Any]:
    """Run the full sentinel sweep (AST invariants and secret scan) over a workspace path."""
    assert isinstance(path, str)
    assert path
    invariants_report = check_ast_invariants(path)
    secrets_report = scan_for_secrets(path)
    assert isinstance(invariants_report, dict)
    assert isinstance(secrets_report, dict)
    return {
        "path": path,
        "invariants": invariants_report,
        "secrets": secrets_report,
        "critical_count": invariants_report["critical_count"] + secrets_report["critical_count"],
    }


@tool
def run_test_suite(path: str, command: str) -> dict[str, Any]:
    """Run the test suite for a repository. Pass command="" to auto-detect pytest/cargo test/make test."""
    assert isinstance(path, str)
    assert isinstance(command, str)
    result: TestRunResult = execute_test_suite(Path(path), command=command or None)
    assert isinstance(result.failures, list)
    return {
        "command": result.command,
        "passed": result.passed,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "duration_seconds": result.duration_seconds,
        "failures": [{"name": f.name, "message": f.message} for f in result.failures],
    }


@tool
def generate_remediation_patch(violation_id: str) -> dict[str, Any]:
    """Return structured remediation guidance for a violation previously reported by an audit tool."""
    assert isinstance(violation_id, str)
    assert violation_id
    record = _VIOLATION_REGISTRY.get(violation_id)
    if record is None:
        return {"violation_id": violation_id, "found": False, "suggested_fix": None}
    suggestion = _REMEDIATION_TEMPLATES.get(record["rule"], _DEFAULT_REMEDIATION)
    assert isinstance(suggestion, str)
    return {"violation_id": violation_id, "found": True, "suggested_fix": suggestion, **record}


def build_sentinel_agent(provider: str | None = None) -> Agent:
    assert provider is None or isinstance(provider, str)
    resolved_provider = provider or select_provider()
    model = build_model(resolved_provider)
    assert model is not None
    return Agent(
        model=model,
        tools=[audit_workspace, check_ast_invariants, scan_for_secrets, run_test_suite, generate_remediation_patch],
        system_prompt=(
            "You are strands-sentinel, an autonomous mission-critical systems and AST safety auditor. "
            "Use the audit tools to find Power of 10 invariant violations, hardcoded secrets, and test "
            "failures. Never fabricate a finding; report only what the tools return."
        ),
        interventions=[SentinelInterventionHandler()],
    )
