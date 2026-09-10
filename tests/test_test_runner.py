"""Tests for the sandboxed test suite executor.

Failure-parser tests use fixture strings captured verbatim from real
`pytest -q` and `cargo test` runs against known-failing sample projects in
this environment (see the session record), not hand-guessed formats.
"""

from __future__ import annotations

import sys
from pathlib import Path

from strands_sentinel.test_runner import (
    TestFailure,
    detect_test_command,
    parse_cargo_failures,
    parse_pytest_failures,
    run_test_suite,
)

_REAL_PYTEST_OUTPUT = """\
.FF                                                                      [100%]
=================================== FAILURES ===================================
________________________________ test_bad_math _________________________________

    def test_bad_math():
>       assert 1 == 2
E       assert 1 == 2

test_fail_sample.py:5: AssertionError
_________________________________ test_raises __________________________________

    def test_raises():
>       raise ValueError("boom")
E       ValueError: boom

test_fail_sample.py:8: ValueError
=========================== short test summary info ============================
FAILED test_fail_sample.py::test_bad_math - assert 1 == 2
FAILED test_fail_sample.py::test_raises - ValueError: boom
2 failed, 1 passed in 0.01s
"""

_REAL_CARGO_OUTPUT = """\
running 3 tests
test tests::test_ok ... ok
test tests::test_panics ... FAILED
test tests::test_bad_math ... FAILED

failures:

---- tests::test_panics stdout ----

thread 'tests::test_panics' (5409014) panicked at src/lib.rs:19:9:
boom
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

---- tests::test_bad_math stdout ----

thread 'tests::test_bad_math' (5409012) panicked at src/lib.rs:14:9:
assertion `left == right` failed
  left: 2
 right: 3


failures:
    tests::test_bad_math
    tests::test_panics

test result: FAILED. 1 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
"""


def test_parse_pytest_failures_extracts_both_failures() -> None:
    failures = parse_pytest_failures(_REAL_PYTEST_OUTPUT)
    assert len(failures) == 2
    assert TestFailure("test_fail_sample.py::test_bad_math", "assert 1 == 2") in failures
    assert TestFailure("test_fail_sample.py::test_raises", "ValueError: boom") in failures


def test_parse_pytest_failures_on_clean_output_is_empty() -> None:
    assert parse_pytest_failures("3 passed in 0.01s\n") == []


def test_parse_cargo_failures_extracts_both_names() -> None:
    failures = parse_cargo_failures(_REAL_CARGO_OUTPUT)
    names = {f.name for f in failures}
    assert names == {"tests::test_bad_math", "tests::test_panics"}


def test_parse_cargo_failures_extracts_panic_message() -> None:
    failures = {f.name: f.message for f in parse_cargo_failures(_REAL_CARGO_OUTPUT)}
    assert "boom" in failures["tests::test_panics"]
    assert "assertion" in failures["tests::test_bad_math"]


def test_detect_test_command_finds_cargo_project(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"x\"\n", encoding="utf-8")
    assert detect_test_command(tmp_path) == "cargo test"


def test_detect_test_command_finds_pytest_project(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_x.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")
    assert detect_test_command(tmp_path) == "pytest"


def test_detect_test_command_finds_makefile_test_target(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text("test:\n\techo running\n", encoding="utf-8")
    assert detect_test_command(tmp_path) == "make test"


def test_detect_test_command_returns_none_when_no_markers(tmp_path: Path) -> None:
    assert detect_test_command(tmp_path) is None


def test_run_test_suite_reports_passing_suite(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    result = run_test_suite(tmp_path, command=f"{sys.executable} -m pytest -q")
    assert result.passed
    assert result.exit_code == 0
    assert result.failures == []


def test_run_test_suite_reports_failing_suite(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_bad.py").write_text("def test_bad():\n    assert 1 == 2\n", encoding="utf-8")
    result = run_test_suite(tmp_path, command=f"{sys.executable} -m pytest -q")
    assert not result.passed
    assert result.exit_code != 0
    assert len(result.failures) == 1
    assert "test_bad" in result.failures[0].name


def test_run_test_suite_enforces_timeout(tmp_path: Path) -> None:
    command = f'{sys.executable} -c "import time; time.sleep(5)"'
    result = run_test_suite(tmp_path, command=command, timeout_seconds=0.2)
    assert result.timed_out
    assert not result.passed


def test_run_test_suite_with_no_detected_command_reports_failure(tmp_path: Path) -> None:
    result = run_test_suite(tmp_path)
    assert not result.passed
    assert result.command == ""
