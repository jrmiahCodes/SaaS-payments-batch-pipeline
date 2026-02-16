SHELL := /bin/bash
PYTHON ?= python3
VENV ?= .venv

PIPELINE_ENV ?= LOCAL
LOCAL_DATA_DIR ?= ./_local_data
MOCK_API_BASE_URL ?= http://127.0.0.1:8000
DAYS ?= 1
ENTITY ?= charges

.DEFAULT_GOAL := help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

venv: ## Create virtual environment
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)

install: venv ## Install project with dev dependencies
	@source $(VENV)/bin/activate && pip install -U pip
	@source $(VENV)/bin/activate && pip install -e ".[dev]"

setup: install ## Bootstrap local development environment

lint: ## Run ruff lint checks
	@source $(VENV)/bin/activate && ruff check .

format: ## Format code with ruff
	@source $(VENV)/bin/activate && ruff format .

format-check: ## Verify formatting without modifying files
	@source $(VENV)/bin/activate && ruff format --check .

typecheck: ## Run mypy type checks
	@source $(VENV)/bin/activate && mypy src

test: ## Run pytest test suite
	@source $(VENV)/bin/activate && pytest -q

mock-api: ## Run mock Stripe-like API on localhost:8000
	@source $(VENV)/bin/activate && $(PYTHON) -m mock_api.app

run-batch: ## Run batch extract for one entity (ENTITY=charges DAYS=1)
	@source $(VENV)/bin/activate && PIPELINE_ENV=$(PIPELINE_ENV) LOCAL_DATA_DIR=$(LOCAL_DATA_DIR) MOCK_API_BASE_URL=$(MOCK_API_BASE_URL) payments-pipeline run-batch --entity $(ENTITY) --days $(DAYS)

run-all: ## Run extraction for all entities
	@source $(VENV)/bin/activate && PIPELINE_ENV=$(PIPELINE_ENV) LOCAL_DATA_DIR=$(LOCAL_DATA_DIR) MOCK_API_BASE_URL=$(MOCK_API_BASE_URL) payments-pipeline run-all --days $(DAYS)

run-transforms: ## Run silver and gold transforms
	@source $(VENV)/bin/activate && PIPELINE_ENV=$(PIPELINE_ENV) LOCAL_DATA_DIR=$(LOCAL_DATA_DIR) payments-pipeline run-transforms

run-quality: ## Run schema/freshness/reconciliation checks
	@source $(VENV)/bin/activate && PIPELINE_ENV=$(PIPELINE_ENV) LOCAL_DATA_DIR=$(LOCAL_DATA_DIR) payments-pipeline run-quality

run-pipeline: ## Run extract -> transform -> quality with one run_id
	@source $(VENV)/bin/activate && PIPELINE_ENV=$(PIPELINE_ENV) LOCAL_DATA_DIR=$(LOCAL_DATA_DIR) MOCK_API_BASE_URL=$(MOCK_API_BASE_URL) payments-pipeline run-pipeline --days $(DAYS)

run-webhooks: ## Run webhook server (localhost:8000)
	@source $(VENV)/bin/activate && PIPELINE_ENV=$(PIPELINE_ENV) LOCAL_DATA_DIR=$(LOCAL_DATA_DIR) payments-pipeline run-webhooks --host 0.0.0.0 --port 8000

clean: ## Remove local outputs and caches
	rm -rf $(VENV) _local_data .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
