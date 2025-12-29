# Technology Stack Details

## Core Technologies

**Python Ecosystem:**
- **Python 3.12+**: Modern type hints, pattern matching, performance improvements
- **uv**: Next-generation Python package manager (10-100x faster than pip)
- **Virtual Environment**: .venv managed by uv for dependency isolation

**MCP Protocol:**
- **FastMCP (mcp SDK 1.2.0+)**: Official Python MCP implementation
- **Transports**: 
  - Stdio: Standard input/output for AI assistant integration
  - Streamable HTTP: ASGI-based server for remote/browser clients
- **Protocol Version**: MCP 2024-11-05 specification
- **JSON-RPC 2.0**: Message protocol with standard error codes

**RabbitMQ Integration:**
- **Management API**: HTTP REST API (port 15672 default)
  - httpx 0.27+ for async HTTP client
  - Connection pooling (5 connections default)
  - 30-second timeout per request
- **AMQP 0-9-1 Protocol**: Message protocol (port 5672 default)
  - pika 1.3+ for AMQP client
  - Auto-reconnection with exponential backoff
  - Support for multiple vhosts

**Semantic Search:**
- **Model**: sentence-transformers/all-MiniLM-L6-v2
  - 384-dimensional embeddings
  - Fast inference (<50ms)
  - Good balance of speed and quality
- **Storage**: JSON file (embeddings.json)
  - Pre-computed at build time
  - Loaded into memory at server startup
  - Cosine similarity for search

**Data Validation:**
- **Pydantic 2.0+**: Type-safe schema validation
  - Auto-generated from OpenAPI components
  - Custom validators for RabbitMQ constraints
  - JSON schema generation for MCP tools

**Logging & Observability:**
- **structlog 24.1+**: Structured JSON logging
  - Processors: timestamper, dict_tracebacks, JSONRenderer
  - Context binding for correlation IDs
  - Log levels: DEBUG, INFO, WARNING, ERROR
- **OpenTelemetry SDK 1.22+**: Distributed tracing
  - OTLP exporter for traces and metrics
  - Automatic instrumentation of HTTP/AMQP calls
  - Jaeger/Prometheus compatibility

**Testing:**
- **pytest 8.0+**: Test framework with fixtures
- **testcontainers-python 4.0+**: RabbitMQ Docker containers
- **pytest-asyncio**: Async test support
- **Coverage.py**: Code coverage measurement (80%+ target)

**Code Quality:**
- **mypy 1.8+**: Static type checking (--strict mode)
- **black 24.0+**: Code formatting (88 char line length)
- **isort 5.13+**: Import sorting (black-compatible profile)
- **ruff 0.2+**: Fast Python linter (replaces flake8, pylint)
- **pre-commit**: Git hooks for quality enforcement

## Integration Points

**AI Assistant Integration (Stdio):**
```
[Claude Desktop] <-> [stdio] <-> [MCP Server] <-> [RabbitMQ]
     JSON-RPC              FastMCP          HTTP/AMQP
```

**Remote Client Integration (HTTP):**
```
[Browser/Remote Client] <-> [HTTPS] <-> [MCP Server] <-> [RabbitMQ]
       JSON-RPC                     Streamable HTTP    HTTP/AMQP
```

**Build-Time Generation Pipeline:**
```
[OpenAPI Spec] -> [generate_schemas.py] -> [Pydantic Models]
       |
       +-------> [generate_embeddings.py] -> [embeddings.json]
       |
       +-------> [Operation Registry] -> [operations.json]
```

**Runtime Operation Flow:**
```
1. [MCP Client] calls search-ids("list queues")
2. [Semantic Search] queries embeddings -> ["queues.list", "queues.list_by_vhost"]
3. [MCP Client] calls get-id("queues.list")
4. [Operation Registry] returns schema + documentation
5. [MCP Client] calls call-id("queues.list", {"vhost": "/"})
6. [Executor] validates params -> HTTP GET /api/queues/%2F
7. [HTTP Client] executes request with connection pool
8. [Response] validated with Pydantic -> returned to client
```

**Logging Flow:**
```
[Operation] -> [structlog] -> [Sanitizers] -> [Correlation ID] -> [File Handler]
                                                                        |
                                                                   [logs/*.log]
                                                                        |
                                                                [Rotation: daily + 100MB]
```

**Testing Infrastructure:**
```
[pytest] -> [testcontainers] -> [RabbitMQ Docker]
                                      |
                                [Per-test vhost isolation]
                                      |
                                [Integration tests]
```

**Configuration Loading:**
```
Priority: CLI args > Env vars > config.toml > .env file > defaults

[CLI Parser] ----+
                 |
[os.environ] ----+----> [Settings Model] -> [Validated Config]
                 |              |
[config.toml] ---+          [Pydantic]
                 |
[.env file] -----+
```

**Error Handling Flow:**
```
[Exception] -> [Error Handler] -> [Pydantic Error Model]
                     |
                     +-> [Correlation ID]
                     +-> [Structured Log]
                     +-> [JSON-RPC Error Response]
```
