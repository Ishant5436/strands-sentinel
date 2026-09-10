"""Tests for the MCP server exposing strands-sentinel tools.

`mcp.server.mcpserver.MCPServer.tool()` returns the original function
unchanged (verified empirically), so these tools remain directly callable
plain functions for unit testing, unlike the Strands `@tool` decorator.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from strands_sentinel.mcp_server import (
    SERVER_NAME,
    mcp,
    sentinel_audit_workspace,
    sentinel_check_ast_invariants,
    sentinel_generate_remediation_patch,
    sentinel_run_test_suite,
    sentinel_scan_for_secrets,
)


def test_server_has_expected_name() -> None:
    assert mcp.name == SERVER_NAME


@pytest.mark.asyncio
async def test_all_five_tools_are_registered() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == {
        "sentinel_audit_workspace",
        "sentinel_check_ast_invariants",
        "sentinel_scan_for_secrets",
        "sentinel_run_test_suite",
        "sentinel_generate_remediation_patch",
    }


def test_sentinel_check_ast_invariants_tool(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def f(x):\n    return x\n", encoding="utf-8")
    result = sentinel_check_ast_invariants(str(bad_file))
    assert result["critical_count"] >= 1


def test_sentinel_scan_for_secrets_tool(tmp_path: Path) -> None:
    secret_file = tmp_path / "config.py"
    secret_file.write_text('key = "AKIAABCDEFGHIJKLMNOP"\n', encoding="utf-8")
    result = sentinel_scan_for_secrets(str(secret_file))
    assert result["critical_count"] == 1


def test_sentinel_audit_workspace_tool(tmp_path: Path) -> None:
    clean_file = tmp_path / "clean.py"
    clean_file.write_text(
        "def f(x):\n    assert x is not None\n    assert isinstance(x, int)\n    return x\n", encoding="utf-8"
    )
    result = sentinel_audit_workspace(str(tmp_path))
    assert result["critical_count"] == 0


def test_sentinel_run_test_suite_tool_with_no_command(tmp_path: Path) -> None:
    result = sentinel_run_test_suite(str(tmp_path), "")
    assert result["passed"] is False


def test_sentinel_generate_remediation_patch_tool_unknown_id() -> None:
    result = sentinel_generate_remediation_patch("unknown-id")
    assert result["found"] is False
