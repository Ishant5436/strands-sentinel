# Devpost Submission Package: Strands Sentinel
## Autonomous Mission-Critical Systems & AST Safety Auditor
### Competition: AWS Agents for Humans Hackathon ($40,000 Prize Pool)

---

### Project Overview
* **Project Name:** Strands Sentinel
* **Tagline:** Autonomous mission-critical systems and AST safety auditor built with the Strands Agents SDK and Model Context Protocol (MCP).
* **Track:** Professional Agents
* **Repository:** [https://github.com/Ishant5436/strands-sentinel](https://github.com/Ishant5436/strands-sentinel)
* **License:** MIT License
* **Author / Developer:** Ishant Panchal (`Ishant5436` / `ishant.p@somaiya.edu`)

---

### Elevator Pitch
Strands Sentinel is an autonomous background auditor for mission-critical software and quantitative systems. Built with the open-source Strands Agents SDK and Model Context Protocol (MCP), it silently observes codebases to verify Gerard J. Holzmann's NASA Power of 10 AST safety invariants, scan for exposed credentials using deterministic regex and Shannon entropy, and execute sandboxed test suites. Utilizing Strands' native `InterventionHandler`, it runs quietly in the background and only interrupts the engineer when an invariant violation or credential leak requires an explicit human decision.

---

### Inspiration & Problem Statement
Software engineers and quantitative developers spend 10 to 15 hours each week on repetitive, manual review tasks:
1. **Linter Fatigue:** Conventional static analyzers generate walls of noisy warnings, obscuring critical bugs behind minor stylistic nits.
2. **Safety Invariant Enforcement:** High-reliability systems (e.g., algorithmic execution, embedded systems, financial infrastructure) mandate deterministic invariants such as bounded loops, maximum function lengths, and high assertion density. Under release deadlines, reviewers routinely miss these structural defects.
3. **Secret Leakage:** Engineers accidentally commit API tokens, private keys, and cloud credentials to repositories.
4. **Context Switching:** Most security tools demand context switching to external dashboards or web portals, interrupting deep focus.

Strands Sentinel addresses the core hackathon mission: rather than introducing another dashboard to monitor, the agent operates in the background and surfaces exclusively when an executive human decision is required.

---

### What It Does & How It Works
Strands Sentinel integrates five deterministic tools behind an intelligent agent orchestrator:
1. **AST Invariant Verification (`invariants.py`):** Parses source trees using Python's native `ast` module and multi-language tokenizers. It checks function length limits (<= 60 lines), assertion density (>= 2 assertions per function), bounded loops (flags unbounded loops), mutable default arguments, and banned dynamic execution patterns (`eval`, `exec`, `os.system`).
2. **Deterministic & Entropy Secret Scanner (`secret_scanner.py`):** Scans files for exposed credentials using deterministic patterns (AWS access keys, GitHub PATs, EVM private keys, 12/24-word mnemonics) and Shannon entropy ($H \ge 3.8$). All findings are redacted before leaving the scanner; raw secret values are never printed, logged, or returned.
3. **Sandboxed Test Harness (`test_runner.py`):** Automatically discovers and executes `pytest`, `cargo test`, or `make test` within a bounded subprocess, parsing structured failures without exposing a shell injection surface.
4. **Strands Decision Gate (`intervention.py`):** Implements `SentinelInterventionHandler` by subclassing `strands.interventions.InterventionHandler`. Read-only audit tools proceed automatically. Mutating remediation tools (or actions taken while a critical finding is unresolved) require explicit human confirmation via `Confirm(prompt=...)`.
5. **Model Router (`agent.py`):** Connects to Amazon Bedrock (`BedrockModel`), Anthropic Claude, OpenAI, Google Gemini, or local Ollama instances, defaulting gracefully based on available environment credentials.
6. **Model Context Protocol Integration (`mcp_server.py`):** Exposes all auditor tools via `mcp.server.mcpserver.MCPServer`, allowing integration into Claude Code CLI, Google Antigravity, Cursor, and Bedrock AgentCore.

---

### How We Built It
- **Language & Environment:** Python 3.12 managed via `uv`.
- **Frameworks:** `strands-agents` (v1.55+), `strands-agents-tools` (v0.8.8+), and `mcp` (v2.1+).
- **Quality Gates:** 100% test coverage across 85 unit and integration tests (`pytest`).
- **Self-Auditing:** The codebase verifies itself against its own Power of 10 safety rules using `scripts/audit_safety_invariants.py`.

---

### Technical Challenges & Empirical Lessons
1. **SDK Parameter Validation:** Initial documentation references indicated `Confirm(message=...)`. Verification against the installed `strands-agents` package source code revealed the correct field name is `prompt`. The code was adjusted to conform to the runtime interface.
2. **MCP v2 Migration:** In `mcp>=2.1.0`, legacy FastMCP interfaces were restructured into `mcp.server.mcpserver.MCPServer`. The server was implemented against the current specification.
3. **Entropy Scanner Tuning:** Early entropy scanning flagged hyphenated multi-word identifiers in documentation strings. The tokenizer was tuned to filter out hyphenated prose while maintaining high sensitivity to base64, hex, and random character tokens.
4. **Environment Exclusion:** Ensured that repository scans explicitly ignore `.venv`, `.git`, `node_modules`, and cache directories to maintain sub-15ms scan latencies.

---

### Key Accomplishments & Metrics
- **85/85 Automated Tests Passing:** Complete coverage across AST parsing, secret detection, intervention lifecycle, and subprocess isolation.
- **Zero Lint & Static Analysis Errors:** Passes `ruff check` and `mypy --strict` with zero warnings.
- **Zero Invariant Violations:** Validated by `scripts/audit_safety_invariants.py` over all 9 source files.
- **Measured Performance:** Full AST invariant scan completes in 13.6 ms; secret scan completes in 2.6 ms.

---

### 5-Minute Video Demonstration Script

#### Part 1: Problem Space (0:00 - 1:00)
- **Visual:** Terminal title card and problem architecture diagram.
- **Narrator:** "Software development teams lose hours every week triaging noisy linter outputs and manually verifying safety standards. Critical invariants like bounded loops, assertion density, and secret prevention are easily missed under release pressure. We built Strands Sentinel using the AWS Strands Agents SDK to automate these repetitive checks in the background."

#### Part 2: Architecture & Decision Gating (1:00 - 2:00)
- **Visual:** Show Mermaid diagram from README and code in `src/strands_sentinel/intervention.py`.
- **Narrator:** "Strands Sentinel combines five deterministic tools with a Strands Agent. Most importantly, it implements an `InterventionHandler`. Routine checks pass silently in the background without disturbing the engineer. When a critical invariant violation or secret leak occurs, the agent pauses and surfaces a confirmation prompt with an exact remediation patch."

#### Part 3: Live Terminal Demonstration (2:00 - 4:00)
- **Visual:** Terminal execution.
- **Steps:**
  1. Run `make demo`: Show clean check against `src/strands_sentinel/` (0 critical violations).
  2. Introduce an intentional defect: Add an unbounded `while True` loop and an unredacted API key in a test file.
  3. Trigger `strands-sentinel check`: Demonstrate instant detection, structured Rich table reporting, and exit code 1.
  4. Demonstrate the Strands Agent intervention: Agent requests human confirmation before applying the remediation.
  5. Run `make test`: 85 passing tests in ~1-5 seconds.
  6. Run `make audit-invariants`: 0 violations.

#### Part 4: Conclusion & Value Proposition (4:00 - 5:00)
- **Visual:** Summary slide with benchmarks and GitHub repository link.
- **Narrator:** "Strands Sentinel transforms safety compliance from a noisy chore into a silent background guard. It provides deterministic guarantees for systems engineers and quantitative developers. The repository is open-source under the MIT license at github.com/Ishant5436/strands-sentinel."
