# SPDX-FileCopyrightText: 2024-present 
# SPDX-License-Identifier: MIT

SHELL := /bin/bash
MAKEFLAGS += --silent
.DEFAULT_GOAL := help

# Respect NO_COLOR: https://no-color.org
NO_COLOR ?=
export PYTHONPATH := $(PYTHONPATH):.

ifneq (,$(NO_COLOR))
	_BLUE :=
	_GREEN :=
	_RED :=
	_YELLOW :=
	_CYAN :=
	_RESET :=
else
	_BLUE := \033[34m
	_GREEN := \033[32m
	_RED := \033[31m
	_YELLOW := \033[33m
	_CYAN := \033[36m
	_RESET := \033[0m
endif

_SECTION := $(_CYAN)
_OPTION := $(_BLUE)

#------------------------------------------------------------------------------
# Logging & Status Variables
#------------------------------------------------------------------------------
_TIME		= `date +%H:%M:%S`

TRY = printf "$(_BLUE)🔄 %-60s$(_RESET)"
RUN_OK = printf " $(_GREEN)✅$(_RESET)\n"
RUN_FAIL = printf " $(_RED)❌$(_RESET)\n" && false

STATUS_OK := printf "$(_GREEN)✅ Done$(_RESET)\n"
FAIL := printf "$(_RED)❌$(_RESET)\n" && false
INFO = echo -e "$(_TIME) $(_BLUE)[INFO]$(_RESET)"

#------------------------------------------------------------------------------
# Configuration & Variables
#------------------------------------------------------------------------------

UV := $(shell command -v uv 2>/dev/null)
ifeq ($(UV),)
$(error uv not found. Please install uv (https://docs.astral.sh/uv/))
endif

VENV := .venv
PYTHON := $(VENV)/bin/python3

# Create venv if needed
$(PYTHON):
	$(INFO) "Setting up virtual environment"
	$(UV) sync --all-groups

#------------------------------------------------------------------------------
# Dev Targets
#------------------------------------------------------------------------------

.PHONY: sync fmt lint typecheck test build publish clean distclean help

sync: $(PYTHON) ## Sync dependencies
	$(UV) sync --all-groups

fmt: $(PYTHON) ## Format code
	$(TRY) "Formatting code"
	$(UV) run ruff format src test
	$(RUN_OK)

lint: $(PYTHON) ## Lint code with fixes
	$(TRY) "Linting code"
	$(UV) run ruff check --fix src test
	$(RUN_OK)

typecheck: $(PYTHON) ## Type check code
	$(TRY) "Type checking"
	$(UV) run zuban check
	$(RUN_OK)

test: $(PYTHON) ## Run tests
	$(TRY) "Running tests"
	$(UV) run pytest test
	$(RUN_OK)

test.coverage: $(PYTHON) ## Run tests with coverage
	$(UV) run pytest --cov=src/dross --cov-report=html test

build: $(PYTHON) ## Build package
	$(TRY) "Building package"
	$(UV) build --out-dir dist
	$(RUN_OK)

publish: build ## Publish package to PyPI
	$(INFO) "Publishing package to PyPI"
	@$(UV) publish

qa: fmt lint typecheck test build ## Run all quality checks

clean: ## Clean cache and temp files
	rm -rf .pytest_cache __pycache__ .ruff_cache .coverage htmlcov

distclean: clean ## Full cleanup including venv
	rm -rf .venv dist build *.egg-info

help: ## Show this help message
	@echo "$(_SECTION)Dross - ML Pipeline Framework$(_RESET)"
	@echo ""
	@echo "$(_SECTION)Development Targets:$(_RESET)"
	@grep -E '^[a-zA-Z_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(_OPTION)%-20s$(_RESET) %s\n", $$1, $$2}'
