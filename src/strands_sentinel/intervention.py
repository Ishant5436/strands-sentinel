"""Strands InterventionHandler for strands-sentinel.

Read-only audit tools always proceed without interruption. Remediation
tools (anything that writes a patch) and any tool call made while a
CRITICAL-severity finding is outstanding require human confirmation via
`Confirm`. `Confirm` takes a `prompt` field, not `message` -- verified
against the installed strands-agents 1.55.1 `Confirm` dataclass, which has
no `message` field.
"""

from __future__ import annotations

from typing import Any

from strands.hooks import BeforeToolCallEvent
from strands.interventions import Confirm, Deny, Guide, InterventionHandler, Proceed, Transform

READ_ONLY_TOOLS = frozenset({"audit_workspace", "check_ast_invariants", "scan_for_secrets", "run_test_suite"})
REMEDIATION_TOOLS = frozenset({"generate_remediation_patch"})


class SentinelInterventionHandler(InterventionHandler):
    """Confirms remediation actions and escalates once a CRITICAL finding exists."""

    name = "strands-sentinel"

    def __init__(self) -> None:
        self._critical_findings: list[str] = []
        assert isinstance(self._critical_findings, list)
        assert len(self._critical_findings) == 0

    def record_critical_finding(self, description: str) -> None:
        assert isinstance(description, str)
        assert description
        self._critical_findings.append(description)

    def clear_critical_findings(self) -> None:
        count = len(self._critical_findings)
        self._critical_findings.clear()
        assert len(self._critical_findings) == 0
        assert count >= 0

    def _build_confirmation_prompt(self, tool_name: str) -> str:
        assert isinstance(tool_name, str)
        assert tool_name
        count = len(self._critical_findings)
        return f"Tool '{tool_name}' requires confirmation: {count} unresolved critical finding(s) recorded. Proceed?"

    def before_tool_call(
        self, event: BeforeToolCallEvent, **kwargs: Any
    ) -> Proceed | Deny | Guide | Confirm | Transform:
        assert event is not None
        assert "name" in event.tool_use
        tool_name = event.tool_use["name"]
        if tool_name in READ_ONLY_TOOLS:
            return Proceed(reason=f"'{tool_name}' is a read-only audit tool")
        if tool_name in REMEDIATION_TOOLS or self._critical_findings:
            return Confirm(
                prompt=self._build_confirmation_prompt(tool_name),
                reason="high-severity finding pending or remediation tool requested",
            )
        return Proceed()
