# Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
|----------|----------|---------|---------------|-----------|
| Language | Python | 3.12+ | All | Type hints, async/await, modern features |
| Package Manager | uv | Latest | All | Fast dependency resolution, reproducible builds |
| MCP Framework | FastMCP (mcp SDK) | 1.2.0+ | Epic 1 | Official MCP Python implementation |
| Transport | Stdio + Streamable HTTP | MCP 2024-11-05 | Epic 1 | Stdio for AI assistants, HTTP for remote/browser |
| HTTP Server | Starlette (ASGI) | 0.39+ | Epic 1 | Built into FastMCP, lightweight, async |
| RabbitMQ HTTP Client | httpx | 0.27+ | Epic 2, 3 | Async HTTP client, connection pooling |
| RabbitMQ AMQP Client | pika | 1.3+ | Epic 2, 4 | Official Python AMQP 0-9-1 library |
| Schema Validation | Pydantic | 2.0+ | Epic 1 | Type-safe validation, OpenAPI integration |
| Semantic Search | sentence-transformers | 2.2+ | Epic 1 | all-MiniLM-L6-v2 model (384 dims, fast) |
| Vector Storage | JSON (embeddings.json) | N/A | Epic 1 | Simple, portable; migrate to sqlite-vec in Epic 9 if needed |
| Structured Logging | structlog | 24.1+ | Epic 7 | JSON logs, processors, context binding |
| Log Rotation | logging.handlers | stdlib | Epic 7 | TimedRotatingFileHandler + size trigger |
| Testing Framework | pytest | 8.0+ | Epic 6 | Fixtures, parametrization, async support |
| Test Containers | testcontainers-python | 4.0+ | Epic 6 | Real RabbitMQ for integration tests |
| Type Checking | mypy | 1.8+ | All | Strict mode, catch type errors early |
| Code Formatting | black | 24.0+ | All | Consistent style, 88 char line length |
| Import Sorting | isort | 5.13+ | All | Consistent import organization |
| Linting | ruff | 0.2+ | All | Fast Python linter, replaces flake8/pylint |
| OpenTelemetry | opentelemetry-sdk | 1.22+ | Epic 7 | Distributed tracing, metrics, OTLP export |
| Configuration | TOML + YAML | stdlib | Epic 2 | TOML primary, YAML legacy support |
| Environment Config | python-dotenv | 1.0+ | Epic 2 | .env file support for development |
| CLI Framework | argparse + rich | stdlib + 13.0+ | Epic 5 | Rich terminal output, tables, colors |
