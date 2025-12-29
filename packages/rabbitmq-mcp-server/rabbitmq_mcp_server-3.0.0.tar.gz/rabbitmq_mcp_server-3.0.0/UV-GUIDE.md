# UV Quick Reference for This Project

This project uses **uv** - a fast Python package manager written in Rust.

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Homebrew
brew install uv

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Common Commands

### Initial Setup
```bash
# Sync all dependencies (including dev/extras)
uv sync --all-extras

# Sync only production dependencies
uv sync
```

### Running Commands
```bash
# Run a command in the virtual environment
uv run <command>

# Examples:
uv run pytest
uv run black .
uv run ruff check
uv run mypy src/
uv run semantic-release version --print
```

### Using uvx (No Installation)
```bash
# Run a tool without adding it to the project
uvx ruff check .
uvx black .
uvx semantic-release version --print
```

### Adding Dependencies
```bash
# Add a production dependency
uv add requests

# Add a dev dependency
uv add --dev pytest

# Add an optional dependency
uv add --optional dev pytest
```

### Removing Dependencies
```bash
uv remove package-name
```

### Updating Dependencies
```bash
# Update all dependencies
uv sync --upgrade

# Update a specific package
uv sync --upgrade-package package-name
```

### Virtual Environment
```bash
# uv automatically creates .venv when you run uv sync
# To activate manually:
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# To deactivate:
deactivate
```

### Python Version Management
```bash
# Use specific Python version
uv python install 3.12

# List available Python versions
uv python list
```

## Project-Specific Commands

### Development
```bash
# Install all dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/mcp_server --cov-report=html

# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy src/
```

### Semantic Release
```bash
# Check what version would be released
uv run semantic-release version --print

# Dry run (see what would happen)
uv run semantic-release version --noop

# Create a new version
uv run semantic-release version

# Publish release
uv run semantic-release publish
```

### Schema Generation (when scripts are available)
```bash
uv run generate-schemas
uv run generate-embeddings
uv run validate-openapi
```

## Lock File

- `uv.lock` - Contains exact versions of all dependencies
- **Commit this file** to ensure reproducible builds
- Updated automatically when you run `uv sync`, `uv add`, or `uv remove`

## Benefits Over pip/Poetry

| Feature | uv | pip | Poetry |
|---------|-----|-----|--------|
| Speed | ⚡ 10-100x faster | baseline | ~2x faster |
| Lock file | ✅ automatic | ❌ no | ✅ yes |
| PEP 621 | ✅ native | ⚠️ partial | ❌ custom |
| Install time (cold) | ~2s | ~30s | ~20s |
| Resolver | ✅ advanced | ⚠️ basic | ✅ advanced |
| Virtual envs | ✅ automatic | ❌ manual | ✅ automatic |

## Troubleshooting

### Cache Issues
```bash
# Clear cache
uv cache clean
```

### Dependency Conflicts
```bash
# See full dependency tree
uv tree

# Show why a package is installed
uv tree --package package-name
```

### Reinstall Everything
```bash
# Remove virtual environment and reinstall
rm -rf .venv
uv sync --all-extras
```

## Migration from Poetry

Already done! ✅ The project has been converted:

- ❌ `poetry.lock` → ✅ `uv.lock`
- ❌ `[tool.poetry]` → ✅ `[project]` (PEP 621)
- ❌ `poetry-core` → ✅ `hatchling`
- ❌ `poetry install` → ✅ `uv sync`
- ❌ `poetry run` → ✅ `uv run`
- ❌ `poetry add` → ✅ `uv add`

## CI/CD Integration

GitHub Actions already configured with:
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v4
  
- name: Install dependencies
  run: uv sync --all-extras
  
- name: Run tests
  run: uv run pytest
```

## Learn More

- Official docs: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- PEP 621: https://peps.python.org/pep-0621/
