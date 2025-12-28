.PHONY: test test_watch lint format

######################
# TESTING AND COVERAGE
######################

start-mssql:
	docker compose up -V --force-recreate --wait || ( \
		echo "Failed to start MSSQL, printing logs..."; \
		docker compose logs; \
		exit 1 \
	)

stop-mssql:
	docker compose down

TEST ?= .
test:
	@make start-mssql
	@uv run pytest $(TEST)
	@EXIT_CODE=$$?; \
	make stop-mssql; \
	exit $$EXIT_CODE

test_watch:
	make start-mssql; \
	uv run ptw $(TEST); \
	EXIT_CODE=$$?; \
	make stop-mssql; \
	exit $$EXIT_CODE

######################
# LINTING AND FORMATTING
######################

PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --relative --diff-filter=d main . | grep -E '\.py$$|\.ipynb$$')

lint lint_diff:
	uv run ruff check .
	[ "$(PYTHON_FILES)" = "" ] || uv run ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || uv run ruff check --select I $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || uv run basedpyright $(PYTHON_FILES)

format format_diff:
	uv run ruff format $(PYTHON_FILES)
	uv run ruff check --select I --fix $(PYTHON_FILES)
