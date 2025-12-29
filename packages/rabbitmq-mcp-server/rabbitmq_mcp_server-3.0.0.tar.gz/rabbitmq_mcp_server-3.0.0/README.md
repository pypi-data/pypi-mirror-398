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
- 📖 **OpenAPI-Driven**: All operations defined in OpenAPI 3.1.0 specifications

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
│         (Generated from OpenAPI 3.1.0 Specs)            │
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

**Built with ❤️ using Python 3.12+, MCP Protocol, and OpenAPI 3.1.0**
