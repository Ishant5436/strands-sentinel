"""Tests for the Strands intervention handler."""

from __future__ import annotations

from strands.hooks import BeforeToolCallEvent
from strands.interventions import Confirm, Proceed

from strands_sentinel.intervention import SentinelInterventionHandler


def _event(tool_name: str) -> BeforeToolCallEvent:
    return BeforeToolCallEvent(
        agent=None,  # type: ignore[arg-type]
        selected_tool=None,
        tool_use={"name": tool_name, "toolUseId": "t1", "input": {}},
        invocation_state={},
    )


def test_handler_name_is_set() -> None:
    handler = SentinelInterventionHandler()
    assert handler.name == "strands-sentinel"


def test_read_only_tool_proceeds() -> None:
    handler = SentinelInterventionHandler()
    action = handler.before_tool_call(_event("audit_workspace"))
    assert isinstance(action, Proceed)


def test_remediation_tool_requires_confirmation() -> None:
    handler = SentinelInterventionHandler()
    action = handler.before_tool_call(_event("generate_remediation_patch"))
    assert isinstance(action, Confirm)
    assert "generate_remediation_patch" in action.prompt


def test_unrelated_tool_proceeds_when_no_critical_findings() -> None:
    handler = SentinelInterventionHandler()
    action = handler.before_tool_call(_event("some_other_tool"))
    assert isinstance(action, Proceed)


def test_critical_finding_escalates_subsequent_calls_to_confirm() -> None:
    handler = SentinelInterventionHandler()
    handler.record_critical_finding("hardcoded AWS key found")
    action = handler.before_tool_call(_event("some_other_tool"))
    assert isinstance(action, Confirm)
    assert "1 unresolved critical" in action.prompt


def test_clear_critical_findings_restores_proceed_behavior() -> None:
    handler = SentinelInterventionHandler()
    handler.record_critical_finding("hardcoded AWS key found")
    handler.clear_critical_findings()
    action = handler.before_tool_call(_event("some_other_tool"))
    assert isinstance(action, Proceed)


def test_read_only_tool_still_proceeds_even_with_critical_findings() -> None:
    handler = SentinelInterventionHandler()
    handler.record_critical_finding("hardcoded AWS key found")
    action = handler.before_tool_call(_event("scan_for_secrets"))
    assert isinstance(action, Proceed)
