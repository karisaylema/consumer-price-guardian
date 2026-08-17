.PHONY: help install lint fmt test cov build tf-fmt tf-validate clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime + dev dependencies
	pip install -r requirements.txt

lint: ## Lint with ruff
	ruff check src tests

fmt: ## Auto-format / auto-fix with ruff
	ruff check --fix src tests
	ruff format src tests

test: ## Run unit tests (no AWS needed)
	pytest tests/unit

cov: ## Run unit tests with coverage
	pytest tests/unit --cov=src --cov-report=term-missing

build: ## Build the RAG Lambda deployment package
	scripts/build_lambda.sh

tf-fmt: ## Check Terraform formatting
	terraform -chdir=infra fmt -check -recursive

tf-validate: ## Validate Terraform (no backend)
	terraform -chdir=infra init -backend=false >/dev/null
	terraform -chdir=infra validate

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov infra/build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
