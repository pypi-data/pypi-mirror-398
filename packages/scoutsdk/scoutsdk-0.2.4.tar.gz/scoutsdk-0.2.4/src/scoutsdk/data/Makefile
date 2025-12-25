GIT_REVISION = `git rev-parse HEAD`

.DEFAULT_GOAL := help

# Introspection targets
# ---------------------
.PHONY: help
help: ## Show available targets
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
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# Dependencies
# -------------------
.PHONY: dependencies
dependencies: ## Setup virtual environment and install dependencies
	@make setupvenv
	@source ".venv/bin/activate" && uv sync

.PHONY: setupvenv
setupvenv: ## Create virtual environment
	@uv venv
	@source ".venv/bin/activate"


# Sync assistants
# -------------------	
.PHONY: sync_assistants
sync_assistants: ## Sync assistants configuration
	# Ensure current directory is the root of the project
	pushd functions && \
	uv pip compile pyproject.toml -o requirements.txt && \
	popd && \
	pushd assistant && \
	echo "** Synchronizing assistants..." && \
	scoutcli --verbose synchronize-assistants -c assistants.json
