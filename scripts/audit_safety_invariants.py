#!/usr/bin/env python3
"""Standalone Power of 10 safety invariant audit over this repository.

Scans both src/ and scripts/ (this file included) so the auditor holds
itself to the same bar it enforces on the rest of the codebase. Exits
non-zero if any WARNING or CRITICAL violation is found; INFO-level output
is a summary, not a violation.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from strands_sentinel.invariants import Severity, scan_repository  # noqa: E402


def _print_violation(v: object) -> None:
    assert v is not None
    assert hasattr(v, "severity")
    print(f"{v.severity.value:9s} {v.rule:50s} {v.file}:{v.line} :: {v.message}")  # type: ignore[attr-defined]


def main() -> int:
    assert REPO_ROOT.exists()
    assert (REPO_ROOT / "src").exists()
    roots = [REPO_ROOT / "src", REPO_ROOT / "scripts"]
    violations = scan_repository(python_roots=roots)
    blocking = [v for v in violations if v.severity in (Severity.WARNING, Severity.CRITICAL)]
    for v in sorted(violations, key=lambda x: (x.file, x.line)):
        _print_violation(v)
    print()
    print(f"scanned roots: {[str(r) for r in roots]}")
    print(f"total violations: {len(violations)} (blocking: {len(blocking)})")
    assert isinstance(blocking, list)
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
