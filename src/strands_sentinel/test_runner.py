"""Sandboxed test suite executor: pytest, cargo test, or make test.

Runs the detected or requested test command as a bounded subprocess (never
through a shell, so no command-string injection surface) with an explicit
timeout, then extracts structured per-test failures. Failure extraction is
verified against real pytest and cargo output captured from this
environment's actual toolchain (see tests/test_test_runner.py), not
against an assumed format.

`strands.PosixShellSandbox` was considered instead of raw `subprocess`, but
it is an abstract base requiring a concrete `execute_streaming`
implementation to get any behavior at all, and its own docstring states the
base class does not enforce `timeout` itself -- a subclass must wire it in.
Plain `subprocess.run(timeout=...)` gives the same bound with less
indirection.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 300.0
_DEFAULT_TAIL_LINES = 40

_PYTEST_FAILURE_RE = re.compile(r"^(?:FAILED|ERROR) (\S+)(?: - (.*))?$", re.MULTILINE)
_CARGO_FAILURES_LIST_RE = re.compile(r"^failures:\n((?:    .+\n)+)", re.MULTILINE)
_CARGO_STDOUT_BLOCK_RE = re.compile(r"---- (\S+) stdout ----\n(.*?)(?=\n----|\nfailures:|\Z)", re.DOTALL)
_CARGO_PANIC_MESSAGE_RE = re.compile(r"panicked at [^\n]+:\n(.+?)(?:\nnote: run with|\Z)", re.DOTALL)
_MAKEFILE_TEST_TARGET_RE = re.compile(r"^test:", re.MULTILINE)


@dataclass(frozen=True)
class TestFailure:
    __test__ = False  # not a pytest test class despite the name
    name: str
    message: str


@dataclass(frozen=True)
class TestRunResult:
    __test__ = False  # not a pytest test class despite the name
    command: str
    exit_code: int
    passed: bool
    duration_seconds: float
    timed_out: bool
    stdout_tail: str
    failures: list[TestFailure]


def _as_text(value: str | bytes | None) -> str:
    assert value is None or isinstance(value, str | bytes)
    result = "" if value is None else value if isinstance(value, str) else value.decode("utf-8", errors="replace")
    assert isinstance(result, str)
    return result


def _tail(text: str, n_lines: int = _DEFAULT_TAIL_LINES) -> str:
    assert isinstance(text, str)
    assert n_lines > 0
    return "\n".join(text.splitlines()[-n_lines:])


def _has_pytest_markers(repo_path: Path) -> bool:
    assert repo_path.exists()
    assert repo_path.is_dir()
    if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
        return True
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and "[tool.pytest" in pyproject.read_text(encoding="utf-8"):
        return True
    tests_dir = repo_path / "tests"
    return tests_dir.is_dir() and any(tests_dir.glob("test_*.py"))


def _makefile_has_test_target(repo_path: Path) -> bool:
    assert repo_path.exists()
    makefile = repo_path / "Makefile"
    if not makefile.exists():
        return False
    content = makefile.read_text(encoding="utf-8")
    assert isinstance(content, str)
    return bool(_MAKEFILE_TEST_TARGET_RE.search(content))


def detect_test_command(repo_path: Path) -> str | None:
    assert repo_path.exists()
    assert repo_path.is_dir()
    if (repo_path / "Cargo.toml").exists():
        return "cargo test"
    if _has_pytest_markers(repo_path):
        return "pytest"
    if _makefile_has_test_target(repo_path):
        return "make test"
    return None


def parse_pytest_failures(output: str) -> list[TestFailure]:
    assert isinstance(output, str)
    failures = [
        TestFailure(name=m.group(1), message=(m.group(2) or "").strip() or "no message captured")
        for m in _PYTEST_FAILURE_RE.finditer(output)
    ]
    assert isinstance(failures, list)
    return failures


def _cargo_failed_names(output: str) -> list[str]:
    assert isinstance(output, str)
    match = _CARGO_FAILURES_LIST_RE.search(output)
    names = [line.strip() for line in match.group(1).splitlines() if line.strip()] if match else []
    assert isinstance(names, list)
    return names


def _cargo_message_for(name: str, output: str) -> str:
    assert isinstance(name, str)
    assert isinstance(output, str)
    for block_name, block in _CARGO_STDOUT_BLOCK_RE.findall(output):
        if block_name != name:
            continue
        panic = _CARGO_PANIC_MESSAGE_RE.search(block)
        if panic:
            return " ".join(panic.group(1).strip().splitlines())
    return "no message captured"


def parse_cargo_failures(output: str) -> list[TestFailure]:
    assert isinstance(output, str)
    names = _cargo_failed_names(output)
    failures = [TestFailure(name=n, message=_cargo_message_for(n, output)) for n in names]
    assert isinstance(failures, list)
    return failures


def _extract_failures(command: str, output: str, exit_code: int) -> list[TestFailure]:
    assert isinstance(command, str)
    assert isinstance(output, str)
    if exit_code == 0:
        return []
    if "pytest" in command:
        failures = parse_pytest_failures(output)
    elif "cargo" in command:
        failures = parse_cargo_failures(output)
    else:
        failures = []
    if not failures:
        failures = [TestFailure(name=command, message=_tail(output, 10))]
    assert isinstance(failures, list)
    return failures


def run_test_suite(
    repo_path: Path, command: str | None = None, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
) -> TestRunResult:
    assert repo_path.exists()
    assert timeout_seconds > 0.0
    resolved = command or detect_test_command(repo_path)
    if resolved is None:
        return TestRunResult(
            command="", exit_code=-1, passed=False, duration_seconds=0.0, timed_out=False,
            stdout_tail="no test command detected", failures=[],
        )
    start = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            shlex.split(resolved), cwd=repo_path, capture_output=True, text=True, timeout=timeout_seconds
        )
        exit_code, output = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out, exit_code = True, -1
        output = _as_text(exc.stdout) + _as_text(exc.stderr)
    duration = time.monotonic() - start
    failures = _extract_failures(resolved, output, exit_code)
    assert isinstance(failures, list)
    return TestRunResult(
        command=resolved, exit_code=exit_code, passed=(exit_code == 0 and not timed_out),
        duration_seconds=duration, timed_out=timed_out, stdout_tail=_tail(output), failures=failures,
    )
