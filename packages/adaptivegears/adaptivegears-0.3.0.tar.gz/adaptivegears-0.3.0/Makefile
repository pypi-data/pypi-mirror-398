.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: dev
dev: ## Run CLI help
	uv run adaptivegears --help

.PHONY: test
test: ## Run tests
	uv run pytest tests/ -v

.PHONY: lint
lint: ## Run linter
	uv run ruff check .

.PHONY: fmt
fmt: ## Format code
	uv run ruff format .

.PHONY: build
build: ## Build package
	rm -rf dist/
	uv build

.PHONY: deploy
deploy: build ## Publish to PyPI
	uv publish

.PHONY: clean
clean: ## Remove build artifacts
	rm -rf dist/ *.egg-info .venv/ __pycache__/
