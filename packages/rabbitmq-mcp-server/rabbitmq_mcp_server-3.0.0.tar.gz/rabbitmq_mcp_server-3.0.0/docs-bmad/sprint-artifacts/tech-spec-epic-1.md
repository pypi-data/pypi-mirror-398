# Epic Technical Specification: Foundation & MCP Protocol

Date: 2025-11-16
Author: Luciano
Epic ID: 1
Status: Draft

---

## Overview

Epic 1 establishes the foundational infrastructure for the RabbitMQ MCP Server by implementing an OpenAPI-driven code generation pipeline and the 3-tool semantic discovery pattern (search-ids, get-id, call-id). This epic solves the MCP tool explosion problem by exposing 100+ RabbitMQ Management API operations through just three tools with natural language search, enabling developers to interact with RabbitMQ using AI assistants like Claude without memorizing API endpoints.

The core architecture leverages OpenAPI specifications as the single source of truth, generating Pydantic schemas, operation registries, and semantic embeddings at build time. The MCP server implements JSON-RPC 2.0 over stdio transport for AI assistant integration, with modern Python 3.12+ patterns including strict type checking, async/await, and comprehensive testing.

## Objectives and Scope

**In Scope:**
- ✅ Project repository setup with Python 3.12+, uv package manager, and modern project structure (src-layout)
- ✅ Pre-commit hooks (black, isort, mypy, ruff) and GitHub Actions CI/CD pipeline
- ✅ OpenAPI specification integration from `docs-bmad/rabbitmq-http-api-openapi.yaml` (~4800 lines, 100+ operations)
- ✅ Automated Pydantic schema generation from OpenAPI component schemas
- ✅ Operation registry generation (JSON file) with metadata for all Management API operations
- ✅ Semantic embeddings generation using sentence-transformers (all-MiniLM-L6-v2, 384 dimensions)
- ✅ MCP server foundation with JSON-RPC 2.0 over stdio transport
- ✅ Three MCP tools: `search-ids` (semantic search), `get-id` (operation docs), `call-id` (HTTP execution)
- ✅ Multi-version API support (3.11.x, 3.12.x, 3.13.x via environment variable)
- ✅ Type-safe parameter validation using Pydantic models
- ✅ Connection pooling and timeout handling for HTTP client
- ✅ Structured logging with correlation IDs (foundation only, detailed implementation in Epic 7)

**Out of Scope:**
- ❌ AMQP protocol operations (publish, consume, ack/nack) - covered in Epic 4
- ❌ RabbitMQ connection management and auto-reconnection - covered in Epic 2
- ❌ Topology operations implementation (queues, exchanges, bindings) - covered in Epic 3
- ❌ Console client CLI interface - covered in Epic 5
- ❌ Comprehensive logging features (rotation, sanitization, audit) - covered in Epic 7
- ❌ Advanced testing (integration, contract, performance) - covered in Epic 6
- ❌ Complete documentation suite - covered in Epic 8
- ❌ sqlite-vec vector database integration - Phase 2 feature (Epic 9)

## System Architecture Alignment

**Architecture Alignment:**

This epic implements **ADR-001 (OpenAPI-Driven Code Generation)** and **ADR-002 (3-Tool Semantic Discovery Pattern)** from the architecture decisions. The build-time generation pipeline (ADR-007) creates artifacts from OpenAPI specifications that are consumed at runtime by the MCP server.

**Components Created:**
- **MCP Server Foundation** (`src/mcp_server/`): JSON-RPC 2.0 handler, tool registry, stdio transport
- **Schema Generation** (`scripts/generate_schemas.py`): OpenAPI → Pydantic conversion pipeline
- **Operation Registry** (`scripts/extract_operations.py`): OpenAPI paths → JSON metadata
- **Embedding Generation** (`scripts/generate_embeddings.py`): Operation descriptions → 384D vectors
- **HTTP Client** (`src/rabbitmq_mcp_connection/http_client.py`): Connection pooling, timeout handling

**Architectural Constraints Followed:**
- Python 3.12+ with strict mypy type checking (technology-stack-details.md)
- Async/await pattern for all I/O operations (consistency-rules.md)
- Pydantic for all data validation (ADR-008)
- Structured logging with structlog (ADR-009, foundation only)
- JSON-based vector storage for MVP (ADR-004, pre-computed embeddings)
- Stateless server design (ADR-005, no shared state between tool calls)

## Detailed Design

### Services and Modules

| Module | Responsibilities | Inputs | Outputs | Owner |
|--------|-----------------|--------|---------|-------|
| `mcp_server/server.py` | MCP protocol handler, JSON-RPC 2.0 dispatcher, tool registry | stdio JSON-RPC requests | JSON-RPC responses | Story 1.7 |
| `mcp_server/tools/search_ids.py` | Semantic search implementation, embedding comparison, result ranking | Query string, threshold, max_results | Ranked operation IDs with scores | Story 1.8 |
| `mcp_server/tools/get_id.py` | Operation documentation retrieval, schema formatting | Operation ID | Operation details (method, path, params, schemas) | Story 1.9 |
| `mcp_server/tools/call_id.py` | Operation execution, parameter validation, HTTP request orchestration | Operation ID, parameters dict | Operation result or error | Story 1.10 |
| `rabbitmq_mcp_connection/http_client.py` | HTTP client with connection pooling, timeout handling, TLS support | HTTP method, URL, headers, body | HTTP response or exception | Story 1.10 |
| `models/operation.py` | Operation registry models, parameter schemas, response models | N/A (data models) | Type-safe operation representations | Story 1.5 |
| `schemas/generated_schemas.py` | Auto-generated Pydantic models from OpenAPI | N/A (generated) | Pydantic BaseModel classes for validation | Story 1.4 |
| `scripts/generate_schemas.py` | OpenAPI → Pydantic code generation | OpenAPI YAML file | Python file with Pydantic models | Story 1.4 |
| `scripts/extract_operations.py` | OpenAPI → operation registry JSON | OpenAPI YAML file | operations.json with metadata | Story 1.5 |
| `scripts/generate_embeddings.py` | Operation descriptions → vector embeddings | operations.json | embeddings.json (384D vectors) | Story 1.6 |
| `config/settings.py` | Configuration management with Pydantic Settings | Env vars, config files, CLI args | Validated Settings object | Story 1.1 |
| `logging/logger.py` | Structured logging setup with structlog | N/A (initialization) | Logger instances with context binding | Story 1.7 |

### Data Models and Contracts

**Core Data Models:**

```python
# Operation Registry Entry (operations.json)
{
  "operation_id": "queues.list",           # Unique identifier
  "namespace": "queues",                    # Grouping category
  "http_method": "GET",                     # HTTP method
  "url_path": "/api/queues/{vhost}",       # URL template with parameters
  "description": "List all queues in vhost", # Human-readable description
  "parameters": [                           # Parameter definitions
    {
      "name": "vhost",
      "location": "path",                   # path | query | header
      "type": "string",
      "required": true,
      "description": "Virtual host name"
    }
  ],
  "request_schema": null,                   # Pydantic model name for body
  "response_schema": "QueueListResponse",   # Pydantic model name for response
  "examples": [...],                        # Sample requests/responses
  "tags": ["queues", "management"],
  "requires_auth": true,
  "deprecated": false
}

# Semantic Embedding (embeddings.json)
{
  "model_name": "all-MiniLM-L6-v2",
  "model_version": "2.6.0",
  "embedding_dimension": 384,
  "embeddings": {
    "queues.list": [0.123, -0.456, ...],   # 384-dimensional vector
    "queues.create": [0.789, 0.234, ...]
  }
}

# MCP Tool Response (search-ids)
{
  "results": [
    {
      "operation_id": "queues.list",
      "description": "List all queues",
      "similarity_score": 0.89,
      "namespace": "queues"
    }
  ]
}

# MCP Tool Response (get-id)
{
  "operation_id": "queues.list",
  "http_method": "GET",
  "url_path": "/api/queues/{vhost}",
  "description": "List all queues in a virtual host",
  "parameters": [...],
  "examples": [...]
}

# MCP Tool Response (call-id)
{
  "status": "success",
  "result": [                               # Actual RabbitMQ response
    {
      "name": "orders",
      "vhost": "/",
      "durable": true,
      "messages": 42
    }
  ],
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Pydantic Validation Models (Auto-Generated):**

```python
# Example from generated_schemas.py
class QueueInfo(BaseModel):
    """Queue information response model."""
    name: str = Field(..., description="Queue name")
    vhost: str = Field(..., description="Virtual host")
    durable: bool = Field(default=True, description="Durable flag")
    auto_delete: bool = Field(default=False, description="Auto-delete flag")
    arguments: Dict[str, Any] = Field(default_factory=dict)
    messages: int = Field(default=0, ge=0, description="Message count")
    consumers: int = Field(default=0, ge=0, description="Consumer count")
    
    model_config = ConfigDict(extra='allow')  # Allow additional fields

class QueueCreateRequest(BaseModel):
    """Queue creation request parameters."""
    durable: bool = Field(default=True)
    auto_delete: bool = Field(default=False)
    arguments: Optional[Dict[str, Any]] = None
    
    @field_validator('arguments')
    @classmethod
    def validate_arguments(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate queue arguments format."""
        if v is not None:
            # RabbitMQ-specific validations
            if 'x-message-ttl' in v and not isinstance(v['x-message-ttl'], int):
                raise ValueError("x-message-ttl must be integer")
        return v
```

### APIs and Interfaces

**MCP Protocol Interface (JSON-RPC 2.0 over stdio):**

```
Method: initialize
Request:
  - protocolVersion: "2024-11-05"
  - capabilities: {...}
  - clientInfo: {name, version}
Response:
  - protocolVersion: "2024-11-05"
  - capabilities: {tools: {...}}
  - serverInfo: {name: "rabbitmq-mcp-server", version: "1.3.0"}

Method: tools/list
Response:
  - tools: [
      {
        name: "search-ids",
        description: "Search for operations using natural language",
        inputSchema: {type: "object", properties: {...}}
      },
      {name: "get-id", ...},
      {name: "call-id", ...}
    ]

Method: tools/call
Request:
  - name: "search-ids" | "get-id" | "call-id"
  - arguments: {operation-specific parameters}
Response:
  - content: [{type: "text", text: "...result..."}]
  - isError: false
Error Response:
  - code: -32602 (Invalid params) | -32601 (Method not found) | -32700 (Parse error)
  - message: "Error description"
  - data: {error_code, context}
```

**HTTP Client Interface (Internal):**

```python
class HTTPClient:
    """Async HTTP client with connection pooling."""
    
    async def request(
        self,
        method: str,                      # GET, POST, PUT, DELETE
        url: str,                         # Full URL with replaced parameters
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> httpx.Response:
        """Execute HTTP request with connection pool."""
        # Returns httpx.Response or raises httpx.HTTPError
        
    async def close(self) -> None:
        """Close connection pool gracefully."""
```

**Semantic Search Interface:**

```python
class SemanticSearch:
    """Semantic search over operation embeddings."""
    
    def __init__(self, embeddings_path: Path, model_name: str):
        """Load embeddings and initialize model."""
        
    async def search(
        self,
        query: str,
        threshold: float = 0.7,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search for operations matching query.
        
        Returns: List of {operation_id, description, similarity_score, namespace}
                 sorted by similarity_score descending
        """
        
    def _compute_similarity(self, query_vec: np.ndarray, op_vec: np.ndarray) -> float:
        """Cosine similarity between vectors."""
```

**Operation Executor Interface:**

```python
class OperationExecutor:
    """Execute RabbitMQ operations with validation."""
    
    def __init__(self, http_client: HTTPClient, registry: OperationRegistry):
        """Initialize with HTTP client and operation registry."""
        
    async def execute(
        self,
        operation_id: str,
        parameters: Dict[str, Any]
    ) -> ExecutionResult:
        """
        Validate parameters and execute operation.
        
        Steps:
        1. Load operation metadata from registry
        2. Validate parameters with Pydantic schema
        3. Build HTTP request (URL, method, headers, body)
        4. Execute via HTTP client
        5. Validate response with Pydantic schema
        6. Return structured result
        
        Returns: {status: "success", result: {...}, correlation_id: "..."}
        Raises: ValidationError, HTTPError, OperationError
        """
```

### Workflows and Sequencing

**Build-Time Generation Pipeline:**

```
1. Developer runs: uv run python scripts/validate_openapi.py
   └─> Validates OpenAPI spec structure and completeness

2. Developer runs: uv run python scripts/generate_schemas.py
   Input: docs-bmad/rabbitmq-http-api-openapi.yaml
   Process:
   ├─> Parse OpenAPI component schemas
   ├─> Generate Pydantic BaseModel classes with validators
   └─> Write to src/schemas/generated_schemas.py
   Output: Type-safe Pydantic models for validation

3. Developer runs: uv run python scripts/extract_operations.py
   Input: docs-bmad/rabbitmq-http-api-openapi.yaml
   Process:
   ├─> Parse OpenAPI paths section (100+ operations)
   ├─> Extract metadata: id, method, path, params, schemas
   ├─> Add manual AMQP operations (not in OpenAPI)
   └─> Write to data/operations.json
   Output: Operation registry with complete metadata

4. Developer runs: uv run python scripts/generate_embeddings.py
   Input: data/operations.json
   Process:
   ├─> Load sentence-transformers model (all-MiniLM-L6-v2)
   ├─> Generate 384D vectors for each operation description
   ├─> Store in JSON format with metadata
   └─> Write to data/embeddings.json
   Output: Pre-computed embeddings for semantic search

5. Artifacts ready for runtime:
   ├─> src/schemas/generated_schemas.py (Pydantic models)
   ├─> data/operations.json (operation metadata)
   └─> data/embeddings.json (semantic vectors)
```

**Runtime Semantic Discovery Flow:**

```
User: "Show me all queues"
   ↓
1. AI Assistant sends JSON-RPC request to MCP server (stdio)
   {method: "tools/call", params: {name: "search-ids", arguments: {query: "list all queues"}}}
   ↓
2. MCP Server → search-ids tool
   ├─> Load embeddings from data/embeddings.json (cached in memory)
   ├─> Generate query embedding using sentence-transformers
   ├─> Compute cosine similarity with all operation embeddings
   ├─> Filter results where similarity >= 0.7
   ├─> Sort by similarity score descending
   └─> Return top 10 results
   ↓
3. Response: [
     {operation_id: "queues.list", score: 0.89},
     {operation_id: "queues.list_by_vhost", score: 0.85}
   ]
   ↓
4. AI Assistant sends: tools/call → get-id("queues.list")
   ↓
5. MCP Server → get-id tool
   ├─> Load operations.json (cached in memory)
   ├─> Lookup operation by ID (O(1) dict access)
   └─> Return complete operation documentation
   ↓
6. Response: {
     operation_id: "queues.list",
     http_method: "GET",
     url_path: "/api/queues/{vhost}",
     parameters: [{name: "vhost", type: "string", required: true}],
     description: "List all queues in virtual host"
   }
   ↓
7. AI Assistant sends: tools/call → call-id("queues.list", {vhost: "/"})
   ↓
8. MCP Server → call-id tool
   ├─> Load operation metadata from registry
   ├─> Validate parameters with Pydantic schema
   ├─> Build HTTP request: GET /api/queues/%2F
   ├─> Execute via HTTPClient (connection pool)
   ├─> Receive response from RabbitMQ Management API
   ├─> Validate response with Pydantic schema
   └─> Return structured result
   ↓
9. Response: {
     status: "success",
     result: [{name: "orders", messages: 42}, ...],
     correlation_id: "uuid"
   }
   ↓
10. AI Assistant presents results to user
```

**Server Startup Sequence:**

```
1. Load configuration from env vars, config.toml, CLI args
2. Initialize structured logger with correlation ID support
3. Load operation registry (data/operations.json) into memory
4. Load embeddings (data/embeddings.json) into memory
5. Initialize sentence-transformers model for query encoding
6. Create HTTP client with connection pool (5 connections)
7. Register MCP tools (search-ids, get-id, call-id)
8. Start stdio transport listener (JSON-RPC 2.0)
9. Log server ready message
10. Wait for incoming JSON-RPC requests
```

## Non-Functional Requirements

### Performance

**Latency Targets (FR-002, FR-003, FR-004):**
- Semantic search (`search-ids`): <100ms at p95, <150ms at p99
- Operation documentation retrieval (`get-id`): <50ms at p95
- Operation execution (`call-id`): <200ms at p95 for HTTP operations
- Server startup: <1 second to ready state

**Resource Constraints:**
- Memory usage: <1GB per instance under normal load
- Embeddings file: <50MB for distribution
- Operations registry: <5MB for fast loading
- Operation lookup: <1ms (dict-based O(1) access)
- Embedding loading: <500ms on startup

**Optimization Strategies:**
- Pre-compute all embeddings at build time (no runtime generation)
- Cache operation registry and embeddings in memory after startup
- LRU cache for query embeddings (max 100 queries)
- Connection pooling for HTTP (default 5 connections, configurable)
- Numpy vectorized operations for similarity calculations
- Async/await for all I/O operations (non-blocking)

**Benchmarking Requirements:**
- Unit tests validate latency targets with pytest-benchmark
- Performance tests measure p50/p95/p99 latencies
- Reference hardware: 4-core CPU, 8GB RAM, SSD

### Security

**Authentication (Stories 1.10, 2.2):**
- RabbitMQ Management API: HTTP Basic Auth (username/password)
- Credentials loaded from: CLI args > env vars > config.toml > prompts
- TLS/SSL support with certificate verification (configurable via --insecure flag)
- No credential storage in plaintext (environment variables only)

**Credential Protection (Foundation for Epic 7):**
- Structured logging foundation includes context binding for correlation IDs
- No passwords logged in this epic (validation only)
- Comprehensive sanitization implemented in Epic 7 (FR-014)
- Connection string sanitization: `amqp://user:pass@host` → `amqp://[REDACTED]@host`

**Network Security:**
- TLS/SSL support for Management API connections
- Certificate verification enabled by default
- Self-signed certificate support via --insecure flag (development only)
- Connection timeout: 30 seconds (prevents hanging on network issues)

**Input Validation:**
- All parameters validated with Pydantic before execution
- JSON-RPC 2.0 message format validation
- Operation ID validation (must exist in registry)
- Parameter type checking (string, int, bool, dict, list)

**Error Information Disclosure:**
- Generic error messages for authentication failures
- No stack traces in production mode
- Correlation IDs for error tracking without exposing internals

### Reliability/Availability

**Stateless Design (ADR-005):**
- No shared state between tool calls
- Each MCP tool call is independent
- Connection pool state isolated per server instance
- Enables horizontal scaling (multiple instances)

**Error Handling:**
- Structured error responses with error codes and context
- JSON-RPC 2.0 error codes: -32700 (parse), -32600 (invalid request), -32601 (method not found), -32602 (invalid params)
- Application error codes: CONNECTION_FAILED, VALIDATION_FAILED, OPERATION_TIMEOUT, NOT_FOUND
- All errors include correlation IDs for tracing

**Timeout Handling:**
- HTTP request timeout: 30 seconds (configurable)
- Operation timeout: 30 seconds max (fail-fast pattern)
- Connection pool timeout: 10 seconds when pool exhausted
- No automatic retries in Epic 1 (fail-fast, retry in Epic 2)

**Graceful Degradation:**
- Invalid operation IDs return clear error with suggestions
- Missing parameters return validation errors with required fields
- Connection failures return immediately without blocking
- Zero search results (all scores <0.7) return empty list with suggestion

**Startup Resilience:**
- Validate operation registry and embeddings on startup
- Fail fast if critical files missing (operations.json, embeddings.json)
- Log startup errors with clear remediation steps
- Health check available immediately after startup

### Observability

**Structured Logging (Foundation for Epic 7):**
- structlog with JSON output format
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation ID generation and propagation
- Context binding for request-scoped data
- Foundation logging includes: server startup, tool calls, operation execution, errors

**Log Fields (Standard):**
- `timestamp`: ISO 8601 format
- `level`: Log level string
- `logger`: Module name
- `event`: Event name (snake_case)
- `correlation_id`: UUID for request tracing
- Additional context: operation_id, duration_ms, status, error_code

**OpenTelemetry (Foundation for Epic 7):**
- OpenTelemetry SDK integrated (API only in Epic 1)
- OTLP exporter configuration prepared
- Trace context propagation prepared
- Full instrumentation in Epic 7 (FR-019)

**Metrics (Prepared for Epic 7):**
- Operation counters: success/failure by operation_id
- Latency histograms: p50, p95, p99 by tool
- Search result counts: results returned per query
- HTTP client metrics: connection pool usage, timeout rate

**Debugging Support:**
- DEBUG log level includes: parameter values, intermediate states, HTTP requests/responses
- Correlation IDs enable end-to-end tracing
- Structured logs enable filtering by operation_id, status, error_code
- Exception logging includes stack traces (sanitized in production)

## Dependencies and Integrations

**Core Dependencies (pyproject.toml):**

```toml
[project.dependencies]
mcp>=1.0.0                          # MCP SDK for protocol implementation
pydantic>=2.0                       # Data validation and schema generation
pydantic-settings>=2.0              # Configuration management
jsonschema>=4.20                    # JSON schema validation
pyyaml>=6.0                         # YAML parsing for OpenAPI
httpx>=0.27                         # Async HTTP client with connection pooling
structlog>=24.1                     # Structured logging
opentelemetry-api>=1.22             # Observability API (foundation)
opentelemetry-sdk>=1.22             # Observability SDK (foundation)
opentelemetry-instrumentation>=0.43b0  # Auto-instrumentation (foundation)
```

**Development Dependencies:**

```toml
[project.optional-dependencies.dev]
pytest>=8.0                         # Test framework
pytest-asyncio>=0.23                # Async test support
pytest-cov>=4.1                     # Code coverage
pytest-mock>=3.12                   # Mocking support
testcontainers>=3.7                 # Docker containers for integration tests
datamodel-code-generator>=0.25      # OpenAPI → Pydantic code generation
black>=24.1                         # Code formatting
ruff>=0.2                           # Fast linting
mypy>=1.8                           # Static type checking
types-pyyaml>=6.0                   # Type stubs for pyyaml
types-requests>=2.32                # Type stubs for requests
types-tabulate>=0.9                 # Type stubs for tabulate
sentence-transformers>=2.6,<3       # Semantic embedding model
numpy>=1.26,<2.0                    # Numerical operations for vectors
```

**System Dependencies:**
- Python 3.12+ (required for modern type hints and performance)
- uv package manager (10-100x faster than pip)
- Git for version control
- Docker (optional, for integration tests with testcontainers)

**External Service Dependencies:**
- RabbitMQ Management API (HTTP REST API, port 15672 default)
  - Version support: 3.11.x, 3.12.x, 3.13.x
  - Requires Management Plugin enabled (standard in most installations)
  - Authentication: HTTP Basic Auth (username/password)
  - TLS/SSL optional but recommended for production

**AI Assistant Integration:**
- MCP protocol 2024-11-05 specification
- JSON-RPC 2.0 message format
- Stdio transport (stdin/stdout)
- Compatible clients: Claude Desktop, ChatGPT (via MCP proxy), custom MCP clients

**Build-Time Integration:**
- OpenAPI specification: `docs-bmad/rabbitmq-http-api-openapi.yaml`
- Sentence-transformers model: `all-MiniLM-L6-v2` (384 dimensions)
  - Downloaded from Hugging Face on first run (~90MB)
  - Cached locally in `~/.cache/huggingface/`

**Runtime Data Files:**
- `data/operations.json`: Operation registry with metadata (~200KB)
- `data/embeddings.json`: Pre-computed semantic vectors (~15MB)
- Generated schemas: `src/schemas/generated_schemas.py` (~500KB)

**Version Constraints:**
- Python: >=3.12,<4.0
- httpx: >=0.27 (async support, connection pooling)
- pydantic: >=2.0 (performance improvements, validation)
- sentence-transformers: >=2.6,<3 (embedding model compatibility)
- numpy: >=1.26,<2.0 (vector operations, API stability)

## Acceptance Criteria (Authoritative)

**AC-1: Project Setup (Story 1.1)**
- Repository initialized with src-layout structure (src/, tests/, scripts/, data/, config/, docs/)
- Python 3.12+ configured with uv package manager
- pyproject.toml contains all core dependencies with correct version constraints
- .gitignore excludes build artifacts and sensitive files
- README.md includes project overview and quick start instructions
- Architecture initialization executed if using template

**AC-2: Quality Tools (Story 1.2)**
- Pre-commit hooks installed and configured (.pre-commit-config.yaml)
- Hooks validate: black, isort, mypy, ruff before commit
- GitHub Actions CI/CD pipeline (.github/workflows/ci.yml) runs tests, linting, type checking
- CI runs on multiple Python versions (3.12, 3.13)
- Code coverage >80% enforced in CI pipeline

**AC-3: OpenAPI Integration (Story 1.3)**
- OpenAPI specification at `docs-bmad/rabbitmq-http-api-openapi.yaml` passes validation
- Specification contains 100+ operation definitions
- All operations have unique operationId values
- Validation script `scripts/validate_openapi.py` confirms integrity

**AC-4: Schema Generation (Story 1.4)**
- Running `python scripts/generate_schemas.py` creates `src/schemas/generated_schemas.py`
- Each OpenAPI component schema has corresponding Pydantic BaseModel
- Field types correctly mapped (string→str, integer→int, etc.)
- Required fields enforced with Pydantic validators
- Generated code passes mypy --strict type checking

**AC-5: Operation Registry (Story 1.5)**
- Running `python scripts/extract_operations.py` creates `data/operations.json`
- Each operation entry contains: operation_id, namespace, http_method, url_path, description, parameters
- All 100+ operations from OpenAPI represented in registry
- Registry file <5MB, operation lookups complete in <1ms

**AC-6: Embeddings Generation (Story 1.6)**
- Running `python scripts/generate_embeddings.py` creates `data/embeddings.json`
- Embeddings use sentence-transformers model `all-MiniLM-L6-v2` (384 dimensions)
- Each operation has corresponding embedding vector
- Embeddings file <50MB, load into memory in <500ms
- Cosine similarity calculations complete in <50ms

**AC-7: MCP Server Foundation (Story 1.7)**
- MCP server responds to JSON-RPC 2.0 requests via stdio
- Implements MCP methods: initialize, tools/list, tools/call
- initialize returns server info: name, version, protocol_version="2024-11-05"
- tools/list returns 3 tools: search-ids, get-id, call-id
- Invalid requests return JSON-RPC error codes (-32700, -32600, -32601, -32602)
- Server startup completes in <1 second

**AC-8: search-ids Tool (Story 1.8)**
- Accepts query string, returns ranked operation IDs with similarity scores
- Results filtered by threshold ≥0.7, ordered by score descending
- Search completes in <100ms at p95
- Zero matches return empty list with suggestion
- Accepts parameters: query (required), threshold (default 0.7), max_results (default 10)

**AC-9: get-id Tool (Story 1.9)**
- Accepts operation_id, returns complete operation documentation
- Response includes: http_method, url_path, parameters, request/response schemas, examples
- Retrieval completes in <50ms
- Invalid operation IDs return error with suggestion to use search-ids

**AC-10: call-id Tool (Story 1.10)**
- Accepts operation_id and parameters, executes HTTP request to RabbitMQ
- Parameters validated against Pydantic schema before execution
- Validation errors list specific missing/invalid fields
- Successful operations return: status="success", result={...}, correlation_id
- Operations complete in <200ms at p95
- 30-second timeout enforced, connection failures return immediately

**AC-11: Multi-Version Support (Story 1.11)**
- Environment variable `RABBITMQ_API_VERSION` selects API version (3.11, 3.12, 3.13)
- Server loads corresponding OpenAPI specification from `data/openapi-{version}.yaml`
- Unsupported versions return error listing supported versions
- Default version is 3.13 (latest)
- Version displayed in server info

## Traceability Mapping

| AC | Spec Section | Components/APIs | Test Approach |
|----|-------------|-----------------|---------------|
| AC-1 | Project Setup | Repository structure, pyproject.toml, .gitignore | Unit: Verify directory structure, file existence. Integration: Run uv install successfully |
| AC-2 | Quality Tools | .pre-commit-config.yaml, .github/workflows/ci.yml | Unit: Validate config files. Integration: Trigger pre-commit and CI pipeline |
| AC-3 | OpenAPI Integration | docs-bmad/rabbitmq-http-api-openapi.yaml, scripts/validate_openapi.py | Unit: OpenAPI validator passes. Integration: Run validation script returns 0 |
| AC-4 | Schema Generation | scripts/generate_schemas.py, src/schemas/generated_schemas.py | Unit: Generated models pass mypy. Integration: Run generation, validate Pydantic models |
| AC-5 | Operation Registry | scripts/extract_operations.py, data/operations.json | Unit: Registry structure validation. Integration: Lookup performance test <1ms |
| AC-6 | Embeddings | scripts/generate_embeddings.py, data/embeddings.json | Unit: Embedding dimension=384. Integration: Load time <500ms, similarity calc <50ms |
| AC-7 | MCP Foundation | src/mcp_server/server.py, stdio transport | Unit: JSON-RPC message parsing. Contract: MCP protocol compliance tests |
| AC-8 | search-ids | src/mcp_server/tools/search_ids.py, SemanticSearch class | Unit: Similarity calculation. Performance: Latency <100ms p95. Integration: End-to-end search |
| AC-9 | get-id | src/mcp_server/tools/get_id.py, OperationRegistry class | Unit: Registry lookup. Performance: Latency <50ms. Integration: Invalid ID handling |
| AC-10 | call-id | src/mcp_server/tools/call_id.py, HTTPClient, OperationExecutor | Unit: Parameter validation. Integration: HTTP request execution with testcontainers |
| AC-11 | Multi-Version | Environment handling, OpenAPI file selection | Unit: Version detection. Integration: Load different API versions successfully |

**FR to AC Traceability:**

- **FR-001 (MCP Protocol Foundation)**: AC-7 (MCP server), AC-8, AC-9, AC-10 (3 tools)
- **FR-002 (Semantic Search)**: AC-6 (embeddings), AC-8 (search-ids with <100ms latency)
- **FR-003 (Operation Documentation)**: AC-5 (operation registry), AC-9 (get-id with <50ms latency)
- **FR-004 (Operation Execution)**: AC-10 (call-id with validation, <200ms latency, 30s timeout)
- **FR-021 (Multi-Version Support)**: AC-11 (version selection via env var)

**Story to Component Mapping:**

- Story 1.1 → Repository structure, pyproject.toml, configuration
- Story 1.2 → Pre-commit hooks, CI/CD pipeline, quality gates
- Story 1.3 → OpenAPI specification, validation script
- Story 1.4 → Schema generation script, Pydantic models
- Story 1.5 → Operation registry generation, metadata extraction
- Story 1.6 → Embedding generation, sentence-transformers integration
- Story 1.7 → MCP server core, JSON-RPC handler, stdio transport
- Story 1.8 → search-ids tool, semantic search implementation
- Story 1.9 → get-id tool, operation documentation retrieval
- Story 1.10 → call-id tool, HTTP client, operation executor
- Story 1.11 → Multi-version support, API version selection

## Risks, Assumptions, Open Questions

**Risks:**

1. **Risk**: OpenAPI specification incompleteness or inaccuracies
   - **Impact**: Generated schemas may not match actual RabbitMQ API behavior
   - **Mitigation**: Validate against live RabbitMQ instance in integration tests. Manual review of critical operations. Cross-reference with official RabbitMQ documentation.
   - **Owner**: Story 1.3, 1.4

2. **Risk**: Sentence-transformers model size and download time
   - **Impact**: First-run experience degraded if model download takes >30 seconds
   - **Mitigation**: Document model download in README. Consider pre-bundling model in Phase 2. Cache model locally after first download.
   - **Owner**: Story 1.6

3. **Risk**: Semantic search quality with threshold=0.7
   - **Impact**: Users may get irrelevant results or miss relevant operations
   - **Mitigation**: Benchmark with representative queries. Tune threshold based on precision/recall metrics. Allow user-configurable threshold.
   - **Owner**: Story 1.8

4. **Risk**: MCP protocol version changes
   - **Impact**: Breaking changes in MCP spec could require server updates
   - **Mitigation**: Pin to MCP protocol version 2024-11-05. Monitor MCP spec changes. Version server independently.
   - **Owner**: Story 1.7

5. **Risk**: HTTP connection pool exhaustion under load
   - **Impact**: Operations fail with timeout when pool is full
   - **Mitigation**: Default 5 connections sufficient for MVP single-user use case. Make pool size configurable. Add pool monitoring in Epic 7.
   - **Owner**: Story 1.10

**Assumptions:**

1. **Assumption**: RabbitMQ Management API plugin is enabled
   - **Validation**: Document as prerequisite in README. Detect and error clearly if plugin not available.
   - **Impact if false**: HTTP operations fail with connection refused

2. **Assumption**: Users have Python 3.12+ available
   - **Validation**: pyproject.toml enforces >=3.12 requirement. Document in README.
   - **Impact if false**: Installation fails with clear error message

3. **Assumption**: Single-user, single-instance deployment for MVP
   - **Validation**: Stateless design enables multi-instance in Phase 2 if needed.
   - **Impact if false**: Performance targets may not hold under concurrent load

4. **Assumption**: English-only operation descriptions for semantic search
   - **Validation**: OpenAPI spec uses English. Multilingual support deferred to Phase 2 (Epic 14).
   - **Impact if false**: Non-English queries may have lower search quality

5. **Assumption**: JSON files sufficient for operation registry and embeddings (no database)
   - **Validation**: Performance targets validate <1ms lookup, <500ms load time.
   - **Impact if false**: Switch to sqlite-vec in Phase 2 (Epic 9) if performance degrades

**Open Questions:**

1. **Question**: Should we bundle sentence-transformers model with distribution?
   - **Decision Needed**: Before v1.0 release
   - **Options**: (A) Download on first run (current), (B) Bundle model (~90MB), (C) Offer both
   - **Recommendation**: Defer to Epic 8 (documentation), document download clearly

2. **Question**: How many API versions should we actively maintain?
   - **Decision Needed**: Story 1.11 implementation
   - **Options**: (A) Only latest (3.13), (B) Latest + LTS (3.12, 3.13), (C) All recent (3.11, 3.12, 3.13)
   - **Recommendation**: Start with (C) for maximum compatibility, deprecate old versions over time

3. **Question**: Should search-ids return confidence score to users?
   - **Decision Needed**: Story 1.8 implementation
   - **Options**: (A) Show score, (B) Hide score
   - **Recommendation**: Show score for transparency and debugging, helps users understand relevance

4. **Question**: What's the error recovery strategy when RabbitMQ is down?
   - **Decision Needed**: Story 1.10 implementation
   - **Options**: (A) Fail fast (current), (B) Retry with backoff, (C) Queue operations
   - **Recommendation**: Fail fast in Epic 1, add retry in Epic 2 (connection management)

5. **Question**: Should we validate vhost existence before every operation?
   - **Decision Needed**: Story 1.10 implementation
   - **Options**: (A) Pre-validate always, (B) Let RabbitMQ return 404, (C) Cache valid vhosts
   - **Recommendation**: Option (B) for Epic 1 (simpler), add pre-validation in Epic 3 (topology)

## Test Strategy Summary

**Test Levels:**

1. **Unit Tests (pytest):**
   - **Scope**: Individual functions, classes, modules in isolation
   - **Coverage Target**: >80% overall, >95% for critical paths (search, validation, execution)
   - **Test Files**: `tests/unit/test_*.py` mirroring `src/` structure
   - **Key Areas**:
     - Schema validation: Test Pydantic models with valid/invalid inputs
     - Semantic search: Test similarity calculation, result ranking, threshold filtering
     - Operation registry: Test lookup, metadata extraction, edge cases
     - Error handling: Test exception types, error codes, context propagation
     - Mocking: Mock HTTP client, file I/O, model loading for fast execution
   - **Execution Time**: <10 seconds for entire unit test suite

2. **Integration Tests (pytest + testcontainers):**
   - **Scope**: End-to-end workflows with real RabbitMQ instance
   - **Infrastructure**: Docker testcontainers for RabbitMQ (automatic start/stop)
   - **Test Files**: `tests/integration/test_*.py`
   - **Key Scenarios**:
     - MCP server startup: Load registry, embeddings, start stdio listener
     - search-ids → get-id → call-id: Complete discovery flow
     - HTTP client: Connection pooling, timeout handling, TLS
     - Multi-version: Load different OpenAPI versions
     - Error scenarios: Invalid credentials, network failures, timeouts
   - **Execution Time**: <60 seconds (includes container startup)

3. **Contract Tests (MCP Protocol Compliance):**
   - **Scope**: Validate MCP protocol implementation against specification
   - **Test Files**: `tests/contract/test_mcp_protocol.py`
   - **Key Validations**:
     - JSON-RPC 2.0 message format (request/response structure)
     - MCP protocol methods (initialize, tools/list, tools/call)
     - Tool schema compliance (inputSchema as JSON Schema)
     - Error code correctness (-32700, -32600, -32601, -32602)
     - Stdio transport behavior (stdin/stdout, no stderr leaks)
   - **Coverage Target**: 100% of MCP protocol surface area
   - **Execution Time**: <5 seconds

4. **Performance Tests (pytest-benchmark):**
   - **Scope**: Validate latency and throughput targets from NFRs
   - **Test Files**: `tests/performance/test_*.py`
   - **Key Metrics**:
     - search-ids latency: <100ms p95, <150ms p99
     - get-id latency: <50ms p95
     - call-id latency: <200ms p95 (with mock RabbitMQ for consistency)
     - Embedding load time: <500ms
     - Registry lookup time: <1ms
     - Server startup time: <1 second
   - **Execution**: Repeated runs (n=100) with statistical analysis
   - **Reporting**: p50, p95, p99 latencies with pass/fail thresholds

**Test Data & Fixtures:**

- **Mock OpenAPI Spec**: Subset of real spec (~20 operations) for fast unit tests
- **Mock Embeddings**: Pre-computed vectors for 20 mock operations
- **Mock RabbitMQ Responses**: JSON files with sample API responses
- **Test RabbitMQ**: Testcontainers with pre-seeded queues/exchanges for integration
- **Pytest Fixtures**: Reusable setup for HTTP client, operation registry, semantic search

**CI/CD Integration:**

- **GitHub Actions Workflow** (`.github/workflows/ci.yml`):
  - Trigger: Pull requests, main branch commits
  - Matrix: Python 3.12, Python 3.13
  - Steps:
    1. Checkout code
    2. Setup Python with uv
    3. Install dependencies (uv sync)
    4. Run unit tests (pytest tests/unit/)
    5. Run contract tests (pytest tests/contract/)
    6. Run integration tests (pytest tests/integration/)
    7. Generate coverage report (pytest-cov)
    8. Upload coverage to Codecov
    9. Run type checking (mypy --strict src/)
    10. Run linting (ruff check src/)
  - Success Criteria: All tests pass, coverage >80%, no type/lint errors

**Edge Cases & Error Scenarios:**

- Empty search results (all similarity scores <0.7)
- Invalid operation IDs (non-existent in registry)
- Malformed parameters (wrong types, missing required fields)
- RabbitMQ connection failures (refused, timeout, auth failure)
- HTTP errors (404, 401, 500, network errors)
- Concurrent requests (connection pool behavior)
- Large responses (>10MB, ensure no memory issues)
- Startup failures (missing files, corrupted data)

**Test Coverage Blind Spots (Deferred to Later Epics):**

- AMQP operations (Epic 4): Only HTTP operations tested in Epic 1
- Connection auto-reconnection (Epic 2): Only fail-fast tested in Epic 1
- Comprehensive logging (Epic 7): Only foundation logging tested
- Rate limiting (Epic 7): Not implemented in Epic 1
- Security testing (Epic 15): Basic auth only, no penetration testing
- Load/stress testing (Epic 15): Single-user performance only
- Chaos engineering (Epic 15): No resilience testing under failures
