"""Tests for the Power of 10 AST/tokenizer invariant engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from strands_sentinel.invariants import (
    Severity,
    scan_generic_source,
    scan_python_file,
    scan_repository,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_function_within_limits_has_no_violations(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "ok.py",
        "def f(x):\n    assert x is not None\n    assert isinstance(x, int)\n    return x + 1\n",
    )
    assert scan_python_file(path, enforce_function_rules=True) == []


def test_function_over_length_limit_is_critical(tmp_path: Path) -> None:
    body = "\n".join(f"    x{i} = {i}" for i in range(65))
    source = f"def f():\n    assert True\n    assert True\n{body}\n    return 1\n"
    path = _write(tmp_path, "long.py", source)
    violations = scan_python_file(path, enforce_function_rules=True)
    rules = {v.rule for v in violations}
    assert "power_of_10.rule_4.function_length" in rules
    assert all(v.severity == Severity.CRITICAL for v in violations if "rule_4" in v.rule)


def test_function_with_fewer_than_two_asserts_is_critical(tmp_path: Path) -> None:
    path = _write(tmp_path, "few.py", "def f(x):\n    assert x is not None\n    return x\n")
    violations = scan_python_file(path, enforce_function_rules=True)
    assert any(v.rule == "power_of_10.rule_5.assertion_density" for v in violations)
    assert any(v.severity == Severity.CRITICAL for v in violations)


def test_tests_directory_is_exempt_from_function_rules(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    path = _write(tests_dir, "test_something.py", "def test_x():\n    assert 1 == 1\n")
    assert scan_python_file(path, enforce_function_rules=False) == []


def test_infinite_loop_without_break_is_critical(tmp_path: Path) -> None:
    source = "def f():\n    assert True\n    assert True\n    while True:\n        pass\n"
    path = _write(tmp_path, "inf.py", source)
    violations = scan_python_file(path, enforce_function_rules=True)
    loop_violations = [v for v in violations if v.rule == "power_of_10.rule_2.bounded_loop"]
    assert len(loop_violations) == 1
    assert loop_violations[0].severity == Severity.CRITICAL


def test_infinite_loop_with_break_is_warning(tmp_path: Path) -> None:
    source = (
        "def f(n):\n"
        "    assert n is not None\n"
        "    assert n >= 0\n"
        "    i = 0\n"
        "    while True:\n"
        "        if i >= n:\n"
        "            break\n"
        "        i += 1\n"
        "    return i\n"
    )
    path = _write(tmp_path, "brk.py", source)
    violations = scan_python_file(path, enforce_function_rules=True)
    loop_violations = [v for v in violations if v.rule == "power_of_10.rule_2.bounded_loop"]
    assert len(loop_violations) == 1
    assert loop_violations[0].severity == Severity.WARNING


def test_break_inside_nested_loop_does_not_satisfy_outer_loop(tmp_path: Path) -> None:
    source = (
        "def f(n):\n"
        "    assert n is not None\n"
        "    assert n >= 0\n"
        "    while True:\n"
        "        for i in range(n):\n"
        "            break\n"
        "        return 0\n"
    )
    path = _write(tmp_path, "nested.py", source)
    violations = scan_python_file(path, enforce_function_rules=True)
    loop_violations = [v for v in violations if v.rule == "power_of_10.rule_2.bounded_loop"]
    assert len(loop_violations) == 1
    assert loop_violations[0].severity == Severity.CRITICAL


def test_eval_call_is_banned(tmp_path: Path) -> None:
    source = "def f(s):\n    assert s is not None\n    assert isinstance(s, str)\n    return eval(s)\n"
    path = _write(tmp_path, "danger.py", source)
    violations = scan_python_file(path, enforce_function_rules=True)
    assert any(v.rule == "power_of_10.banned_pattern.dynamic_execution" for v in violations)


def test_os_system_call_is_banned(tmp_path: Path) -> None:
    source = (
        "import os\n\n\n"
        "def f(cmd):\n"
        "    assert cmd is not None\n"
        "    assert isinstance(cmd, str)\n"
        "    os.system(cmd)\n"
    )
    path = _write(tmp_path, "sysdanger.py", source)
    violations = scan_python_file(path, enforce_function_rules=True)
    assert any(v.rule == "power_of_10.banned_pattern.dynamic_execution" for v in violations)


def test_mutable_default_argument_is_warning(tmp_path: Path) -> None:
    source = "def f(items=[]):\n    assert items is not None\n    assert isinstance(items, list)\n    return items\n"
    path = _write(tmp_path, "mut.py", source)
    violations = scan_python_file(path, enforce_function_rules=True)
    mutable_violations = [v for v in violations if v.rule == "power_of_10.rule_3.mutable_default_argument"]
    assert len(mutable_violations) == 1
    assert mutable_violations[0].severity == Severity.WARNING


def test_scan_python_file_requires_existing_python_file(tmp_path: Path) -> None:
    with pytest.raises(AssertionError):
        scan_python_file(tmp_path / "missing.py", enforce_function_rules=True)


def test_scan_generic_source_flags_oversized_rust_function(tmp_path: Path) -> None:
    body = "\n".join(f"    let x{i} = {i};" for i in range(65))
    source = f"fn f() {{\n{body}\n}}\n"
    path = _write(tmp_path, "big.rs", source)
    violations = scan_generic_source(path)
    assert len(violations) == 1
    assert violations[0].severity == Severity.WARNING


def test_scan_generic_source_accepts_short_function(tmp_path: Path) -> None:
    path = _write(tmp_path, "small.rs", "fn f() {\n    let x = 1;\n}\n")
    assert scan_generic_source(path) == []


def test_scan_repository_aggregates_across_python_files(tmp_path: Path) -> None:
    _write(tmp_path, "clean.py", "def f(x):\n    assert x is not None\n    assert isinstance(x, int)\n    return x\n")
    _write(tmp_path, "dirty.py", "def f(x):\n    return x\n")
    violations = scan_repository(python_roots=[tmp_path])
    assert any(v.file.endswith("dirty.py") for v in violations)
    assert not any(v.file.endswith("clean.py") for v in violations)
