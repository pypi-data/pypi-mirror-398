.PHONY: install run dev test lint format clean help build publish sync

# Default target
help:
	@echo "Claude Agent Framework - Available Commands"
	@echo ""
	@echo "  Setup Commands (UV):"
	@echo "    make sync          Sync dependencies with uv"
	@echo "    make install       Install package in editable mode"
	@echo "    make dev           Install with all optional dependencies"
	@echo ""
	@echo "  Basic Commands:"
	@echo "    make run           Run interactive session (default: research architecture)"
	@echo "    make list-archs    List all available architectures"
	@echo ""
	@echo "  Run by Architecture:"
	@echo "    make run-research      Run Research architecture"
	@echo "    make run-pipeline      Run Pipeline architecture"
	@echo "    make run-critic        Run Critic-Actor architecture"
	@echo "    make run-specialist    Run Specialist Pool architecture"
	@echo "    make run-debate        Run Debate architecture"
	@echo "    make run-reflexion     Run Reflexion architecture"
	@echo "    make run-mapreduce     Run MapReduce architecture"
	@echo ""
	@echo "  Development Commands:"
	@echo "    make test          Run tests"
	@echo "    make test-cov      Run tests with coverage"
	@echo "    make lint          Lint code"
	@echo "    make format        Format code"
	@echo "    make clean         Clean temporary files"
	@echo "    make clean-logs    Clean logs and output files"
	@echo ""
	@echo "  Build & Publish Commands (UV):"
	@echo "    make build         Build wheel and source distributions"
	@echo "    make build-clean   Clean old builds and rebuild"
	@echo "    make publish-test  Publish to TestPyPI"
	@echo "    make publish-prod  Publish to PyPI (production)"
	@echo ""
	@echo "  Examples:"
	@echo "    make example-basic        Run basic usage example"
	@echo "    make example-custom       Run custom architecture example"
	@echo "    make example-programmatic Run programmatic usage example"
	@echo ""

# Install dependencies
sync:
	uv sync

install:
	uv sync
	uv pip install -e .

# Install all dependencies (including dev dependencies)
dev:
	uv sync --all-groups

# List all available architectures
list-archs:
	uv run python -m claude_agent_framework.cli --list

# Run interactive session (default: research architecture)
run:
	uv run python -m claude_agent_framework.cli --arch research -i

# Run by architecture
run-research:
 	# uv run python -m claude_agent_framework.cli --arch research -i
	claude-agent run --arch research -bt competitive_intelligence \
    -tv company_name="TechCorp" -tv industry="Cloud Computing"

run-pipeline:
	uv run python -m claude_agent_framework.cli --arch pipeline -i

run-critic:
	uv run python -m claude_agent_framework.cli --arch critic_actor -i

run-specialist:
	uv run python -m claude_agent_framework.cli --arch specialist_pool -i

run-debate:
	# uv run python -m claude_agent_framework.cli --arch debate -i
	claude-agent run --arch debate -bt tech_decision \
	-tv decision_topic="Database Selection" -q "PostgreSQL vs MongoDB?"

run-reflexion:
	uv run python -m claude_agent_framework.cli --arch reflexion -i

run-mapreduce:
	uv run python -m claude_agent_framework.cli --arch mapreduce -i

# Run single query
query:
	@read -p "Select architecture (research/pipeline/critic_actor/specialist_pool/debate/reflexion/mapreduce): " arch; \
	read -p "Enter query: " q; \
	uv run python -m claude_agent_framework.cli --arch "$$arch" -q "$$q"

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage report
test-cov:
	uv run pytest tests/ -v --cov=src/claude_agent_framework --cov-report=html

# Lint code
lint:
	uv run ruff check .
	uv run mypy src/claude_agent_framework

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Clean temporary files
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean logs and output files
clean-logs:
	rm -rf logs/*
	rm -rf files/research_notes/*
	rm -rf files/data/*
	rm -rf files/charts/*
	rm -rf files/reports/*

# Run examples
example-basic:
	uv run python examples/basic_usage.py

example-custom:
	uv run python examples/custom_agents.py

example-programmatic:
	uv run python examples/programmatic_usage.py

# Build and publish commands
.PHONY: build build-clean publish-test publish-prod

build:
	@echo "🔨 Building package with uv..."
	@uv build

build-clean:
	@echo "🧹 Cleaning old builds..."
	@rm -rf dist/ build/ *.egg-info
	@echo "🔨 Building package with uv..."
	@uv build

publish-test:
	@echo "📤 Publishing to TestPyPI..."
	@if [ -f ~/.pypirc ] && [ -z "$$UV_PUBLISH_PASSWORD" ]; then \
		echo "🔑 Reading credentials from ~/.pypirc..."; \
		PYPI_PASSWORD=$$(sed -n '/^\[testpypi\]/,/^\[/p' ~/.pypirc | grep "^password" | sed 's/password[[:space:]]*=[[:space:]]*//' | tr -d '\n\r'); \
		UV_PUBLISH_USERNAME=__token__ UV_PUBLISH_PASSWORD="$$PYPI_PASSWORD" uv publish --publish-url https://test.pypi.org/legacy/; \
	else \
		uv publish --publish-url https://test.pypi.org/legacy/; \
	fi

publish-prod:
	@echo "📤 Publishing to PyPI..."
	@if [ -f ~/.pypirc ] && [ -z "$$UV_PUBLISH_PASSWORD" ]; then \
		echo "🔑 Reading credentials from ~/.pypirc..."; \
		PYPI_PASSWORD=$$(sed -n '/^\[pypi\]/,/^\[/p' ~/.pypirc | grep "^password" | sed 's/password[[:space:]]*=[[:space:]]*//' | tr -d '\n\r'); \
		UV_PUBLISH_USERNAME=__token__ UV_PUBLISH_PASSWORD="$$PYPI_PASSWORD" uv publish; \
	else \
		uv publish; \
	fi
