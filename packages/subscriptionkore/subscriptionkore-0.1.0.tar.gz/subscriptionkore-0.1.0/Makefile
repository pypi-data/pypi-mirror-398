.PHONY: help install test lint format run-fastapi-example run-multi-provider-example docs docs-serve build publish publish-test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .[dev]

test: ## Run tests
	pytest

lint: ## Run linter
	ruff check src/

format: ## Format code
	ruff format src/

run-fastapi-example: ## Run the FastAPI example
	python examples/fastapi_app.py

run-multi-provider-example: ## Run the multi-provider example
	python examples/multi_provider_app.py

docs: ## Build documentation
	pip install -e .[docs]
	sphinx-build -b html docs docs/_build/html

docs-serve: ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8000

build: ## Build distribution packages
	pip install build
	python -m build

publish-test: build ## Publish to TestPyPI
	pip install twine
	python -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	pip install twine
	python -m twine upload dist/*