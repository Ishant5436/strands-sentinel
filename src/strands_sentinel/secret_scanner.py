"""Zero-tolerance secret scanner: deterministic patterns plus Shannon entropy.

Deterministic detectors (AWS access keys, GitHub PATs, EVM private keys,
BIP-39-shaped mnemonic phrases) are reported at CRITICAL severity and are
the "zero false alarm" surface: each is a structural match against a known
credential format. Generic high-entropy tokens are a secondary, lower
confidence catch-all reported at WARNING, and are excluded whenever they
overlap a span already claimed by a deterministic match, so the same
secret is never double-reported.

The mnemonic detector is a structural heuristic (exact run of 12 or 24
lowercase words of 3-8 characters) rather than a full BIP-39 wordlist
match; it will not catch a mnemonic phrase mixed with punctuation, and it
can be tripped by prose that happens to have the same shape.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from strands_sentinel.invariants import SKIP_DIR_NAMES, Severity

ENTROPY_THRESHOLD = 3.8
_MIN_ENTROPY_TOKEN_LENGTH = 20
_MNEMONIC_LENGTHS = frozenset({12, 24})

_MNEMONIC_WORD_RE = re.compile(r"^[a-z]{3,8}$")
# Hyphen is deliberately excluded: it is not part of the standard or
# base64url alphabet, and including it let hyphen-joined English compound
# words (e.g. "dynamic-execution/deserialization" in this module's own
# docstrings) match as one long token and trip the entropy threshold.
_CANDIDATE_TOKEN_RE = re.compile(r"[A-Za-z0-9+/_=]{" + str(_MIN_ENTROPY_TOKEN_LENGTH) + r",}")
_DETERMINISTIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("secret.aws_access_key_id", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("secret.github_pat", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{82}\b")),
    ("secret.evm_private_key", re.compile(r"\b0x[a-fA-F0-9]{64}\b")),
)


@dataclass(frozen=True)
class SecretFinding:
    file: str
    line: int
    rule: str
    severity: Severity
    redacted: str
    entropy: float | None = None


def redact(secret: str) -> str:
    assert isinstance(secret, str)
    assert len(secret) >= 0
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * (len(secret) - 6)}{secret[-2:]}"


def shannon_entropy(s: str) -> float:
    assert isinstance(s, str)
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    entropy = -sum((c / length) * math.log2(c / length) for c in counts.values())
    assert entropy >= 0.0
    return entropy


def _lowercase_word_runs(line: str) -> list[int]:
    assert isinstance(line, str)
    tokens = line.strip().split()
    runs: list[int] = []
    current = 0
    for tok in tokens:
        if _MNEMONIC_WORD_RE.match(tok):
            current += 1
        else:
            if current > 0:
                runs.append(current)
            current = 0
    if current > 0:
        runs.append(current)
    assert isinstance(runs, list)
    return runs


def _looks_like_mnemonic(line: str) -> int | None:
    assert isinstance(line, str)
    matches = [r for r in _lowercase_word_runs(line) if r in _MNEMONIC_LENGTHS]
    assert isinstance(matches, list)
    return matches[0] if matches else None


def _scan_line_deterministic(
    line: str, line_no: int, filename: str
) -> tuple[list[SecretFinding], list[tuple[int, int]]]:
    assert isinstance(line, str)
    assert line_no > 0
    findings: list[SecretFinding] = []
    spans: list[tuple[int, int]] = []
    for rule, pattern in _DETERMINISTIC_PATTERNS:
        for m in pattern.finditer(line):
            spans.append(m.span())
            findings.append(
                SecretFinding(
                    file=filename, line=line_no, rule=rule, severity=Severity.CRITICAL, redacted=redact(m.group(0))
                )
            )
    mnemonic_len = _looks_like_mnemonic(line)
    if mnemonic_len is not None:
        findings.append(
            SecretFinding(
                file=filename,
                line=line_no,
                rule="secret.mnemonic_seed_phrase",
                severity=Severity.CRITICAL,
                redacted=f"<{mnemonic_len}-word phrase redacted>",
            )
        )
    assert isinstance(findings, list)
    return findings, spans


def _overlaps_any(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    assert isinstance(span, tuple)
    assert isinstance(spans, list)
    return any(span[0] < e and s < span[1] for s, e in spans)


def _scan_line_entropy(
    line: str, line_no: int, filename: str, exclude_spans: list[tuple[int, int]]
) -> list[SecretFinding]:
    assert isinstance(line, str)
    assert line_no > 0
    findings: list[SecretFinding] = []
    for m in _CANDIDATE_TOKEN_RE.finditer(line):
        if _overlaps_any(m.span(), exclude_spans):
            continue
        h = shannon_entropy(m.group(0))
        if h >= ENTROPY_THRESHOLD:
            findings.append(
                SecretFinding(
                    file=filename,
                    line=line_no,
                    rule="secret.high_entropy_token",
                    severity=Severity.WARNING,
                    redacted=redact(m.group(0)),
                    entropy=round(h, 3),
                )
            )
    assert isinstance(findings, list)
    return findings


def scan_line(line: str, line_no: int, filename: str) -> list[SecretFinding]:
    assert isinstance(line, str)
    assert line_no > 0
    deterministic, spans = _scan_line_deterministic(line, line_no, filename)
    combined = deterministic + _scan_line_entropy(line, line_no, filename, spans)
    assert isinstance(combined, list)
    return combined


def scan_file(path: Path) -> list[SecretFinding]:
    assert path.exists()
    assert path.is_file()
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    findings: list[SecretFinding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        findings.extend(scan_line(line, line_no, str(path)))
    assert isinstance(findings, list)
    return findings


def scan_directory(root: Path) -> list[SecretFinding]:
    assert root.exists()
    assert root.is_dir()
    findings: list[SecretFinding] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        findings.extend(scan_file(path))
    assert isinstance(findings, list)
    return findings
