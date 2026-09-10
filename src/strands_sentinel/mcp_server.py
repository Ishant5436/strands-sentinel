"""MCP server exposing strands-sentinel tools over stdio/SSE.

Built against mcp>=2.1.0, where `mcp.server.fastmcp.FastMCP` has been
renamed to `mcp.server.mcpserver.MCPServer` (confirmed empirically: the old
import path raises `ModuleNotFoundError` with an explicit migration
message under the installed mcp==2.1.0 in this environment). The
decorator-based API is otherwise a near drop-in match: `.tool()` returns
the original function unchanged (unlike the Strands `@tool` decorator,
which wraps it), and `.run(transport=...)` accepts "stdio", "sse", or
"streamable-http".
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from strands_sentinel.agent import audit_workspace as _audit_workspace
from strands_sentinel.agent import check_ast_invariants as _check_ast_invariants
from strands_sentinel.agent import generate_remediation_patch as _generate_remediation_patch
from strands_sentinel.agent import run_test_suite as _run_test_suite
from strands_sentinel.agent import scan_for_secrets as _scan_for_secrets

SERVER_NAME = "strands-sentinel"
SERVER_INSTRUCTIONS = (
    "Autonomous mission-critical systems and AST safety auditor. Use these tools to check "
    "Power of 10 safety invariants, scan for hardcoded secrets, and run test suites."
)

mcp = MCPServer(name=SERVER_NAME, instructions=SERVER_INSTRUCTIONS)


@mcp.tool()
def sentinel_audit_workspace(path: str) -> dict[str, Any]:
    """Run the full sentinel sweep (AST invariants and secret scan) over a workspace path."""
    assert isinstance(path, str)
    assert path
    result = _audit_workspace(path)
    assert isinstance(result, dict)
    return result


@mcp.tool()
def sentinel_check_ast_invariants(path: str) -> dict[str, Any]:
    """Scan a file or directory for Power of 10 AST safety invariant violations."""
    assert isinstance(path, str)
    assert path
    result = _check_ast_invariants(path)
    assert isinstance(result, dict)
    return result


@mcp.tool()
def sentinel_scan_for_secrets(path: str) -> dict[str, Any]:
    """Scan a file or directory for hardcoded secrets using deterministic patterns and entropy."""
    assert isinstance(path, str)
    assert path
    result = _scan_for_secrets(path)
    assert isinstance(result, dict)
    return result


@mcp.tool()
def sentinel_run_test_suite(path: str, command: str) -> dict[str, Any]:
    """Run the test suite for a repository. Pass command="" to auto-detect pytest/cargo test/make test."""
    assert isinstance(path, str)
    assert isinstance(command, str)
    result = _run_test_suite(path, command)
    assert isinstance(result, dict)
    return result


@mcp.tool()
def sentinel_generate_remediation_patch(violation_id: str) -> dict[str, Any]:
    """Return structured remediation guidance for a violation previously reported by an audit tool."""
    assert isinstance(violation_id, str)
    assert violation_id
    result = _generate_remediation_patch(violation_id)
    assert isinstance(result, dict)
    return result


def main() -> None:
    assert mcp is not None
    assert mcp.name == SERVER_NAME
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
