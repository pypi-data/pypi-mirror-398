# Developer Tool Specific Requirements

## API/Backend Architecture

**OpenAPI-Driven Code Generation Pipeline**:

The architecture philosophy centers on a **single source of truth** approach—the OpenAPI specification (`rabbitmq-http-api-openapi.yaml`) drives all code generation at build time, ensuring consistency and eliminating runtime overhead.

**Pipeline Stages**:

1. **OpenAPI Specification (Source of Truth)**
   - Location: `.specify/memory/rabbitmq-http-api-openapi.yaml`
   - Content: 4800+ lines defining all RabbitMQ Management API operations
   - Components: Operations (paths), Schemas (components), Parameters, Responses

2. **Schema Generation (Build-Time)**
   - Script: `python scripts/generate_schemas.py`
   - Output: `src/schemas/generated_schemas.py`
   - Process: Pydantic models from `components.schemas`
   - Result: Type-safe request/response validation schemas

3. **Embeddings Generation (Build-Time)**
   - Script: `python scripts/generate_embeddings.py`
   - Output: `data/embeddings.json`
   - Process: Semantic vectors from operation descriptions
   - Model: `sentence-transformers/all-mpnet-base-v2`
   - Performance: Pre-computed for <100ms search

4. **Operation Registry Generation (Build-Time)**
   - Script: `python scripts/extract_operations.py`
   - Output: `data/operations.json`
   - Content: Operation IDs mapped to HTTP methods, paths, parameters, documentation

5. **Runtime Execution (Zero Generation Overhead)**
   - Load pre-generated artifacts from disk
   - Instant server startup (<1 second)
   - Semantic search uses pre-computed embeddings
   - Operation execution uses pre-validated schemas

**Generation Triggers**:
- OpenAPI file modified (manual detection or file watchers)
- Manual invocation by developer
- Initial repository setup (first-time clone)
- CI/CD validation (verifies artifacts are synchronized, does NOT regenerate)

**Artifact Management**:
- All generated files committed to version control
- Portable across platforms (no external database dependencies)
- Validated in CI pipeline
- No runtime generation required

**Key Benefits**:
- Performance: <100ms semantic search, <1s server startup
- Reliability: Build-time errors caught before deployment
- Consistency: Single source of truth eliminates drift
- Maintainability: OpenAPI changes propagate automatically
- Developer Experience: Type-safe operations with IDE autocomplete

## MCP Protocol Integration

**Three-Tool Semantic Discovery Pattern**:

Instead of exposing 100+ individual MCP tools (one per RabbitMQ operation), we implement a semantic discovery interface with exactly 3 tools:

1. **`search-ids` Tool** (Operation Discovery)
   - Input: Natural language query (e.g., "list slow queues")
   - Process: Generate embedding → vector similarity search (threshold ≥0.7)
   - Output: Ranked list of relevant operation IDs with similarity scores
   - Performance: <100ms latency (p95)

2. **`get-id` Tool** (Operation Documentation)
   - Input: Operation ID (e.g., "queues.list")
   - Process: Query operation registry for complete metadata
   - Output: Full schema, parameters, descriptions, examples
   - Performance: <50ms latency

3. **`call-id` Tool** (Operation Execution)
   - Input: Operation ID + parameters (JSON object)
   - Process: Validate parameters → execute HTTP/AMQP call → return result
   - Output: Operation result or structured error
   - Performance: <200ms for HTTP operations, <50ms for AMQP

**JSON-RPC 2.0 Compliance**:
- All requests/responses follow MCP specification
- Standard error codes: -32600 (invalid request), -32601 (method not found), -32602 (invalid params), -32603 (internal error), -32700 (parse error)
- Stdio transport for AI assistant integration

**Rate Limiting**:
- 100 requests/minute per client (configurable via `RATE_LIMIT_RPM`)
- Client identification: MCP connection ID → IP address → global limit
- Exceeded limits return HTTP 429 with `Retry-After` header
- Rejection latency <5ms

## Authentication & Security

**RabbitMQ Credentials**:
- Username/password authentication via Management API
- TLS/SSL support with certificate verification
- Environment variables: `AMQP_HOST`, `AMQP_PORT`, `AMQP_USER`, `AMQP_PASSWORD`, `AMQP_VHOST`
- Configuration precedence: CLI args > env vars > TOML config > defaults

**Automatic Credential Sanitization**:
- All passwords/tokens/API keys automatically redacted from logs
- Regex patterns detect sensitive data in multiple formats
- Replacement: `password=[REDACTED]`, `token=[REDACTED]`, `Authorization: [REDACTED]`
- 100% automated (not optional)—security by default

**Audit Trail**:
- Every operation logged with correlation ID
- Structured JSON logs include: timestamp, user, operation, vhost, resource, result
- Correlation IDs link all log entries for complete traceability
- Log retention minimum 30 days (configurable)

**Secure Defaults**:
- Log file permissions: 600 (files), 700 (directories) on Unix
- Sensitive data truncation: messages >100KB truncated
- No credential exposure in error messages
- Multi-line stack traces escaped as single JSON strings

## CLI Interface Design

**Command Structure**:
```
rabbitmq-mcp-server <resource> <operation> [options]
```

**Resource Types**:
- `queue` - Queue management operations
- `exchange` - Exchange management operations
- `binding` - Binding management operations
- `message` - Message publish/consume operations
- `connection` - Connection and health check operations

**Common Options**:
- `--host` - RabbitMQ host (default: localhost)
- `--port` - RabbitMQ port (default: 5672 for AMQP, 15672 for HTTP)
- `--user` - Username (default: guest)
- `--password` - Password (default: guest)
- `--vhost` - Virtual host (default: /)
- `--format` - Output format: table (default), json
- `--insecure` - Disable TLS certificate verification (for self-signed certs)

**Output Formatting**:
- Human-readable: Rich tables with colors, column ordering (Identity → Config → Metrics)
- Machine-readable: JSON via `--format=json`
- Exit codes: 0 (success), non-zero (error)

**Help System**:
- Integrated help via `--help` for all commands and subcommands
- Examples included in help text
- Discoverable without external documentation

## Data Schemas & Validation

**Operation Entity** (Core data model):
```python
class Operation(BaseModel):
    operation_id: str  # Format: "{namespace}.{resource}.{action}"
    namespace: str  # Logical category from OpenAPI tag
    http_method: str  # GET, POST, PUT, DELETE, PATCH
    url_path: str  # URL template (e.g., "/api/queues/{vhost}/{name}")
    description: str  # Human-readable description
    parameters: Dict[str, ParameterSchema]  # Parameter definitions
    request_schema: Optional[Dict[str, Any]]  # Request body schema
    response_schema: Optional[Dict[str, Any]]  # Response schema
    examples: Optional[List[Dict[str, Any]]]  # Example requests/responses
    tags: List[str]  # OpenAPI tags
    requires_auth: bool = True
    rate_limit_exempt: bool = False
```

**AMQP Operation Schemas** (Manually maintained):
- `amqp.publish` - Publish message to exchange
- `amqp.consume` - Subscribe to queue
- `amqp.ack` - Acknowledge message
- `amqp.nack` - Negative acknowledge with requeue
- `amqp.reject` - Reject message (send to DLX)

**Parameter Validation**:
- Pydantic models validate all inputs before execution
- Validation errors list specific missing/invalid fields (<10ms overhead)
- Queue names: alphanumeric, hyphen, underscore, period; max 255 chars
- Exchange names: same rules as queues
- Routing keys: topic wildcards (* and #) supported

---
