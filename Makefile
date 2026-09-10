.PHONY: install test lint audit-invariants demo clean

VENV := .venv
PYTHON := $(VENV)/bin/python3

install:
	uv venv $(VENV) --python python3.12
	uv pip install --python $(PYTHON) -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/mypy src/ scripts/

audit-invariants:
	$(PYTHON) scripts/audit_safety_invariants.py

demo:
	$(VENV)/bin/strands-sentinel check src/strands_sentinel

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -not -path "./$(VENV)/*" -exec rm -rf {} +
