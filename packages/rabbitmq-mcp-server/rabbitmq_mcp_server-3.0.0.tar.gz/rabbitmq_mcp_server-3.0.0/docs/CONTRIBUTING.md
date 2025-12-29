# Contributing Guide

Welcome! This guide will help you contribute to the RabbitMQ MCP Server project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [OpenAPI Specifications](#openapi-specifications)
- [Vector Embeddings](#vector-embeddings)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)
- [Release Process](#release-process)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.12+**: Required for development
- **uv**: Fast Python package installer
- **Docker**: For running integration tests with RabbitMQ
- **Git**: Version control

### Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/guercheLE/rabbitmq-mcp-server.git
cd rabbitmq-mcp-server

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv pip install -e ".[dev]"

# 4. Install pre-commit hooks
pre-commit install

# 5. Run tests to verify setup
pytest
```

---

## Development Environment Setup

### Step-by-Step Setup

#### 1. Install Python 3.12+

**macOS (using Homebrew)**:
```bash
brew install python@3.12
```

**Linux (using apt)**:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

**Windows**:
- Download from [python.org](https://www.python.org/downloads/)

---

#### 2. Install uv

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:
```bash
uv --version
```

---

#### 3. Clone and Install

```bash
# Clone repository
git clone https://github.com/guercheLE/rabbitmq-mcp-server.git
cd rabbitmq-mcp-server

# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows

# Install in editable mode with dev dependencies
uv pip install -e ".[dev,vector]"
```

---

#### 4. Install Docker (for integration tests)

**macOS**:
- Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

**Linux**:
```bash
sudo apt install docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**Windows**:
- Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

Verify installation:
```bash
docker --version
docker run hello-world
```

---

#### 5. Setup Pre-commit Hooks

```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

---

## Project Structure

```
rabbitmq-mcp-server/
├── src/
│   ├── mcp_server/           # Main source code
│   │   ├── tools/            # MCP tools (search-ids, get-id, call-id)
│   │   ├── cli/              # CLI commands
│   │   ├── config/           # Configuration management
│   │   └── utils/            # Shared utilities
├── tests/
│   ├── unit/                 # Unit tests (fast, isolated)
│   ├── integration/          # Integration tests (with RabbitMQ)
│   └── contract/             # Contract tests (OpenAPI validation)
├── specs/
│   └── 003-essential-topology-operations/
│       ├── spec.md           # Feature specification
│       ├── plan.md           # Implementation plan
│       ├── tasks.md          # Task breakdown
│       ├── contracts/        # OpenAPI specifications
│       └── research.md       # Technical research
├── docs/                     # Documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── EXAMPLES.md
│   └── CONTRIBUTING.md (this file)
├── scripts/                  # Build and utility scripts
│   ├── generate_schemas.py   # Generate Pydantic from OpenAPI
│   ├── generate_embeddings.py # Generate vector DB indices
│   └── validate_openapi.py   # Validate OpenAPI specs
├── data/vectors/             # Pre-built vector database
├── config/                   # Configuration examples
├── pyproject.toml            # Project metadata and dependencies
├── pytest.ini                # Pytest configuration
└── .pre-commit-config.yaml   # Pre-commit hooks config
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Always branch from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Or bug fix branch
git checkout -b fix/issue-number-description
```

### 2. Make Changes

Follow the **TDD (Test-Driven Development)** approach:

```bash
# 1. Write tests first
vim tests/unit/test_your_feature.py

# 2. Run tests (should fail)
pytest tests/unit/test_your_feature.py

# 3. Implement feature
vim src/mcp_server/your_feature.py

# 4. Run tests (should pass)
pytest tests/unit/test_your_feature.py

# 5. Refactor if needed
```

### 3. Run Full Test Suite

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add new queue validation feature"

# Pre-commit hooks will run automatically
```

**Conventional Commit Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

**Examples**:
```bash
git commit -m "feat(queue): add priority queue support"
git commit -m "fix(validation): handle edge case in name validation"
git commit -m "docs: update API reference with new endpoints"
git commit -m "test(integration): add RabbitMQ container tests"
```

### 5. Push and Create Pull Request

```bash
# Push branch to GitHub
git push origin feature/your-feature-name

# Create pull request on GitHub
# Go to: https://github.com/guercheLE/rabbitmq-mcp-server/pulls
```

---

## Code Style

### Linting and Formatting

We use the following tools:

- **black**: Code formatting (line-length: 100)
- **ruff**: Fast linting
- **mypy**: Static type checking

### Configuration

All tools are configured in `pyproject.toml`:

```toml
[tool.black]
line-length = 100
target-version = ['py312']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
```

### Running Linters

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/

# Or use pre-commit to run all checks
pre-commit run --all-files
```

### Code Style Guidelines

#### 1. Type Hints

**Always use type hints**:

```python
# ✓ Good
def create_queue(name: str, durable: bool = True) -> Queue:
    ...

# ✗ Bad
def create_queue(name, durable=True):
    ...
```

#### 2. Docstrings

**Use Google-style docstrings**:

```python
def validate_name(name: str) -> None:
    """Validate resource name against RabbitMQ naming rules.

    Args:
        name: The resource name to validate.

    Raises:
        ValidationError: If name contains invalid characters or is too long.

    Example:
        >>> validate_name("my-queue")
        >>> validate_name("invalid queue!")  # Raises ValidationError
    """
    ...
```

#### 3. Error Handling

**Use standardized error classes**:

```python
# ✓ Good
if not re.match(r"^[a-zA-Z0-9._-]{1,255}$", name):
    raise ValidationError(
        code="INVALID_NAME",
        field="queue_name",
        expected="alphanumeric, dots, dashes, underscores only",
        actual=name,
        action="Remove special characters"
    )

# ✗ Bad
if not re.match(r"^[a-zA-Z0-9._-]{1,255}$", name):
    raise ValueError("Invalid name")
```

#### 4. Logging

**Use structured logging with context**:

```python
# ✓ Good
logger.info(
    "queue_created",
    vhost=vhost,
    queue_name=name,
    durable=options.durable,
    correlation_id=correlation_id
)

# ✗ Bad
logger.info(f"Created queue {name}")
```

---

## Testing

### Test Structure

```
tests/
├── unit/                # Fast, isolated, mocked tests
│   ├── test_validation.py
│   ├── test_operations.py
│   └── test_mcp_tools.py
├── integration/         # Real RabbitMQ tests
│   ├── test_queue_operations.py
│   ├── test_exchange_operations.py
│   └── test_binding_operations.py
└── contract/            # OpenAPI compliance tests
    └── test_openapi_compliance.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_validation.py

# Run specific test function
pytest tests/unit/test_validation.py::test_validate_name_accepts_valid

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/

# Run only integration tests (requires Docker)
pytest tests/integration/

# Run with verbose output
pytest -v

# Run with stdout/logging visible
pytest -s
```

### Writing Unit Tests

**Example unit test**:

```python
import pytest
from utils.validation import validate_name
from utils.errors import ValidationError


def test_validate_name_accepts_valid_names():
    """Valid names should pass without raising exceptions."""
    validate_name("my-queue")
    validate_name("queue_123")
    validate_name("queue.name")


def test_validate_name_rejects_special_chars():
    """Names with special characters should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        validate_name("my queue!")
    
    assert exc_info.value.code == "INVALID_NAME"
    assert "Remove special characters" in exc_info.value.action


def test_validate_name_rejects_too_long():
    """Names over 255 characters should raise ValidationError."""
    long_name = "a" * 256
    with pytest.raises(ValidationError) as exc_info:
        validate_name(long_name)
    
    assert exc_info.value.code == "INVALID_NAME"
    assert "255" in exc_info.value.expected
```

### Writing Integration Tests

**Example integration test with testcontainers**:

```python
import pytest
from testcontainers.rabbitmq import RabbitMQContainer
from tools.operations.queues import create_queue, list_queues, delete_queue


@pytest.fixture
def rabbitmq_container():
    """Provide a RabbitMQ container for testing."""
    with RabbitMQContainer() as container:
        yield container


def test_create_and_list_queue(rabbitmq_container):
    """Integration test: create queue and verify it appears in list."""
    # Setup
    host = rabbitmq_container.get_container_host_ip()
    port = rabbitmq_container.get_exposed_port(15672)
    
    # Create queue
    result = create_queue(
        host=host,
        port=port,
        user="guest",
        password="guest",
        vhost="/",
        name="test-queue",
        durable=True
    )
    
    assert result.name == "test-queue"
    
    # List queues and verify
    queues = list_queues(host=host, port=port, user="guest", password="guest", vhost="/")
    queue_names = [q.name for q in queues.items]
    
    assert "test-queue" in queue_names
    
    # Cleanup
    delete_queue(host=host, port=port, user="guest", password="guest", vhost="/", name="test-queue")
```

### Test Coverage Requirements

- **Minimum coverage**: 80% across all source files
- **Critical paths**: 95%+ coverage for validation, error handling, safety checks
- **New features**: 100% coverage required

Check coverage:

```bash
pytest --cov=src --cov-report=term-missing

# View HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## OpenAPI Specifications

### Location

All OpenAPI specifications are in:

```
specs/003-essential-topology-operations/contracts/
├── queue-operations.yaml
├── exchange-operations.yaml
└── binding-operations.yaml
```

### Editing OpenAPI Specs

When adding or modifying operations:

1. **Edit the YAML file**:
```yaml
paths:
  /queues:
    get:
      operationId: queues.list
      summary: List all queues
      description: |
        Detailed description of the operation.
      parameters:
        - name: vhost
          in: query
          schema:
            type: string
```

2. **Validate the spec**:
```bash
python scripts/validate_openapi.py specs/003-essential-topology-operations/contracts/queue-operations.yaml
```

3. **Regenerate Pydantic schemas**:
```bash
python scripts/generate_schemas.py
```

4. **Regenerate vector embeddings**:
```bash
python scripts/generate_embeddings.py
```

5. **Commit all changes** (spec + generated files):
```bash
git add specs/003-essential-topology-operations/contracts/
git add src/schemas/
git add data/vectors/
git commit -m "feat(api): add new queue operation"
```

### OpenAPI Best Practices

- **operationId**: Use format `{resource}.{action}` (e.g., `queues.list`, `exchanges.create`)
- **Summary**: One-line description (< 80 chars)
- **Description**: Detailed explanation with examples
- **Parameters**: Include all required and optional parameters
- **Responses**: Define success and error responses
- **Schemas**: Reuse components for consistency

---

## Vector Embeddings

### Generating Embeddings

When OpenAPI specs change, regenerate embeddings:

```bash
# Generate embeddings for semantic search
python scripts/generate_embeddings.py

# This creates/updates: data/vectors/rabbitmq.db
```

### Testing Semantic Search

```bash
# Test search functionality
pytest tests/unit/test_search_ids.py -v

# Manual test
python -c "
from tools.search_ids import search_operations
results = search_operations('list queues')
print(results)
"
```

### Embedding Model

We use **all-MiniLM-L6-v2** from sentence-transformers:

- **Size**: 90MB
- **Embedding dimension**: 384
- **Performance**: < 10ms per text
- **Quality**: Good semantic understanding

---

## Documentation

### Documentation Files

All documentation is in `docs/`:

- `API.md`: Complete API reference
- `ARCHITECTURE.md`: System design and architecture
- `EXAMPLES.md`: Usage examples and use cases
- `CONTRIBUTING.md`: This file

### Documentation Guidelines

- **Language**: All documentation in English
- **Format**: Markdown
- **Style**: Clear, concise, with examples
- **Code blocks**: Include language specifiers
- **Links**: Use relative links for internal docs

### Building Documentation

Documentation is plain Markdown (no build step required).

Preview locally:

```bash
# Using grip (GitHub-flavored markdown viewer)
pip install grip
grip docs/API.md

# Opens browser at http://localhost:6419
```

---

## Pull Request Process

### 1. Before Creating PR

**Checklist**:

- [ ] All tests pass: `pytest`
- [ ] Code coverage ≥ 80%: `pytest --cov=src`
- [ ] Linting passes: `ruff check src/`
- [ ] Type checking passes: `mypy src/`
- [ ] Documentation updated (if applicable)
- [ ] OpenAPI specs updated (if adding/changing operations)
- [ ] Vector embeddings regenerated (if OpenAPI changed)
- [ ] Commit messages follow conventional commits format

### 2. Creating PR

**Title format**:
```
<type>(<scope>): <subject>
```

**Example titles**:
```
feat(queue): add priority queue support
fix(validation): handle edge case in wildcard patterns
docs(api): update binding examples
```

**Description template**:

```markdown
## Description
Brief description of the changes.

## Related Issues
Closes #123
Fixes #456

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Coverage remains ≥ 80%
```

### 3. PR Review Process

- **Automated checks**: CI/CD runs tests, linting, type checking
- **Code review**: At least one maintainer approval required
- **Changes requested**: Address feedback and push updates
- **Approval**: Once approved, PR can be merged

### 4. Merging

- **Squash merge**: Preferred for keeping clean history
- **Merge commit**: For significant features with multiple logical commits
- **Delete branch**: After merging

---

## Code Review Guidelines

### As a Reviewer

**Focus areas**:

1. **Correctness**: Does the code do what it's supposed to?
2. **Tests**: Are there sufficient tests? Do they cover edge cases?
3. **Style**: Does the code follow project conventions?
4. **Performance**: Are there obvious performance issues?
5. **Security**: Are there security concerns?
6. **Documentation**: Is the code well-documented?

**Review tips**:

- Be respectful and constructive
- Explain why, not just what
- Approve minor issues, request changes for major issues
- Ask questions if unclear
- Appreciate good work

**Example review comments**:

```markdown
✓ Good: "Great test coverage! Consider adding an edge case for empty strings."

✗ Bad: "This is wrong."

✓ Good: "This could be more efficient using a set instead of a list for membership checks."

✗ Bad: "Why did you do it this way?"
```

### As a PR Author

**Responding to feedback**:

- Thank reviewers for their time
- Address all comments (fix or explain)
- Ask for clarification if needed
- Mark conversations as resolved when addressed
- Request re-review after making changes

---

## Release Process

Releases are automated using **semantic-release**.

### Versioning

We follow **Semantic Versioning** (SemVer):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward-compatible
- **PATCH** (0.0.1): Bug fixes, backward-compatible

### Triggering a Release

Releases happen automatically when commits are merged to `main`:

1. **Commit types trigger releases**:
   - `feat:` → Minor version bump
   - `fix:` → Patch version bump
   - `BREAKING CHANGE:` → Major version bump

2. **Semantic-release**:
   - Analyzes commit history
   - Determines version bump
   - Generates changelog
   - Creates GitHub release
   - Publishes to PyPI (if configured)

### Manual Release

If needed, trigger manually:

```bash
# Generate changelog
semantic-release changelog

# Create release (dry-run)
semantic-release --dry-run

# Create release (for real)
semantic-release publish
```

---

## Additional Resources

- **GitHub Repository**: https://github.com/guercheLE/rabbitmq-mcp-server
- **Issue Tracker**: https://github.com/guercheLE/rabbitmq-mcp-server/issues
- **API Reference**: `docs/API.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Examples**: `docs/EXAMPLES.md`

---

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and discussions
- **Email**: [maintainer email] (for security issues)

---

## License

By contributing, you agree that your contributions will be licensed under the **LGPL v3.0** license.

All source files must include the license header:

```python
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2025 RabbitMQ MCP Server Contributors
```

---

**Thank you for contributing to RabbitMQ MCP Server!** 🎉

*Last Updated: October 2025*
