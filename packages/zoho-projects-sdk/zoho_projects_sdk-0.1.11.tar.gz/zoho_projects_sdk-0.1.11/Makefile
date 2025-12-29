# Makefile for Zoho Projects SDK development tasks

# Variables
PYTHON := python3
UV := uv
PIP := $(UV) pip
TEST_DIR := tests
SRC_DIR := src
PACKAGE := zoho_projects_sdk
PACKAGE_DIR := $(SRC_DIR)/$(PACKAGE)

# Help target
.PHONY: help
help: ## Display this help message
	@echo "Zoho Projects SDK Development Tasks"
	@echo "==================================="
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Installation targets
.PHONY: install
install: ## Install the package in development mode using uv
	$(UV) sync

.PHONY: install-dev
install-dev: ## Install development dependencies using uv
	$(UV) sync --dev

.PHONY: install-test
install-test: ## Install test dependencies only using uv
	$(UV) pip install pytest pytest-cov

# uv-based development targets
.PHONY: run-black
run-black: ## Run black using uv
	$(UV) run black $(SRC_DIR) $(TEST_DIR)

.PHONY: run-isort
run-isort: ## Run isort using uv
	$(UV) run isort $(SRC_DIR) $(TEST_DIR)

.PHONY: run-flake8
run-flake8: ## Run flake8 using uv
	$(UV) run flake8 $(SRC_DIR) $(TEST_DIR)

.PHONY: run-pylint
run-pylint: ## Run pylint using uv
	$(UV) run pylint $(SRC_DIR) $(TEST_DIR)

.PHONY: run-mypy
run-mypy: ## Run mypy using uv with proper configuration
	MYPYPATH=$(SRC_DIR) $(UV) run mypy -p $(PACKAGE)
	MYPYPATH=$(SRC_DIR) $(UV) run mypy $(TEST_DIR)

# Test targets
.PHONY: test
test: ## Run all tests using uv
	$(UV) run pytest $(TEST_DIR) -v

.PHONY: test-unit
test-unit: ## Run unit tests only using uv
	$(UV) run pytest $(TEST_DIR) -v -m "unit"

.PHONY: test-integration
test-integration: ## Run integration tests only using uv
	$(UV) run pytest $(TEST_DIR) -v -m "integration"

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests only using uv
	$(UV) run pytest $(TEST_DIR) -v -m "e2e"

.PHONY: test-quick
test-quick: ## Run quick tests (skip slow tests) using uv
	$(UV) run pytest $(TEST_DIR) -v -m "not slow"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report using uv
	$(UV) run pytest $(TEST_DIR) --cov=$(PACKAGE_DIR) --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=95 -v

.PHONY: test-coverage-html
test-coverage-html: ## Run tests with HTML coverage report using uv
	$(UV) run pytest $(TEST_DIR) --cov=$(PACKAGE_DIR) --cov-report=html -v
	@echo "HTML coverage report generated in htmlcov/index.html"

.PHONY: test-coverage-xml
test-coverage-xml: ## Run tests with XML coverage report using uv
	$(UV) run pytest $(TEST_DIR) --cov=$(PACKAGE_DIR) --cov-report=xml -v
	@echo "XML coverage report generated in coverage.xml"

.PHONY: html-coverage
html-coverage: ## Generate HTML coverage report using uv
	$(UV) run pytest $(TEST_DIR) --cov=$(PACKAGE_DIR) --cov-report=html
	@echo "HTML coverage report generated in htmlcov/index.html"

.PHONY: verify-coverage
verify-coverage: ## Verify 95%+ test coverage
	$(PYTHON) scripts/coverage_summary.py

# Linting and formatting targets
.PHONY: format
format: ## Format code with black and isort using uv
	$(UV) run black $(SRC_DIR) $(TEST_DIR)
	$(UV) run isort $(SRC_DIR) $(TEST_DIR)

.PHONY: lint
lint: ## Run all linters using uv and scripts
	$(UV) run python scripts/run_lint.py

.PHONY: lint-check
lint-check: ## Check code formatting and linting using uv
	$(UV) run black $(SRC_DIR) $(TEST_DIR) --check
	$(UV) run isort $(SRC_DIR) $(TEST_DIR) --check-only
	$(UV) run flake8 $(SRC_DIR) $(TEST_DIR)
	$(UV) run pylint $(SRC_DIR) $(TEST_DIR)
	MYPYPATH=$(SRC_DIR) $(UV) run mypy -p $(PACKAGE)
	MYPYPATH=$(SRC_DIR) $(UV) run mypy $(TEST_DIR) || true

.PHONY: check
check: ## Run all code quality checks (format, lint, test)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test

.PHONY: ci
ci: ## Run continuous integration checks using uv
	$(UV) sync --dev
	$(UV) run python scripts/run_lint.py
	$(UV) run pytest $(TEST_DIR) --cov=$(PACKAGE_DIR) --cov-report=term-missing --cov-report=xml --cov-fail-under=95 -v
	$(PYTHON) scripts/coverage_summary.py

# Clean targets
.PHONY: clean
clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: clean-test
clean-test: ## Clean test artifacts only
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf coverage.xml

# Documentation targets
.PHONY: docs
docs: ## Generate documentation using uv (placeholder)
	@echo "Documentation generation not yet implemented"

.PHONY: docs-serve
docs-serve: ## Serve documentation locally (placeholder)
	@echo "Local documentation server not yet implemented"

# Release targets
.PHONY: build
build: ## Build distribution packages using uv
	$(UV) run python -m build

.PHONY: publish-test
publish-test: build ## Publish to TestPyPI (includes build step)
	$(UV) run python -m twine upload --repository testpypi dist/*

.PHONY: publish
publish: ## Publish to PyPI
	$(UV) run python -m twine upload dist/*

# Development workflow targets
.PHONY: dev
dev: ## Run development workflow (format, lint, test) using uv
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test

.PHONY: pre-commit
pre-commit: ## Run pre-commit checks using uv
	$(MAKE) format
	$(MAKE) lint-check
	$(MAKE) test-quick