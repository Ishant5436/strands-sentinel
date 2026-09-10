"""Tests for the Rich terminal CLI."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from rich.console import Console

from strands_sentinel.cli import _mtime_snapshot, _severity_style, cli, run_check, watch_loop


def test_severity_style_known_and_unknown_values() -> None:
    assert _severity_style("CRITICAL") == "bold red"
    assert _severity_style("UNKNOWN_LEVEL") == "white"


def test_mtime_snapshot_of_single_file(tmp_path: Path) -> None:
    path = tmp_path / "f.py"
    path.write_text("x = 1\n", encoding="utf-8")
    snapshot = _mtime_snapshot(path)
    assert list(snapshot.keys()) == [str(path)]


def test_mtime_snapshot_of_directory_covers_all_python_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "readme.md").write_text("not python\n", encoding="utf-8")
    snapshot = _mtime_snapshot(tmp_path)
    assert len(snapshot) == 2


def test_run_check_returns_zero_on_clean_workspace(tmp_path: Path) -> None:
    clean = tmp_path / "clean.py"
    clean.write_text(
        "def f(x):\n    assert x is not None\n    assert isinstance(x, int)\n    return x\n", encoding="utf-8"
    )
    console = Console(record=True)
    assert run_check(tmp_path, console) == 0


def test_run_check_returns_one_on_dirty_workspace(tmp_path: Path) -> None:
    dirty = tmp_path / "dirty.py"
    dirty.write_text('def f(x):\n    key = "AKIAABCDEFGHIJKLMNOP"\n    return x\n', encoding="utf-8")
    console = Console(record=True)
    assert run_check(tmp_path, console) == 1


def test_watch_loop_detects_change_within_bounded_iterations(tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text("x = 1\n", encoding="utf-8")
    console = Console(record=True)
    exit_code = watch_loop(tmp_path, interval_seconds=0.01, max_iterations=1, console=console)
    assert exit_code == 0
    assert "AST Safety Invariant Violations" in console.export_text()


def test_check_command_exits_zero_on_clean_workspace(tmp_path: Path) -> None:
    clean = tmp_path / "clean.py"
    clean.write_text(
        "def f(x):\n    assert x is not None\n    assert isinstance(x, int)\n    return x\n", encoding="utf-8"
    )
    result = CliRunner().invoke(cli, ["check", str(tmp_path)])
    assert result.exit_code == 0


def test_check_command_exits_one_on_dirty_workspace(tmp_path: Path) -> None:
    dirty = tmp_path / "dirty.py"
    dirty.write_text('def f(x):\n    key = "AKIAABCDEFGHIJKLMNOP"\n    return x\n', encoding="utf-8")
    result = CliRunner().invoke(cli, ["check", str(tmp_path)])
    assert result.exit_code == 1


def test_watch_command_stops_after_max_iterations(tmp_path: Path) -> None:
    (tmp_path / "f.py").write_text("x = 1\n", encoding="utf-8")
    result = CliRunner().invoke(cli, ["watch", str(tmp_path), "--interval", "0.01", "--max-iterations", "1"])
    assert result.exit_code == 0


def test_mcp_command_invokes_server_main(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[bool] = []
    monkeypatch.setattr("strands_sentinel.mcp_server.main", lambda: calls.append(True))
    result = CliRunner().invoke(cli, ["mcp"])
    assert result.exit_code == 0
    assert calls == [True]


def test_cli_group_lists_all_three_subcommands() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert "check" in result.output
    assert "watch" in result.output
    assert "mcp" in result.output
