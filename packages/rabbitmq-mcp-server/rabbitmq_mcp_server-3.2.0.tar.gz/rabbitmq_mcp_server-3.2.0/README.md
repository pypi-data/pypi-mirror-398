# RabbitMQ MCP Server

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io/)
[![Code Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)](htmlcov/index.html)

**Production-ready MCP server for RabbitMQ** with semantic operation discovery and built-in CLI. Manage queues, exchanges, and bindings through natural language or command-line interface.

## ✨ Features

- 🔍 **Semantic Discovery**: Find operations using natural language queries
- 🛠️ **Three MCP Tools**: `search-ids`, `get-id`, `call-id` pattern for unlimited operations
- 📋 **Essential Operations**: List, create, and delete queues, exchanges, and bindings
- 🔐 **Safety First**: Built-in validations prevent data loss (queue message checks, binding validation)
- 📊 **Client-Side Pagination**: Handle 1000+ resources efficiently
- 📝 **Structured Logging**: Enterprise-grade audit logs with correlation IDs
- 🚀 **High Performance**: < 100ms semantic search, < 2s list operations, < 1s CRUD operations
- 🧪 **Well Tested**: 80%+ code coverage with unit, integration, and contract tests
- 📖 **OpenAPI-Driven**: All operations defined in OpenAPI 3.0.3 specification

## 🚀 Quick Start

### Using uvx (Recommended)

No installation needed! Run directly:

```bash
# List all queues
uvx rabbitmq-mcp-server queue list \
  --host localhost \
  --user guest \
  --password guest

# Create a durable queue
uvx rabbitmq-mcp-server queue create \
  --name orders-queue \
  --durable

# Create a topic exchange
uvx rabbitmq-mcp-server exchange create \
  --name order-events \
  --type topic \
  --durable

# Create a binding with wildcards
uvx rabbitmq-mcp-server binding create \
  --exchange order-events \
  --queue orders-queue \
  --routing-key "orders.*.created"
```

### Using pip

```bash
pip install rabbitmq-mcp-server

rabbitmq-mcp-server queue list --help
```

### Using uv (Development)

```bash
git clone https://github.com/guercheLE/rabbitmq-mcp-server.git
cd rabbitmq-mcp-server
uv pip install -e ".[dev]"

rabbitmq-mcp-server queue list
```

## 📚 Documentation

- **[API Reference](docs/API.md)**: Complete operation documentation
- **[Architecture](docs/ARCHITECTURE.md)**: System design and technical decisions
- **[Examples](docs/EXAMPLES.md)**: Practical use cases and integration examples
- **[Contributing](docs/CONTRIBUTING.md)**: How to contribute to the project

## 🎯 Use Cases

### Monitoring Queue Depths

```bash
# List queues with message counts
uvx rabbitmq-mcp-server queue list --verbose --format json | \
  jq '.items[] | select(.messages > 0) | {name, messages, consumers}'
```

### Event-Driven Architecture Setup

```bash
# Create topic exchange for order events
uvx rabbitmq-mcp-server exchange create --name order-events --type topic --durable

# Create queues for different services
uvx rabbitmq-mcp-server queue create --name inventory-service --durable
uvx rabbitmq-mcp-server queue create --name shipping-service --durable

# Bind with routing patterns
uvx rabbitmq-mcp-server binding create \
  --exchange order-events \
  --queue inventory-service \
  --routing-key "orders.*.created"

uvx rabbitmq-mcp-server binding create \
  --exchange order-events \
  --queue shipping-service \
  --routing-key "orders.*.fulfilled"
```

### Dead Letter Queue Setup

```bash
# Create DLX and DLQ
uvx rabbitmq-mcp-server exchange create --name dlx --type direct --durable
uvx rabbitmq-mcp-server queue create --name dlq --durable
uvx rabbitmq-mcp-server binding create --exchange dlx --queue dlq --routing-key failed

# Create main queue with DLX
uvx rabbitmq-mcp-server queue create \
  --name orders-queue \
  --durable \
  --arguments '{
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "failed",
    "x-message-ttl": 300000
  }'
```

## 🏗️ Architecture

RabbitMQ MCP Server follows an **OpenAPI-driven architecture** with semantic discovery:

```
┌─────────────────────────────────────────────────────────┐
│                   MCP Tools (3 Public)                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │ search-ids │  │   get-id   │  │    call-id     │   │
│  │  (< 100ms) │  │  (schema)  │  │  (execute)     │   │
│  └────────────┘  └────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              OpenAPI Operation Registry                  │
│         (Generated from OpenAPI 3.0.3 Spec)             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            Operation Executors (Queues,                  │
│          Exchanges, Bindings) + Validators               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│           RabbitMQ Management API (HTTP)                 │
└─────────────────────────────────────────────────────────┘
```

**Key Design Principles**:

1. **Three-Tool Pattern**: Semantic discovery supports unlimited operations without tool explosion
2. **OpenAPI as Source of Truth**: All operations defined in OpenAPI specs, code generated
3. **Safety by Design**: Built-in validations prevent data loss (queue messages, bindings)
4. **Performance-First**: Mandatory pagination, connection pooling, 60s vhost cache
5. **Enterprise Logging**: Structured JSON logs with correlation IDs, credential sanitization

See [Architecture Documentation](docs/ARCHITECTURE.md) for details.

## 🔧 Requirements

- **Python**: 3.12 or higher
- **RabbitMQ**: 3.8+ with Management plugin enabled
- **Docker**: Optional, for integration tests

## 📦 Installation Options

### Option 1: uvx (Recommended for end-users)

```bash
# No installation needed, runs in isolated environment
uvx rabbitmq-mcp-server queue list
```

### Option 2: pip (Traditional)

```bash
pip install rabbitmq-mcp-server
rabbitmq-mcp-server --version
```

### Option 3: uv (Recommended for developers)

```bash
# Clone repository
git clone https://github.com/guercheLE/rabbitmq-mcp-server.git
cd rabbitmq-mcp-server

# Install with uv
uv pip install -e ".[dev,vector]"

# Run tests
pytest --cov=src
```

## 🧪 Testing

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests (requires Docker)
pytest tests/integration/

# Run specific test
pytest tests/unit/test_validation.py -v
```

**Test Coverage**: 80%+ minimum, 95%+ for critical paths

## 💻 Development Workflow

### Setting Up Your Development Environment

```bash
# Clone the repository
git clone https://github.com/guercheLE/rabbitmq-mcp-server.git
cd rabbitmq-mcp-server

# Install dependencies with uv (recommended)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Code Quality Tools

This project uses automated code quality checks enforced via pre-commit hooks and CI/CD:

**Pre-commit Hooks** (run automatically on `git commit`):
- **black**: Code formatting (88 character line length)
- **isort**: Import sorting (black-compatible profile)
- **ruff**: Fast Python linting (replaces flake8/pylint)
- **mypy**: Static type checking (strict mode)

**Running Quality Checks Manually**:

```bash
# Format code with black
uv run black .

# Sort imports with isort
uv run isort .

# Run linting with ruff
uv run ruff check .

# Run type checking with mypy
uv run mypy src/

# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# Run tests with coverage
uv run pytest
```

### CI/CD Pipeline

The GitHub Actions CI/CD pipeline runs automatically on:
- Pull requests to `main` branch
- Pushes to `main` branch

**Quality Gates** (all must pass):
- ✅ All tests pass (pytest with zero failures)
- ✅ Linting passes (ruff with zero errors)
- ✅ Type checking passes (mypy strict mode with zero errors)
- ✅ Code coverage >80% (enforced via pytest-cov)

**Pipeline Features**:
- Tests run on Python 3.12 and 3.13
- Dependency caching for faster runs (<5 minutes typical)
- Parallel job execution (tests, linting, type checking run concurrently)
- Coverage reports uploaded to Codecov

**Status Badges**:

[![CI](https://github.com/guercheLE/rabbitmq-mcp-server/workflows/CI/badge.svg)](https://github.com/guercheLE/rabbitmq-mcp-server/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/guercheLE/rabbitmq-mcp-server/branch/main/graph/badge.svg)](https://codecov.io/gh/guercheLE/rabbitmq-mcp-server)

### OpenAPI Specification

The RabbitMQ Management API OpenAPI specification serves as the **single source of truth** for all operations, schemas, and documentation in this project.

**Location**: `docs-bmad/rabbitmq-http-api-openapi.yaml`

**Features**:
- 127+ RabbitMQ Management API operations fully documented
- OpenAPI 3.0.3 compliant specification
- Unique operationId for every operation (format: `namespace.action`)
- Complete request/response schemas with validation rules
- All operations include descriptions, parameters, and response definitions

**Validation**:

The OpenAPI specification is automatically validated in the CI/CD pipeline to ensure:
- Structural compliance with OpenAPI 3.0 schema
- All operations have unique operationId values
- No missing required fields or invalid schema references

Run validation locally:

```bash
# Validate the OpenAPI specification
uv run validate-openapi

# Or with custom path
uv run python scripts/validate_openapi.py --spec-path docs-bmad/rabbitmq-http-api-openapi.yaml
```

### Schema Generation

Pydantic models are automatically generated from the OpenAPI specification to ensure type-safe validation synchronized with the API specification.

**Generated File**: `src/schemas/generated_schemas.py`

**Features**:
- Automatic generation from OpenAPI component schemas
- Type-safe Pydantic v2 models with complete type annotations
- Field validation with constraints (min/max length, patterns, enums)
- RabbitMQ-specific validators for queue names, vhosts, exchange types
- Change detection to skip regeneration if OpenAPI unchanged

**Generate Schemas**:

```bash
# Generate with default paths
uv run python scripts/generate_schemas.py

# Generate with custom paths
uv run python scripts/generate_schemas.py \
  --spec-path docs-bmad/rabbitmq-http-api-openapi.yaml \
  --output-path src/schemas/generated_schemas.py

# Force regeneration (skip change detection)
uv run python scripts/generate_schemas.py --force
```

**When to Regenerate**:
- After modifying the OpenAPI specification
- When adding new component schemas
- When changing field types, constraints, or descriptions
- CI/CD automatically validates generated schemas match OpenAPI

**Notes**:
- Generated file includes header comment with timestamp and source path
- File is committed to version control for type checking and IDE support
- Do not edit generated file manually - changes will be overwritten
- All validations pass `mypy --strict` type checking

For more details, see:
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- Architecture Decision Record: ADR-008 (Pydantic for All Validation)

**Code Generation**:

All Pydantic schemas, operation registries, and semantic embeddings are generated from this OpenAPI specification at build time. This ensures:
- Zero drift between documentation and implementation
- Type-safe operations with compile-time validation
- Consistent API surface across all tools

For more details, see:
- [RabbitMQ Management API Documentation](https://rabbitmq.com/management.html)
- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- Architecture Decision Record: ADR-001 (OpenAPI-Driven Code Generation)

### Operation Registry

The Operation Registry is a JSON file containing metadata for all RabbitMQ Management API operations and AMQP protocol operations. It serves as the foundation for semantic discovery and dynamic operation execution.

**Generated File**: `data/operations.json`

**Features**:
- 132+ operations extracted from OpenAPI specification
- Complete operation metadata: operation_id, namespace, HTTP method, URL path, parameters, schemas
- AMQP protocol operations (publish, consume, ack, nack, reject) with message properties
- O(1) operation lookups by operation_id (dict structure)
- Metadata enrichment: deprecated flags, safety validation requirements, rate limit exemptions
- File size < 5MB for fast loading and distribution
- Load time < 100ms, operation lookup < 1ms (benchmarked)

**Generate Operation Registry**:

```bash
# Generate with default paths
uv run python scripts/extract_operations.py

# Generate with custom paths
uv run python scripts/extract_operations.py \
  --spec-path docs-bmad/rabbitmq-http-api-openapi.yaml \
  --output-path data/operations.json

# Exclude AMQP operations (HTTP only)
uv run python scripts/extract_operations.py --no-include-amqp
```

**Registry Structure**:

The registry is a JSON object with operation_id keys for O(1) lookup performance:

```json
{
  "model_version": "1.0.0",
  "generated_at": "2025-12-26T21:48:27.686810+00:00",
  "openapi_source": "docs-bmad/rabbitmq-http-api-openapi.yaml",
  "total_operations": 132,
  "operations": {
    "queues.list": {
      "operation_id": "queues.list",
      "namespace": "queues",
      "http_method": "GET",
      "url_path": "/api/queues",
      "description": "List all queues",
      "parameters": [
        {
          "name": "page",
          "location": "query",
          "type": "integer",
          "required": false,
          "description": "Page number for pagination"
        }
      ],
      "request_schema": null,
      "response_schema": {"$ref": "#/components/schemas/Queue", "name": "Queue"},
      "tags": ["Queues"],
      "requires_auth": true,
      "protocol": "http",
      "deprecated": false,
      "rate_limit_exempt": false,
      "safety_validation_required": false
    },
    "amqp.publish": {
      "operation_id": "amqp.publish",
      "namespace": "amqp",
      "http_method": "",
      "url_path": "",
      "description": "Publish a message to an exchange using AMQP protocol",
      "parameters": [
        {
          "name": "exchange",
          "location": "amqp",
          "type": "string",
          "required": true,
          "description": "Exchange name to publish to"
        }
      ],
      "protocol": "amqp",
      "deprecated": false
    }
  }
}
```

**Using the Operation Registry**:

```python
import json

# Load registry (fast: <100ms)
with open("data/operations.json") as f:
    registry = json.load(f)

# O(1) lookup by operation_id (fast: <1ms)
operation = registry["operations"]["queues.list"]
print(operation["http_method"])  # GET
print(operation["url_path"])     # /api/queues

# Filter operations by namespace
queue_ops = [
    op for op in registry["operations"].values()
    if op["namespace"] == "queues"
]

# Filter by protocol (HTTP vs AMQP)
amqp_ops = [
    op for op in registry["operations"].values()
    if op["protocol"] == "amqp"
]
```

**When to Regenerate**:
- After modifying the OpenAPI specification
- When adding new operations or changing operation metadata
- When updating AMQP operation definitions
- CI/CD automatically validates registry synchronization with OpenAPI

### Semantic Embeddings

The Semantic Embeddings system enables natural language search over RabbitMQ operations using pre-computed vector embeddings. This powers the `search-ids` MCP tool for semantic discovery.

**Generated File**: `data/embeddings.json`

**Features**:
- 132+ pre-computed 384-dimensional vector embeddings
- Uses sentence-transformers model `all-MiniLM-L6-v2` for optimal speed/quality balance
- Normalized vectors (unit length) for efficient cosine similarity calculations
- File size < 2MB for fast loading and distribution
- Load time < 500ms, query time < 100ms (benchmarked)
- Supports multi-language queries (matches operation descriptions)

**Generate Embeddings**:

```bash
# Generate with default paths
uv run python scripts/generate_embeddings.py

# Generate with custom paths
uv run python scripts/generate_embeddings.py \
  --registry-path data/operations.json \
  --output-path data/embeddings.json \
  --model-name all-MiniLM-L6-v2
```

**First Run**: The sentence-transformers model (~90MB) will download automatically to `~/.cache/torch/sentence_transformers/` on first run. Subsequent runs are faster using the cached model.

**Embedding Structure**:

The embeddings file contains metadata and pre-computed vectors for all operations:

```json
{
  "model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "model_version": "2.6.0",
  "embedding_dimension": 384,
  "generation_timestamp": "2025-12-26T20:05:50.746566",
  "embeddings": {
    "queues.list": [0.123, -0.456, 0.789, ...],
    "exchanges.create": [-0.234, 0.567, -0.890, ...],
    ...
  }
}
```

**Testing Embedding Quality**:

```bash
# Run quality tests with semantic queries
uv run python scripts/test_embeddings.py

# Example output:
# Query: 'listar filas'
# ✓ 1. queues.list                    1.0000
#   2. queues_detailed.list           0.7831
#   3. rebalance_queues.list          0.6435
```

**Performance Benchmarks**:

```bash
# Benchmark loading and query performance
uv run python scripts/benchmark_embeddings.py

# Example output:
# Load time:         11.86 ms (target: <500ms)
# Query time:         9.72 ms (target: <100ms)
# Embeddings count:    132
# File size:          1.36 MB (target: <50MB)
```

**Using Embeddings in Code**:

```python
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Load embeddings (fast: <500ms)
with open("data/embeddings.json") as f:
    data = json.load(f)

embeddings_dict = data["embeddings"]
op_ids = list(embeddings_dict.keys())
embeddings = np.array([embeddings_dict[op_id] for op_id in op_ids])

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Semantic search (fast: <100ms)
query = "list queues"
query_embedding = model.encode(query, normalize_embeddings=True)
similarities = np.dot(embeddings, query_embedding)

# Get top 5 results
top_indices = np.argsort(similarities)[::-1][:5]
results = [(op_ids[i], similarities[i]) for i in top_indices]
```

**When to Regenerate**:
- After modifying operation descriptions in operations.json
- When adding new operations to the registry
- When changing the embedding model (requires all embeddings to be regenerated)
- CI/CD automatically validates embeddings are synchronized with operations.json

**Model Selection Rationale**:

`all-MiniLM-L6-v2` was chosen for optimal performance:
- **Speed**: Fast inference (<10ms per query on CPU)
- **Quality**: High accuracy for short text similarity
- **Size**: Compact 384-dimensional vectors (vs 768 for larger models)
- **Multi-language**: Decent performance across languages including Portuguese
- **Community**: Well-maintained and widely used in production

For more details, see:
- [Sentence Transformers Documentation](https://www.sbert.net/)
- Architecture Decision Record: ADR-004 (JSON-based Vector Storage)
- Architecture Decision Record: ADR-007 (Build-time vs Runtime Generation)


**Notes**:
- Registry file is committed to version control for distribution
- URL paths preserve parameter placeholders: `/api/queues/{vhost}/{name}`
- AMQP operations marked with `protocol: "amqp"` (HTTP operations have `protocol: "http"`)
- Destructive operations (DELETE, purge, reset) marked with `safety_validation_required: true`
- Operation IDs follow format: `{namespace}.{action}` (e.g., `queues.list`, `amqp.publish`)

For more details, see:
- Architecture Decision Record: ADR-007 (Build-Time vs Runtime Generation)
- [OpenAPI 3.0 Paths Object](https://swagger.io/specification/#paths-object)
- [OpenAPI 3.0 Parameter Object](https://swagger.io/specification/#parameter-object)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:

- Setting up development environment
- Code style guidelines
- Testing requirements
- Pull request process

Quick contribution guide:

```bash
# 1. Fork and clone
git clone https://github.com/your-username/rabbitmq-mcp-server.git

# 2. Create feature branch
git checkout -b feature/your-feature

# 3. Install dependencies
uv pip install -e ".[dev]"

# 4. Make changes and test
pytest --cov=src

# 5. Commit with conventional commit format
git commit -m "feat: add new feature"

# 6. Push and create PR
git push origin feature/your-feature
```

## 📋 Roadmap

- [x] Queue operations (list, create, delete)
- [x] Exchange operations (list, create, delete)
- [x] Binding operations (list, create, delete)
- [x] Semantic discovery with vector search
- [x] Client-side pagination
- [x] Safety validations
- [ ] Message publishing/consuming
- [ ] Advanced monitoring (message rates, connection stats)
- [ ] Plugin management operations
- [ ] Cluster management operations
- [ ] User and permission management

## 📄 License

This project is licensed under the **GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later)**.

See [LICENSE](LICENSE) file for full text.

**What this means**:
- ✅ Use in proprietary software
- ✅ Modify and distribute
- ✅ Commercial use
- ⚠️ Must share modifications to library itself
- ⚠️ Must include license notice

## 🙏 Acknowledgments

- **RabbitMQ**: For the excellent message broker and Management API
- **MCP Protocol**: For the Model Context Protocol specification
- **ChromaDB**: For local vector database capabilities
- **sentence-transformers**: For efficient semantic embeddings

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/guercheLE/rabbitmq-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/guercheLE/rabbitmq-mcp-server/discussions)

## 🔗 Links

- **Repository**: https://github.com/guercheLE/rabbitmq-mcp-server
- **PyPI**: https://pypi.org/project/rabbitmq-mcp-server/ (coming soon)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **MCP Protocol**: https://modelcontextprotocol.io/
- **RabbitMQ Docs**: https://www.rabbitmq.com/documentation.html

---

**Built with ❤️ using Python 3.12+, MCP Protocol, and OpenAPI 3.0.3**
