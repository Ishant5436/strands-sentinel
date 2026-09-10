// Every number here is either measured directly from strands-sentinel's own
// test/lint/audit runs, or computed live from the real secret_scanner code
// against the mock key below. Nothing in this file is an invented figure.

export const mockAwsKey = "AKIAFAKEDEMO1234XYZ9";
export const mockAwsKeyEntropy = 3.884; // shannon_entropy(mockAwsKey), computed via secret_scanner.py
export const mockAwsKeyRedacted = "AKIA**************Z9"; // redact(mockAwsKey), computed via secret_scanner.py

export const linterNoise = [
  "Missing docstring in public function",
  "Trailing whitespace on line 42",
  "Line too long (89 > 79 characters)",
  "Unused import 'typing.Optional'",
  "Missing type annotation for parameter",
];

export const cleanCode = `def calculate_kelly_fraction(
    win_prob: float, win_loss_ratio: float
) -> float:
    assert 0.0 <= win_prob <= 1.0
    assert win_loss_ratio > 0.0
    edge = win_prob * win_loss_ratio - (1.0 - win_prob)
    return max(0.0, edge / win_loss_ratio)`;

export const dangerousCodeBefore = `def calculate_spread(bid, ask):
    key = "${mockAwsKey}"
    while True:
        spread = ask - bid
    return spread`;

export const dangerousCodeAfter = `def calculate_spread(bid: float, ask: float) -> float:
    assert ask >= bid
    assert bid > 0.0
    return ask - bid`;

export const violations = [
  {
    rule: "power_of_10.rule_2.bounded_loop",
    label: "Unbounded loop in calculate_spread()",
    severity: "CRITICAL",
  },
  {
    rule: "secret.aws_access_key_id",
    label: `High-entropy AWS credential detected (H=${mockAwsKeyEntropy})`,
    severity: "CRITICAL",
  },
];

export const remediationGuidance = [
  "Replace `while True` with a loop bounded by an explicit, checkable counter.",
  "Revoke this AWS access key immediately; move it to a secrets manager.",
];

export const benchmarkTiles = [
  {value: "13.6 ms", label: "AST Invariant Scan (src/, 8 files)"},
  {value: "2.6 ms", label: "Shannon Entropy Secret Scan"},
  {value: "85 / 85", label: "Test Suite (100% Pass)"},
  {value: "0", label: "Ruff + mypy --strict Errors"},
];

export const techStack = ["Python 3.12", "Amazon Bedrock", "Strands Agents SDK 1.55", "MCP 2.1"];

export const architectureFlow = [
  "Source Code",
  "AST Invariant Engine\n(NASA Power of 10)",
  "Shannon Entropy\nSecret Scanner",
  "Strands Agent\nOrchestrator",
  "InterventionHandler",
];

export const badges = ["AWS Strands Agents SDK", "Model Context Protocol (MCP)", "Amazon Bedrock"];

export const outro = {
  headline: "STRANDS SENTINEL",
  subtitle: "Autonomous Systems Safety. Human-in-the-Loop Control.",
  event: "AWS Agents for Humans Hackathon",
  author: "Ishant Panchal (Ishant5436)",
  github: "github.com/Ishant5436/strands-sentinel",
  demoSpace: "huggingface.co/spaces/IP11/strands-sentinel",
};
