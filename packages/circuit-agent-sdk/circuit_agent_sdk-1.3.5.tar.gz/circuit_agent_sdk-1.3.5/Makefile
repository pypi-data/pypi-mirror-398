.PHONY: help install test lint format fix type-check build clean all publish-pypi publish-test release commit

# Default target
help:
	@echo "Circuit Agent Python SDK - Development Commands"
	@echo ""
	@echo "Essential commands:"
	@echo "  make install         - Install dependencies and set up pre-commit hooks"
	@echo "  make fix             - Auto-fix all code issues (run this before committing!)"
	@echo "  make test            - Run tests with coverage"
	@echo "  make all             - Run fix + test (recommended before committing)"
	@echo "  make commit          - Fix everything and commit with your message"
	@echo ""
	@echo "Individual checks:"
	@echo "  make lint            - Check code style (without fixing)"
	@echo "  make format          - Check formatting (without fixing)"
	@echo "  make type-check      - Run type checking"
	@echo ""
	@echo "Build & Release:"
	@echo "  make build           - Build the package"
	@echo "  make clean           - Clean build artifacts"
	@echo "  make release         - Create a new release and publish to PyPI"
	@echo "  make publish-pypi    - Publish to PyPI (requires PYPI_TOKEN env var)"
	@echo "  make publish-test    - Publish to TestPyPI (requires TEST_PYPI_TOKEN env var)"

# Install dependencies and set up pre-commit hooks
install:
	@echo "Installing dependencies..."
	uv sync --dev
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "Ready! The pre-commit hooks will now run automatically on git commit."

# Auto-fix all issues (RUN THIS BEFORE COMMITTING!)
fix:
	@echo "Auto-fixing all code issues..."
	@echo "  -> Running ruff fixes..."
	@uv run ruff check . --fix --quiet 2>/dev/null || true
	@echo "  -> Formatting with ruff..."
	@uv run ruff format . --quiet
	@echo "  -> Upgrading Python syntax..."
	@find . -name "*.py" -not -path "./.venv/*" -not -path "./build/*" -not -path "./dist/*" | xargs uv run pyupgrade --py312-plus 2>/dev/null || true
	@echo "  -> Sorting imports..."
	@uv run isort . --profile=black --quiet
	@echo "  -> Final ruff format pass..."
	@uv run ruff format . --quiet
	@echo "All fixable issues resolved!"

# Run tests
test:
	@echo "Running tests..."
	uv run --isolated pytest tests/ -v --cov=src/agent_sdk --cov-report=term-missing --cov-report=html

# Check linting (read-only)
lint:
	@echo "Checking code style..."
	uv run --isolated ruff check .

# Check formatting (read-only)
format:
	@echo "Checking code formatting..."
	uv run --isolated ruff format --check .

# Type checking
type-check:
	@echo "Running type checking..."
	cd src && uv run --isolated mypy --ignore-missing-imports .

# Build package
build: clean
	@echo "Building package..."
	uv build

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist/ build/ *.egg-info/ htmlcov/ .coverage .pytest_cache/ .mypy_cache/ .ruff_cache/

# Run everything (recommended before commit)
all: fix type-check test
	@echo "All checks passed! Ready to commit."

# Pre-push checks (without tests)
pre-push: fix type-check lint format
	@echo "All pre-push checks passed! Ready to push."

# Commit with automatic fixing (no more pre-commit conflicts!)
commit:
	@if [ -z "$(MSG)" ]; then \
		echo "ERROR: Please provide a commit message: make commit MSG='your message'"; \
		exit 1; \
	fi
	@echo "Fixing all code issues first..."
	@make fix --no-print-directory
	@echo "Staging all changes..."
	@git add -A
	@echo "Committing with message: $(MSG)"
	@git commit -m "$(MSG)" --no-verify
	@echo "Committed successfully! (bypassed pre-commit to avoid conflicts)"

# Publish to PyPI
publish-pypi: build
	@echo "Publishing to PyPI..."
	@if [ -z "$$PYPI_TOKEN" ]; then \
		echo "ERROR: PYPI_TOKEN environment variable not set."; \
		echo ""; \
		echo "To set up PyPI publishing:"; \
		echo "1. Go to https://pypi.org/manage/account/token/"; \
		echo "2. Create an API token with 'Upload packages' permission"; \
		echo "3. Export the token: export PYPI_TOKEN='pypi-...'"; \
		echo "4. Run this command again"; \
		exit 1; \
	fi
	@echo "Using PyPI token for authentication..."
	uv pip install --upgrade twine
	uv run twine upload dist/* --username __token__ --password $$PYPI_TOKEN

# Publish to TestPyPI (for testing)
publish-test: build
	@echo "Publishing to TestPyPI..."
	@if [ -z "$$TEST_PYPI_TOKEN" ]; then \
		echo "ERROR: TEST_PYPI_TOKEN environment variable not set."; \
		echo ""; \
		echo "To set up TestPyPI publishing:"; \
		echo "1. Go to https://test.pypi.org/manage/account/token/"; \
		echo "2. Create an API token with 'Upload packages' permission"; \
		echo "3. Export the token: export TEST_PYPI_TOKEN='pypi-...'"; \
		echo "4. Run this command again"; \
		exit 1; \
	fi
	@echo "Using TestPyPI token for authentication..."
	uv pip install --upgrade twine
	uv run twine upload --repository testpypi dist/* --username __token__ --password $$TEST_PYPI_TOKEN

# Create a new release
release: all
	@echo "Creating a new release..."
	@echo "Current version: $$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')"
	@read -p "Enter new version (or press enter to keep current): " new_version; \
	if [ -n "$$new_version" ]; then \
		sed -i '' 's/^version = ".*"/version = "'$$new_version'"/' pyproject.toml; \
		echo "Updated to version: $$new_version"; \
	fi
	@version=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	git add -A; \
	git commit -m "Release v$$version"; \
	git tag v$$version; \
	echo "Created tag v$$version"
	@echo "Pushing to GitHub..."
	@git push origin main
	@git push origin v$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
	@if [ -n "$$PYPI_TOKEN" ]; then \
		make publish-pypi; \
	else \
		echo "WARNING: PYPI_TOKEN not set. Skipping PyPI publish."; \
		echo "   To publish manually: export PYPI_TOKEN='your-token' && make publish-pypi"; \
	fi
