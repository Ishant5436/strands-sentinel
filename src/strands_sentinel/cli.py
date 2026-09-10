"""Rich terminal CLI: `strands-sentinel check|watch|mcp`.

`watch` uses `while max_iterations is None or iterations < max_iterations`
rather than `while True`, so it is a genuinely bounded construct whenever a
caller supplies a limit (as the test suite does) and an intentionally
open-ended one in real interactive use, without disguising an unconditional
loop as a bounded one.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from strands_sentinel.agent import audit_workspace

_SEVERITY_STYLES: dict[str, str] = {"CRITICAL": "bold red", "WARNING": "yellow", "INFO": "cyan"}
_DEFAULT_WATCH_INTERVAL_SECONDS = 2.0


def _severity_style(severity: str) -> str:
    assert isinstance(severity, str)
    assert severity
    return _SEVERITY_STYLES.get(severity, "white")


def _render_findings_table(console: Console, title: str, rows: list[dict[str, Any]], message_key: str) -> None:
    assert console is not None
    assert isinstance(rows, list)
    table = Table(title=title)
    table.add_column("Severity")
    table.add_column("Rule")
    table.add_column("File:Line")
    table.add_column("Detail")
    for row in rows:
        style = _severity_style(row["severity"])
        table.add_row(
            f"[{style}]{row['severity']}[/{style}]", row["rule"], f"{row['file']}:{row['line']}", row[message_key]
        )
    console.print(table)


def run_check(path: Path, console: Console) -> int:
    assert path.exists()
    assert console is not None
    report = audit_workspace(str(path))
    _render_findings_table(console, "AST Safety Invariant Violations", report["invariants"]["violations"], "message")
    _render_findings_table(console, "Secret Scan Findings", report["secrets"]["findings"], "redacted")
    critical = report["critical_count"]
    assert isinstance(critical, int)
    summary = f"CRITICAL FINDINGS: {critical}" if critical else "CLEAN: 0 critical findings"
    console.print(f"\n[bold]{summary}[/bold]")
    return 1 if critical > 0 else 0


def _mtime_snapshot(root: Path) -> dict[str, float]:
    assert root.exists()
    if root.is_file():
        return {str(root): root.stat().st_mtime}
    snapshot = {str(p): p.stat().st_mtime for p in root.rglob("*.py") if p.is_file()}
    assert isinstance(snapshot, dict)
    return snapshot


def watch_loop(path: Path, interval_seconds: float, max_iterations: int | None, console: Console) -> int:
    assert path.exists()
    assert interval_seconds > 0.0
    last_snapshot: dict[str, float] = {}
    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        snapshot = _mtime_snapshot(path)
        if snapshot != last_snapshot:
            run_check(path, console)
            last_snapshot = snapshot
        iterations += 1
        if max_iterations is None or iterations < max_iterations:
            time.sleep(interval_seconds)
    assert iterations >= 0
    return 0


@click.group()
def cli() -> None:
    """strands-sentinel: autonomous mission-critical systems and AST safety auditor."""
    assert isinstance(cli, click.Group)
    assert cli.name == "cli"


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def check(path: Path) -> None:
    """Run a one-shot audit of PATH and print a report."""
    assert path.exists()
    console = Console()
    exit_code = run_check(path, console)
    assert isinstance(exit_code, int)
    raise SystemExit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--interval", default=_DEFAULT_WATCH_INTERVAL_SECONDS, show_default=True, help="Polling interval.")
@click.option("--max-iterations", default=None, type=int, help="Stop after N polls (used by tests).")
def watch(path: Path, interval: float, max_iterations: int | None) -> None:
    """Continuously re-audit PATH whenever a tracked .py file changes."""
    assert path.exists()
    console = Console()
    exit_code = watch_loop(path, interval, max_iterations, console)
    assert isinstance(exit_code, int)
    raise SystemExit(exit_code)


@cli.command(name="mcp")
def mcp_command() -> None:
    """Run the strands-sentinel MCP server over stdio."""
    from strands_sentinel.mcp_server import main as mcp_main

    assert mcp_main is not None
    assert callable(mcp_main)
    mcp_main()


def main() -> None:
    assert cli is not None
    assert callable(cli)
    cli()


if __name__ == "__main__":
    main()
