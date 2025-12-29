# Non-Functional Requirements

## Performance

**Latency Requirements** (Traced to Story Acceptance Criteria):
- Semantic search: <100ms (p95), <150ms (p99) → **Story 1.8**: Search completes in <100ms
- Operation documentation retrieval: <50ms (p95) → **Story 1.9**: Retrieval completes in <50ms
- Operation execution: <200ms for HTTP operations (p95) → **Story 1.10**: Operations complete in <200ms (p95)
- AMQP operations: <50ms for publish/consume (p95) → **Stories 4.1, 4.2**: Publish <100ms, consume delivery latency <50ms
- Health checks: <1 second (p95) → **Story 2.4**: Health checks complete in <1 second
- Logging overhead: <5ms per operation → **Story 7.6**: Logging completes in <5ms overhead
- Rate limit rejection: <5ms → **Story 7.9**: Rate limit rejection latency <5ms

**Throughput Requirements** (Traced to Story Acceptance Criteria):
- Message publishing: 1000+ messages/minute → **Story 4.1**: FR-011 requires 1000+ msg/min
- Message consumption: 1000+ messages/minute → **Story 4.2**: FR-012 requires 1000+ msg/min, 100+ concurrent consumers
- Logging throughput: 1000 logs/second minimum → **Story 7.6**: FR-016 requires 1000 logs/second

**Resource Constraints** (Traced to Story Acceptance Criteria):
- Memory usage: <1GB per instance under normal load
- Server startup time: <1 second → **Story 1.7**: Server startup completes in <1 second
- Connection establishment: <5 seconds to available RabbitMQ → **Story 2.2**: FR-006 requires <5 seconds
- Auto-reconnection: <10 seconds after server recovery → **Story 2.5**: FR-007 requires <10 seconds

## Security

**Authentication**:
- RabbitMQ Management API: Username/password authentication
- AMQP protocol: Username/password authentication
- TLS/SSL support with certificate verification (configurable)
- No credential storage in plaintext (environment variables or secure config)

**Credential Protection**:
- 100% automatic sanitization in logs and error messages
- Regex patterns detect: passwords, tokens, API keys, authorization headers
- Stack traces sanitized before logging
- Connection strings sanitized (e.g., `amqp://user:password@host` → `amqp://[REDACTED]@host`)

**Audit & Compliance**:
- Complete audit trail for all operations
- Correlation IDs enable end-to-end tracing
- Structured JSON logs enable automated analysis
- Log retention minimum 30 days (configurable for compliance requirements)
- Secure file permissions (600/700) on Unix systems

**Network Security**:
- TLS/SSL support for Management API connections
- Certificate verification enabled by default (--insecure flag for self-signed)
- No plaintext credential transmission when TLS enabled

## Scalability

**Horizontal Scaling**:
- Stateless design enables multiple instances
- Connection pooling (default 5 connections, configurable)
- Rate limiting per client (not global)
- No shared state between instances

**Data Volume Handling**:
- System handles 1000+ queues without performance degradation
- System handles 1000+ exchanges without performance degradation
- Vector search efficient with 100+ operations
- Log file rotation prevents unbounded disk usage

**Concurrent Operations**:
- Thread-safe cache access using asyncio.Lock
- 100+ concurrent consumers supported
- Connection pool blocks when full (10s timeout, configurable)

## Accessibility

**Developer Experience**:
- Natural language operation discovery (no memorization required)
- Clear error messages with corrective actions
- Comprehensive help system (`--help` on all commands)
- Examples included in documentation and help text
- Type-safe operations with IDE autocomplete (Pydantic models)

**Internationalization** (Future):
- English only in MVP
- Phase 2: Multi-language support for console client
- Log messages remain English for tooling compatibility

## Integration

**AI Assistant Compatibility**:
- MCP protocol stdio transport (Claude, ChatGPT, custom clients)
- JSON-RPC 2.0 compliance
- Tested with multiple MCP clients
- Clear protocol documentation

**RabbitMQ Compatibility**:
- Management API plugin required (standard in most installations)
- AMQP 0-9-1 protocol support
- Multi-vhost support
- Works with RabbitMQ 3.11.x, 3.12.x, 3.13.x

**Observability Integrations**:
- OpenTelemetry with OTLP exporter
- Optional Jaeger/Prometheus exporters
- Structured JSON logs (ELK, Splunk, CloudWatch compatible)
- Standard log formats for aggregation pipelines

**Development Tools**:
- Python 3.12+ required
- pytest for testing
- Docker/testcontainers for integration tests
- pre-commit hooks (black, isort, mypy, pylint)
- CI/CD via GitHub Actions

---
