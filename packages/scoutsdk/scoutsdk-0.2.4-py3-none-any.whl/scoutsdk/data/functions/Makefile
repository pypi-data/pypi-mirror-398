# Build configuration
# -------------------

APP_NAME = `grep -m1 name package.json | awk -F: '{ print $$2 }' | sed 's/[ ",]//g'`
APP_VERSION = `grep -m1 version package.json | awk -F: '{ print $$2 }' | sed 's/[ ",]//g'`
GIT_REVISION = `git rev-parse HEAD`

# Introspection targets
# ---------------------
.PHONY: help
help: header targets

.PHONY: header
header:
	@echo "\033[34mEnvironment\033[0m"
	@echo "\033[34m---------------------------------------------------------------\033[0m"
	@printf "\033[33m%-23s\033[0m" "GIT_REVISION"
	@printf "\033[35m%s\033[0m" $(GIT_REVISION)
	@echo "\n"

.PHONY: targets
targets:
	@echo "\033[34mTargets\033[0m"
	@echo "\033[34m---------------------------------------------------------------\033[0m"
	@perl -nle'print $& if m{^[a-zA-Z_-\d]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'


# Dependencies
# -------------------
.PHONY: dependencies
dependencies: ## Setup virtual environment and install dependencies
	@make setupvenv
	@source ".venv/bin/activate" && uv sync

.PHONY: setupvenv
setupvenv: ## Create a virtual environment
	@uv venv
	@source ".venv/bin/activate"

.PHONY: lock-dependencies
lock-dependencies: ## Lock the dependencies
	@uv pip freeze | uv pip compile - -o requirements.txt

# Format / Linting
# -------------------
.PHONY: format
format: ## Format the code
	ruff check . --fix
	ruff format .

.PHONY: check
check: ## Check the linting rules
	@ruff check .
	@ruff format --check .
	@mypy main.py
