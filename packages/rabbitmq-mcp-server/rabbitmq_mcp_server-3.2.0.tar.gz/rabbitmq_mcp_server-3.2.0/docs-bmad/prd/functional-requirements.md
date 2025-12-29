# Functional Requirements

## Core Capabilities (Comprehensive FR List)

**FR-001: MCP Protocol Foundation**
- System MUST expose exactly 3 public MCP tools: `search-ids`, `get-id`, `call-id`
- All operations and schemas MUST derive from single OpenAPI specification
- Parameter validation MUST occur before RabbitMQ execution
- Error codes MUST follow JSON-RPC 2.0 standards

**FR-002: Semantic Search**
- Search MUST use sentence-transformers model `all-MiniLM-L6-v2` (384 dimensions)
- Similarity threshold MUST be ≥0.7 to return results
- Search latency MUST be <100ms (95th percentile)
- Results MUST be ordered by similarity score descending
- Zero results (all scores <0.7) MUST return empty list with suggestion

**FR-003: Operation Documentation**
- `get-id` tool MUST return complete parameter schemas with types and descriptions
- Operation details MUST include examples when available
- Response latency MUST be <50ms
- Invalid operation IDs MUST return clear error indicating non-existence

**FR-004: Operation Execution**
- `call-id` tool MUST validate parameters against Pydantic schema before execution
- Validation errors MUST list specific missing/invalid fields with expected formats
- Operations MUST complete in <200ms under normal conditions (p95)
- Operations exceeding 30-second timeout MUST be aborted with descriptive error
- Connection failures MUST return immediately without retry (fail-fast pattern)

**FR-006: Connection Management**
- AMQP 0-9-1 protocol MUST be used for RabbitMQ connection
- Configuration MUST load from: CLI args > env vars > TOML > defaults
- Connection establishment MUST complete in <5 seconds when server available
- Connection timeout MUST be 30 seconds
- Health check MUST complete in <1 second and return connection state

**FR-007: Auto-Reconnection**
- Reconnection MUST be automatic with exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, then 60s max
- Infinite retries MUST continue until connection restored
- Successful reconnection MUST complete in <10 seconds when server returns
- Connection state MUST be monitored in real-time (connected, disconnected, reconnecting)

**FR-008: Queue Operations**
- System MUST support list, create, delete, purge operations for queues
- Queue statistics MUST include: messages, messages_ready, messages_unacknowledged, consumers, memory
- Queue deletion MUST validate: messages=0 AND consumers=0 before allowing (unless --force)
- Queue names MUST be validated: alphanumeric, hyphen, underscore, period; max 255 chars

**FR-009: Exchange Operations**
- System MUST support list, create, delete operations for exchanges
- Supported exchange types: direct, topic, fanout, headers
- System exchanges (amq.* prefix) and default exchange ("") MUST be protected from deletion
- Exchange deletion MUST block if active bindings exist

**FR-010: Binding Operations**
- System MUST support list, create, delete operations for bindings
- Binding creation MUST validate exchange existence first, then queue existence
- Topic exchange bindings MUST support wildcard patterns (* and #)
- Duplicate bindings MUST be prevented (same exchange, queue, routing key)

**FR-005: AMQP Protocol Operations**
- System MUST support message publishing via AMQP with exchange, routing key, properties
- System MUST support message consumption with prefetch limits and acknowledgment modes
- System MUST support ack, nack, reject operations with delivery tag validation
- AMQP operations MUST have manually maintained Pydantic schemas

**FR-011: Message Publishing**
- System MUST support publishing to exchanges with routing keys
- Payload types supported: JSON, plain text, binary data
- Message properties MUST be configurable: headers, content-type, correlation ID, delivery mode
- Exchange existence MUST be validated before publishing
- Publish operations MUST complete in <100ms

**FR-012: Message Consumption**
- System MUST support queue subscription with real-time delivery
- Prefetch limit MUST be configurable (default: 10 messages)
- Consumption latency MUST remain <50ms per message
- System MUST support at least 100 concurrent consumers
- Throughput MUST be at least 1000 messages per minute

**FR-013: Message Acknowledgment**
- System MUST support ack (positive acknowledgment)
- System MUST support nack with requeue option
- System MUST support reject (send to DLX if configured)
- Duplicate acknowledgments MUST be prevented
- Delivery tags MUST be validated before acknowledgment

**FR-014: Structured Logging**
- All logs MUST be structured JSON format with consistent schema
- Log levels supported: ERROR, WARN, INFO, DEBUG
- Logs MUST write to files in `./logs/` directory with pattern `rabbitmq-mcp-{date}.log`
- Sensitive data (passwords, tokens, API keys) MUST be automatically redacted
- Unique correlation IDs MUST be generated and propagated across all log entries

**FR-015: Log Rotation & Retention**
- Log files MUST rotate based on dual triggers: (1) daily at midnight UTC, (2) when reaching 100MB
- Logs MUST be retained minimum 30 days (configurable)
- Rotated log files MUST be compressed using gzip
- Secure file permissions (600 files, 700 directories) MUST be attempted

**FR-016: Logging Performance**
- Logging operations MUST complete in <5ms overhead per operation
- Asynchronous logging MUST be supported for high throughput
- Minimum throughput: 1000 logs/second on reference hardware (4-core CPU, 8GB RAM, SSD)
- Buffer saturation MUST block writes (zero log loss)

**FR-017: Audit Trail**
- All creation/deletion operations MUST be logged for audit
- Audit logs MUST include: timestamp, correlation_id, operation, vhost, resource_name, user, result
- Complete operation lifecycle MUST be traceable through correlation IDs

**FR-018: Testing Framework**
- Unit tests MUST cover all critical components with >80% coverage
- Integration tests MUST use real RabbitMQ instance
- Contract tests MUST validate MCP protocol compliance (100% coverage)
- Performance tests MUST measure latency and throughput
- Complete test suite MUST execute in <5 minutes

**FR-019: Observability**
- OpenTelemetry instrumentation MUST be implemented with OTLP exporter
- Distributed traces MUST cover 100% of operations with correlation IDs
- Metrics MUST include: request counters, latency histograms (p50/p95/p99), cache hit/miss ratios
- 95% of operations MUST generate complete traces

**FR-020: Rate Limiting**
- Rate limiting MUST be 100 requests/minute per client (configurable)
- Client identification priority: (1) MCP connection ID, (2) IP address, (3) global limit
- Exceeded limits MUST return HTTP 429 with Retry-After header
- Rate limit rejection latency MUST be <5ms

**FR-021: Multi-Version Support**
- System MUST support one OpenAPI version per deployment
- Version selectable via `RABBITMQ_API_VERSION` environment variable
- Supported versions: 3.11.x (legacy), 3.12.x (LTS), 3.13.x (latest)
- Invalid version MUST return error listing supported versions

**FR-022: CLI Interface**
- CLI syntax MUST follow: `<command> <subcommand> <options>`
- Credentials MUST be accepted via CLI arguments or environment variables
- TLS/SSL connections MUST be supported with certificate verification
- Output MUST be formatted for humans (tables) with optional JSON via `--format` flag
- Exit codes: 0 for success, non-zero for errors

**FR-023: Safety Validations**
- Queue deletion MUST block if messages=0 OR consumers=0 not both true (unless --force)
- Exchange deletion MUST block if active bindings exist
- Virtual host existence MUST be validated before topology operations
- All validation failures MUST return structured errors with corrective actions

---
