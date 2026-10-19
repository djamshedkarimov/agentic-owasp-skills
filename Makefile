SEMGREP_VERSION := 1.179.0
TS_EXAMPLES := examples/typescript
RULES := skills/mcp-security/rules

.PHONY: install lint format test check

install:
	uv sync --locked
	uv tool install --force semgrep==$(SEMGREP_VERSION)
	semgrep --version
	npm ci --prefix $(TS_EXAMPLES)

lint:
	uv run ruff check .
	uv run ruff format --check .
	npm run --prefix $(TS_EXAMPLES) typecheck

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	semgrep scan --test --metrics=off --disable-version-check $(RULES)
	uv run pytest

check: lint test
