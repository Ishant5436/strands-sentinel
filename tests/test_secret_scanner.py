"""Tests for the zero-tolerance secret scanner."""

from __future__ import annotations

from pathlib import Path

from strands_sentinel.invariants import Severity
from strands_sentinel.secret_scanner import (
    redact,
    scan_directory,
    scan_file,
    scan_line,
    shannon_entropy,
)


def test_shannon_entropy_of_empty_string_is_zero() -> None:
    assert shannon_entropy("") == 0.0


def test_shannon_entropy_of_repeated_character_is_zero() -> None:
    assert shannon_entropy("aaaaaaaaaa") == 0.0


def test_shannon_entropy_of_random_looking_token_exceeds_threshold() -> None:
    assert shannon_entropy("aK9$mZ2!qP7&xR4@vN1#wL8%") > 3.8


def test_redact_short_secret_is_fully_masked() -> None:
    assert redact("short") == "*****"


def test_redact_long_secret_preserves_prefix_and_suffix_only() -> None:
    redacted = redact("AKIAABCDEFGHIJKLMNOP")
    assert redacted.startswith("AKIA")
    assert redacted.endswith("OP")
    assert "ABCDEFGHIJKLMN" not in redacted


def test_aws_access_key_is_detected_as_critical() -> None:
    findings = scan_line('aws_key = "AKIAABCDEFGHIJKLMNOP"', 1, "f.py")
    matched = [f for f in findings if f.rule == "secret.aws_access_key_id"]
    assert len(matched) == 1
    assert matched[0].severity == Severity.CRITICAL


def test_github_pat_is_detected_as_critical() -> None:
    token = "ghp_" + "a" * 36
    findings = scan_line(f'token = "{token}"', 1, "f.py")
    matched = [f for f in findings if f.rule == "secret.github_pat"]
    assert len(matched) == 1
    assert matched[0].severity == Severity.CRITICAL


def test_evm_private_key_is_detected_as_critical() -> None:
    key = "0x" + "a" * 64
    findings = scan_line(f'priv_key = "{key}"', 1, "f.py")
    matched = [f for f in findings if f.rule == "secret.evm_private_key"]
    assert len(matched) == 1
    assert matched[0].severity == Severity.CRITICAL


def test_twelve_word_mnemonic_is_detected_as_critical() -> None:
    phrase = "abandon ability able about above absent absorb abstract absurd abuse access accident"
    findings = scan_line(phrase, 1, "f.py")
    matched = [f for f in findings if f.rule == "secret.mnemonic_seed_phrase"]
    assert len(matched) == 1
    assert matched[0].severity == Severity.CRITICAL


def test_eleven_word_phrase_is_not_flagged_as_mnemonic() -> None:
    phrase = "abandon ability able about above absent absorb abstract absurd abuse access"
    findings = scan_line(phrase, 1, "f.py")
    assert not any(f.rule == "secret.mnemonic_seed_phrase" for f in findings)


def test_deterministic_match_is_not_double_reported_by_entropy_scan() -> None:
    key = "0x" + "a" * 64
    findings = scan_line(f'priv_key = "{key}"', 1, "f.py")
    assert len(findings) == 1


def test_high_entropy_token_without_known_pattern_is_warning() -> None:
    findings = scan_line('token = "aK9mZ2qP7xR4vN1wL8bQ5tY3fH6jD0sG2"', 1, "f.py")
    matched = [f for f in findings if f.rule == "secret.high_entropy_token"]
    assert len(matched) == 1
    assert matched[0].severity == Severity.WARNING
    assert matched[0].entropy is not None


def test_clean_line_has_no_findings() -> None:
    assert scan_line("x = compute_result(a, b)", 1, "f.py") == []


def test_scan_file_reports_correct_line_numbers(tmp_path: Path) -> None:
    key = "AKIAABCDEFGHIJKLMNOP"
    path = tmp_path / "config.py"
    path.write_text(f'a = 1\nb = 2\nsecret = "{key}"\n', encoding="utf-8")
    findings = scan_file(path)
    assert len(findings) == 1
    assert findings[0].line == 3


def test_scan_file_never_returns_raw_secret_value(tmp_path: Path) -> None:
    key = "AKIAABCDEFGHIJKLMNOP"
    path = tmp_path / "config.py"
    path.write_text(f'secret = "{key}"\n', encoding="utf-8")
    findings = scan_file(path)
    assert len(findings) == 1
    assert key not in findings[0].redacted


def test_scan_directory_skips_venv_and_git_dirs(tmp_path: Path) -> None:
    key = "AKIAABCDEFGHIJKLMNOP"
    skipped = tmp_path / ".venv" / "lib"
    skipped.mkdir(parents=True)
    (skipped / "leaked.py").write_text(f'x = "{key}"\n', encoding="utf-8")
    included = tmp_path / "app.py"
    included.write_text(f'y = "{key}"\n', encoding="utf-8")
    findings = scan_directory(tmp_path)
    assert len(findings) == 1
    assert findings[0].file.endswith("app.py")


def test_scan_file_handles_binary_file_without_crashing(tmp_path: Path) -> None:
    path = tmp_path / "binary.dat"
    path.write_bytes(b"\xff\xfe\x00\x01\x02\x03")
    assert scan_file(path) == []
