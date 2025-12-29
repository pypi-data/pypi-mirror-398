# Development Environment

## Prerequisites

**Required:**
- Python 3.12 or higher
- uv package manager (0.1.0+)
- Git
- RabbitMQ 3.11+ (for integration tests)
  - Docker recommended: `docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management`

**Optional:**
- Docker Desktop (for testcontainers)
- VS Code with Python extension
- pre-commit (installed via uv)

## Setup Commands

```bash
# 1. Clone repository
git clone https://github.com/guercheLE/rabbitmq-mcp.git
cd rabbitmq-mcp

# 2. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env  # Add uv to PATH

# 3. Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# 4. Install dependencies (including dev dependencies)
uv sync --all-extras

# 5. Install pre-commit hooks
uv run pre-commit install

# 6. Generate build-time artifacts
uv run python scripts/generate_schemas.py
uv run python scripts/generate_embeddings.py

# 7. Copy example config
cp config/config.toml.example config/config.toml
cp .env.example .env

# 8. Edit .env with your RabbitMQ credentials
nano .env  # or your preferred editor

# 9. Run tests to verify setup
uv run pytest

# 10. Start development server (stdio mode)
uv run python -m rabbitmq_mcp_server

# Or HTTP mode for browser testing
uv run python -m rabbitmq_mcp_server --transport http --port 8000
```

## Development Workflow

```bash
# Run tests
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit tests only
uv run pytest tests/integration/ # Integration tests
uv run pytest -v -s              # Verbose with output

# Run tests with coverage
uv run pytest --cov=rabbitmq_mcp_server --cov-report=html
open htmlcov/index.html          # View coverage report

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/ tests/

# Formatting
uv run black src/ tests/
uv run isort src/ tests/

# Run all pre-commit checks
uv run pre-commit run --all-files

# Regenerate schemas after OpenAPI changes
uv run python scripts/generate_schemas.py
uv run python scripts/generate_embeddings.py

# Validate OpenAPI spec
uv run python scripts/validate_openapi.py

# Start MCP Inspector for testing
uv run mcp dev src/rabbitmq_mcp_server/__main__.py
```

## IDE Configuration

**VS Code (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```
