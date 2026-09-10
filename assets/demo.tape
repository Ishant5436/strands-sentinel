Output "assets/strands_sentinel_demo.gif"
Output "assets/strands_sentinel_demo_raw.mp4"

Set FontSize 14
Set Width 1280
Set Height 760
Set Padding 20
Set Theme "TokyoNight"
Set TypingSpeed 30ms

Type "# Strands Sentinel: Autonomous Systems & AST Safety Auditor"
Enter
Type "# Built with AWS Strands Agents SDK and Model Context Protocol (MCP)"
Enter
Sleep 3s

Type "source .venv/bin/activate"
Enter
Sleep 1s

Type "strands-sentinel check src/strands_sentinel"
Enter
Sleep 4s

Type "python scripts/audit_safety_invariants.py"
Enter
Sleep 4s

Type "pytest tests/test_intervention.py -v"
Enter
Sleep 4s

Type "make test"
Enter
Sleep 9s

Type "git status"
Enter
Sleep 6s
