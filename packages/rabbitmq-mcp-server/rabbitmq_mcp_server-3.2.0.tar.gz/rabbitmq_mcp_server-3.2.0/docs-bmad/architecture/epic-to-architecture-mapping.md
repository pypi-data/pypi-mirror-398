# Epic to Architecture Mapping

| Epic | Primary Components | Key Files | External Dependencies |
|------|-------------------|-----------|----------------------|
| **Epic 1: Foundation & MCP Protocol** | mcp_server/, schemas/, scripts/ | server.py, tools.py, search.py, generate_schemas.py, generate_embeddings.py | mcp, sentence-transformers, pydantic |
| **Epic 2: RabbitMQ Connection Management** | rabbitmq_connection/, config/ | http_client.py, amqp_client.py, reconnect.py, loader.py, settings.py | httpx, pika, python-dotenv, tomli |
| **Epic 3: Topology Operations** | tools/ | queue_ops.py, exchange_ops.py, binding_ops.py, safety.py | httpx, pydantic |
| **Epic 4: Message Publishing & Consumption** | tools/ | message_ops.py, schemas/amqp_schemas.py | pika, pydantic |
| **Epic 5: Console Client Interface** | cli/ | commands.py, output.py, __main__.py | rich, argparse |
| **Epic 6: Testing & Quality Framework** | tests/ | conftest.py, unit/, integration/, contract/ | pytest, testcontainers, pytest-asyncio |
| **Epic 7: Structured Logging & Observability** | logging/ | setup.py, sanitizers.py, correlation.py | structlog, opentelemetry-sdk |
| **Epic 8: Documentation & Release** | docs/, README.md | API.md, ARCHITECTURE.md, EXAMPLES.md | mkdocs (optional) |

**Component Responsibilities:**

**mcp_server/** - MCP Protocol Layer
- FastMCP server initialization
- 3-tool implementation (search-ids, get-id, call-id)
- Semantic search with embeddings
- Operation registry management
- Dual transport support (stdio + HTTP)

**rabbitmq_connection/** - RabbitMQ Communication
- HTTP Management API client with connection pooling
- AMQP 0-9-1 protocol client with pika
- Auto-reconnection with exponential backoff
- Health checks and monitoring
- TLS/SSL configuration

**tools/** - RabbitMQ Operations
- Queue operations (list, create, delete, purge)
- Exchange operations (list, create, delete)
- Binding operations (list, create, delete)
- Message operations (publish, consume, ack/nack/reject)
- Safety validations (prevent data loss)

**schemas/** - Data Validation
- generated_schemas.py: Auto-generated from OpenAPI
- amqp_schemas.py: Manually defined AMQP operation schemas
- Pydantic models for all requests/responses

**config/** - Configuration Management
- Multi-source loading (TOML, YAML, env vars, CLI args)
- Precedence: CLI > env > file > defaults
- Validation with Pydantic settings
- .env file support for development

**logging/** - Structured Logging
- JSON-structured logs with structlog
- Automatic credential sanitization
- Correlation ID propagation
- File-based output with rotation
- OpenTelemetry integration

**cli/** - Console Client
- Rich terminal output (tables, colors)
- Command structure: `<resource> <operation> [options]`
- Human-readable and JSON output formats
- Help system with examples

**scripts/** - Build-Time Code Generation
- generate_schemas.py: Pydantic models from OpenAPI
- generate_embeddings.py: Pre-compute semantic vectors
- validate_openapi.py: OpenAPI specification validation
