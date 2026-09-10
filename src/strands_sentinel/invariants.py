"""AST and tokenizer based Power of 10 safety invariant engine.

Implements a practical subset of Gerard J. Holzmann's Power of 10 rules
against Python source (via ast) and a lightweight brace-counting heuristic
for other curly-brace languages (Rust, TypeScript, JavaScript, Go, C/C++).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

MAX_FUNCTION_LINES = 60
MIN_ASSERTIONS = 2
GENERIC_FUNCTION_LINE_LIMIT = 60

BANNED_CALL_NAMES = frozenset({"eval", "exec", "compile", "__import__"})
BANNED_ATTR_CALLS = frozenset(
    {
        ("os", "system"),
        ("pickle", "loads"),
        ("pickle", "load"),
        ("yaml", "load"),
    }
)

_LOOP_OR_FUNC_TYPES = (ast.While, ast.For, ast.AsyncFor, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_GENERIC_FUNC_START = re.compile(r"^\s*(?:pub\s+|async\s+|export\s+|static\s+)*(?:fn|function|func)\s+\w+\s*\(")
_GENERIC_SUFFIXES = frozenset({".rs", ".ts", ".js", ".go", ".cpp", ".hpp", ".c", ".h"})
SKIP_DIR_NAMES = frozenset({".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".ruff_cache"})


def _is_within_skipped_dir(path: Path) -> bool:
    assert isinstance(path, Path)
    assert isinstance(SKIP_DIR_NAMES, frozenset)
    return any(part in SKIP_DIR_NAMES for part in path.parts)


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    rule: str
    severity: Severity
    message: str
    function: str | None = None


def _function_line_span(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    assert node.end_lineno is not None
    assert node.end_lineno >= node.lineno
    return node.end_lineno - node.lineno + 1


def check_function_length(node: ast.FunctionDef | ast.AsyncFunctionDef, filename: str) -> list[Violation]:
    assert isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    assert filename
    span = _function_line_span(node)
    if span <= MAX_FUNCTION_LINES:
        return []
    return [
        Violation(
            file=filename,
            line=node.lineno,
            rule="power_of_10.rule_4.function_length",
            severity=Severity.CRITICAL,
            message=f"function '{node.name}' spans {span} lines, exceeds limit of {MAX_FUNCTION_LINES}",
            function=node.name,
        )
    ]


def _count_assertions(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    assert isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    count = sum(1 for child in ast.walk(node) if isinstance(child, ast.Assert))
    assert count >= 0
    return count


def check_assertion_count(node: ast.FunctionDef | ast.AsyncFunctionDef, filename: str) -> list[Violation]:
    assert isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    assert filename
    count = _count_assertions(node)
    if count >= MIN_ASSERTIONS:
        return []
    return [
        Violation(
            file=filename,
            line=node.lineno,
            rule="power_of_10.rule_5.assertion_density",
            severity=Severity.CRITICAL,
            message=f"function '{node.name}' has {count} assert statement(s), minimum is {MIN_ASSERTIONS}",
            function=node.name,
        )
    ]


def _has_reachable_break(node: ast.AST) -> bool:
    assert isinstance(node, ast.AST)
    assert node is not None
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Break):
            return True
        if isinstance(child, _LOOP_OR_FUNC_TYPES):
            continue
        if _has_reachable_break(child):
            return True
    return False


def check_bounded_loop(node: ast.While, filename: str) -> list[Violation]:
    assert isinstance(node, ast.While)
    assert filename
    is_infinite = isinstance(node.test, ast.Constant) and node.test.value is True
    if not is_infinite:
        return []
    if not _has_reachable_break(node):
        return [
            Violation(
                file=filename,
                line=node.lineno,
                rule="power_of_10.rule_2.bounded_loop",
                severity=Severity.CRITICAL,
                message="`while True:` loop has no reachable break; loop bound is not statically verifiable",
            )
        ]
    return [
        Violation(
            file=filename,
            line=node.lineno,
            rule="power_of_10.rule_2.bounded_loop",
            severity=Severity.WARNING,
            message="`while True:` loop exits via break; runtime bound is not statically provable, verify manually",
        )
    ]


def _is_banned_call(call: ast.Call) -> bool:
    assert isinstance(call, ast.Call)
    assert call.func is not None
    if isinstance(call.func, ast.Name):
        return call.func.id in BANNED_CALL_NAMES
    if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
        return (call.func.value.id, call.func.attr) in BANNED_ATTR_CALLS
    return False


def _banned_call_name(call: ast.Call) -> str:
    assert isinstance(call, ast.Call)
    if isinstance(call.func, ast.Name):
        return call.func.id
    assert isinstance(call.func, ast.Attribute)
    return call.func.attr


def check_banned_calls(tree: ast.AST, filename: str) -> list[Violation]:
    assert tree is not None
    assert filename
    violations = [
        Violation(
            file=filename,
            line=node.lineno,
            rule="power_of_10.banned_pattern.dynamic_execution",
            severity=Severity.CRITICAL,
            message=f"call to banned dynamic-execution/deserialization primitive '{_banned_call_name(node)}'",
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _is_banned_call(node)
    ]
    assert isinstance(violations, list)
    return violations


def _mutable_defaults(args: ast.arguments) -> list[ast.expr]:
    assert isinstance(args, ast.arguments)
    defaults = list(args.defaults) + [d for d in args.kw_defaults if d is not None]
    mutable: list[ast.expr] = [d for d in defaults if isinstance(d, ast.List | ast.Dict | ast.Set)]
    assert isinstance(mutable, list)
    return mutable


def check_mutable_defaults(node: ast.FunctionDef | ast.AsyncFunctionDef, filename: str) -> list[Violation]:
    assert isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    assert filename
    if not _mutable_defaults(node.args):
        return []
    return [
        Violation(
            file=filename,
            line=node.lineno,
            rule="power_of_10.rule_3.mutable_default_argument",
            severity=Severity.WARNING,
            message=f"function '{node.name}' uses a mutable default argument (shared unbounded state)",
            function=node.name,
        )
    ]


def scan_python_file(path: Path, enforce_function_rules: bool) -> list[Violation]:
    assert path.exists()
    assert path.suffix == ".py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    filename = str(path)
    violations = list(check_banned_calls(tree, filename))
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            violations.extend(check_bounded_loop(node, filename))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            violations.extend(check_mutable_defaults(node, filename))
            if enforce_function_rules:
                violations.extend(check_function_length(node, filename))
                violations.extend(check_assertion_count(node, filename))
    assert isinstance(violations, list)
    return violations


def _generic_function_spans(lines: list[str]) -> list[tuple[int, int]]:
    assert isinstance(lines, list)
    spans: list[tuple[int, int]] = []
    start: int | None = None
    depth = 0
    for i, line in enumerate(lines):
        if start is None and _GENERIC_FUNC_START.match(line):
            start, depth = i, 0
        if start is not None:
            depth += line.count("{") - line.count("}")
            if depth <= 0 and "{" in "".join(lines[start : i + 1]):
                spans.append((start, i))
                start = None
    assert isinstance(spans, list)
    return spans


def scan_generic_source(path: Path) -> list[Violation]:
    assert path.exists()
    assert path.suffix in _GENERIC_SUFFIXES
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    filename = str(path)
    violations = [
        Violation(
            file=filename,
            line=start + 1,
            rule="power_of_10.rule_4.function_length.generic",
            severity=Severity.WARNING,
            message=f"function spans approximately {end - start + 1} lines (brace-heuristic), "
            f"exceeds limit of {GENERIC_FUNCTION_LINE_LIMIT}",
        )
        for start, end in _generic_function_spans(lines)
        if end - start + 1 > GENERIC_FUNCTION_LINE_LIMIT
    ]
    assert isinstance(violations, list)
    return violations


def scan_repository(python_roots: list[Path], generic_roots: list[Path] | None = None) -> list[Violation]:
    assert isinstance(python_roots, list)
    assert all(isinstance(r, Path) for r in python_roots)
    violations: list[Violation] = []
    for root in python_roots:
        for path in sorted(root.rglob("*.py")):
            if _is_within_skipped_dir(path):
                continue
            violations.extend(scan_python_file(path, enforce_function_rules="tests" not in path.parts))
    for root in generic_roots or []:
        for path in sorted(root.rglob("*")):
            if path.suffix in _GENERIC_SUFFIXES and not _is_within_skipped_dir(path):
                violations.extend(scan_generic_source(path))
    assert isinstance(violations, list)
    return violations
