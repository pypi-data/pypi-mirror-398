# Project Structure

```
rabbitmq-mcp/
├── .bmad/                          # BMAD workflow artifacts
│   └── bmm/
│       ├── agents/                 # Agent definitions
│       ├── config.yaml             # BMM configuration
│       └── workflows/              # Workflow definitions
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI/CD
├── config/
│   ├── config.toml.example         # Example configuration
│   ├── config.yaml                 # Legacy YAML config support
│   └── logging_config.yaml         # Logging configuration
├── data/
│   ├── embeddings.json             # Pre-computed semantic embeddings
│   ├── operations.json             # Operation registry (from OpenAPI)
│   └── openapi-*.yaml              # OpenAPI specs per RabbitMQ version
├── docs/
│   ├── API.md                      # API reference
│   ├── ARCHITECTURE.md             # Architecture documentation
│   ├── CONTRIBUTING.md             # Contribution guidelines
│   └── EXAMPLES.md                 # Usage examples
├── docs-bmad/
│   ├── architecture.md             # This file
│   ├── bmm-workflow-status.yaml    # Workflow tracking
│   ├── brief/                      # Product briefs
│   ├── epics/                      # Epic definitions
│   └── prd/                        # Product requirements
├── logs/                           # Log files (created at runtime)
│   └── rabbitmq-mcp-*.log          # Daily rotated logs
├── scripts/
│   ├── generate_schemas.py         # Generate Pydantic schemas from OpenAPI
│   ├── generate_embeddings.py      # Generate semantic embeddings
│   ├── validate_openapi.py         # Validate OpenAPI specs
│   └── setup_test_env.py           # Test environment setup
├── src/
│   └── rabbitmq_mcp_server/
│       ├── __init__.py
│       ├── __main__.py             # Server entry point
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── commands.py         # CLI command implementations
│       │   └── output.py           # Rich terminal output formatting
│       ├── config/
│       │   ├── __init__.py
│       │   ├── loader.py           # Config file loading (TOML/YAML)
│       │   ├── settings.py         # Pydantic settings models
│       │   └── validation.py       # Config validation
│       ├── logging/
│       │   ├── __init__.py
│       │   ├── setup.py            # Structlog configuration
│       │   ├── sanitizers.py       # Credential sanitization
│       │   └── correlation.py      # Correlation ID management
│       ├── mcp_server/
│       │   ├── __init__.py
│       │   ├── server.py           # FastMCP server instance
│       │   ├── tools.py            # MCP tool implementations
│       │   ├── search.py           # Semantic search (search-ids)
│       │   ├── operations.py       # Operation registry (get-id)
│       │   └── executor.py         # Operation execution (call-id)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── errors.py           # Error response models
│       │   ├── operations.py       # Operation metadata models
│       │   └── mcp_types.py        # MCP-specific types
│       ├── rabbitmq_connection/
│       │   ├── __init__.py
│       │   ├── http_client.py      # Management API HTTP client
│       │   ├── amqp_client.py      # AMQP protocol client (pika)
│       │   ├── connection_pool.py  # HTTP connection pooling
│       │   ├── reconnect.py        # Auto-reconnection logic
│       │   └── health.py           # Connection health checks
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── generated_schemas.py # Auto-generated from OpenAPI
│       │   └── amqp_schemas.py     # Manually defined AMQP schemas
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── queue_ops.py        # Queue operations
│       │   ├── exchange_ops.py     # Exchange operations
│       │   ├── binding_ops.py      # Binding operations
│       │   ├── message_ops.py      # Message operations
│       │   └── safety.py           # Safety validations
│       └── utils/
│           ├── __init__.py
│           ├── embeddings.py       # Embedding utilities
│           └── validators.py       # Input validators
├── tests/
│   ├── conftest.py                 # Pytest configuration & fixtures
│   ├── contract/                   # MCP protocol compliance tests
│   │   ├── test_mcp_protocol.py
│   │   └── test_json_rpc.py
│   ├── integration/                # Integration tests with RabbitMQ
│   │   ├── test_queue_ops.py
│   │   ├── test_exchange_ops.py
│   │   ├── test_binding_ops.py
│   │   └── test_message_ops.py
│   └── unit/                       # Unit tests
│       ├── test_search.py
│       ├── test_operations.py
│       ├── test_executor.py
│       └── test_sanitizers.py
├── .env.example                    # Example environment variables
├── .gitignore
├── .pre-commit-config.yaml         # Pre-commit hook configuration
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml                  # Project metadata & dependencies
├── pytest.ini                      # Pytest configuration
├── README.md
└── uv.lock                         # Locked dependencies
```
