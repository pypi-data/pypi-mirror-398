# Epic 7: Structured Logging & Observability

**Goal**: Implement production-grade structured logging with automatic sensitive data sanitization, correlation ID tracking, observability instrumentation, and security compliance features.

**Value**: Enables enterprise adoption with audit trails, security compliance (no credential leaks), debugging capabilities, and operational visibility required for production deployments. This is the **production security by default** differentiator realized.

**Product Differentiator**: 100% automatic credential sanitization - security teams approve immediately because sensitive data redaction is automatic, not optional. Zero credential leaks, ever.

**Covered FRs**: FR-014, FR-015, FR-016, FR-017, FR-019, FR-020

---

## Story 7.1: Structured Logging Foundation - structlog Integration

As a developer,
I want structured JSON logging using structlog with consistent schema and log levels,
So that all logs are machine-parsable, searchable, and compatible with log aggregation systems.

**Acceptance Criteria:**

**Given** application code that logs events
**When** logs are written
**Then** all logs are JSON-formatted with consistent schema: {"timestamp": "2025-11-16T10:30:00Z", "level": "INFO", "event": "operation_executed", "correlation_id": "uuid", "operation": "queues.list", "duration_ms": 45, ...}

**And** log levels supported: ERROR, WARN, INFO, DEBUG with configurable minimum level via LOG_LEVEL environment variable

**And** structured fields automatically added: timestamp (ISO 8601), level, event (message), logger_name, thread_id, process_id

**And** custom context fields supported: operation, vhost, queue, exchange, user, duration_ms, status

**And** logger creation is simple: logger = structlog.get_logger(__name__)

**And** logging calls are structured: logger.info("operation_executed", operation="queues.list", duration_ms=45)

**And** JSON output format: one log entry per line (newline-delimited JSON)

**Prerequisites:** Story 1.1 (project setup)

**Technical Notes:**
- Use structlog library: `uv add structlog`
- Configure processors in src/logging/config.py:
  - structlog.stdlib.add_log_level
  - structlog.processors.TimeStamper(fmt="iso")
  - structlog.processors.StackInfoRenderer()
  - structlog.processors.format_exc_info
  - structlog.processors.JSONRenderer()
- Processor chain: add_log_level → TimeStamper → StackInfoRenderer → format_exc_info → JSONRenderer
- Logger initialization: structlog.configure(processors=[...], wrapper_class=structlog.stdlib.BoundLogger, context_class=dict, logger_factory=structlog.stdlib.LoggerFactory())
- Development mode: use ConsoleRenderer for pretty-printed logs (configure via LOG_FORMAT=console environment variable)

---

## Story 7.2: Structured Logging Configuration & Output

As a developer,
I want configurable log output destinations (file, console) with environment-based configuration,
So that logging behavior adapts to different environments (development, production) without code changes.

**Acceptance Criteria:**

**Given** structured logging is configured (Story 7.1)
**When** application starts
**Then** logs are written to file: ./logs/rabbitmq-mcp-{date}.log

**And** console output is configurable via LOG_TO_CONSOLE environment variable (true/false, default: false in production)

**And** console output format in development: human-readable pretty-printed logs (not JSON)

**And** console output format in production: JSON format (same as file output)

**And** logging configuration via environment variables: LOG_LEVEL (DEBUG/INFO/WARN/ERROR, default: INFO), LOG_FILE_PATH (default: ./logs/rabbitmq-mcp.log), LOG_TO_CONSOLE (true/false, default: false), LOG_FORMAT (json/console, default: json)

**And** logs directory ./logs/ is created automatically if it doesn't exist

**And** configuration validation: invalid LOG_LEVEL values log warning and default to INFO

**Prerequisites:** Story 7.1 (structlog integration)

**Technical Notes:**
- Configuration in logging_config.yaml or via environment variables (environment takes precedence)
- Create logs directory: os.makedirs('./logs', mode=0o700, exist_ok=True)
- File handler: logging.FileHandler(filename='./logs/rabbitmq-mcp.log')
- Console handler: logging.StreamHandler(sys.stdout) with conditional renderer (JSON or Console)
- Multiple outputs: configure structlog with multiple handlers (file + console)
- Development detection: check LOG_FORMAT or default based on presence of .env file
- Configuration loading: use python-dotenv for .env file support

---

## Story 7.3: Correlation ID Tracking

As a developer,
I want unique correlation IDs generated and propagated across all log entries for a single request,
So that I can trace complete request lifecycle from entry to exit, including all sub-operations.

**Acceptance Criteria:**

**Given** an incoming MCP request
**When** request is processed
**Then** a unique correlation ID is generated (UUID v4)

**And** correlation ID is attached to all log entries for this request: MCP tool call, RabbitMQ operation, HTTP requests, errors

**And** correlation ID flows through: MCP server → operation handler → HTTP client → AMQP client

**And** correlation ID is included in operation responses: {"status": "success", "correlation_id": "...", "result": {...}}

**And** correlation ID enables end-to-end tracing: search logs by correlation_id shows complete request flow

**And** nested operations (e.g., call-id triggers HTTP call) use same correlation ID

**And** correlation ID added to thread-local or async context for automatic propagation

**Prerequisites:** Story 7.2 (structured logging configuration)

**Technical Notes:**
- Generate correlation ID: import uuid; correlation_id = str(uuid.uuid4())
- Thread-local storage for synchronous code: threading.local()
- Context variables for async code: contextvars.ContextVar for async/await compatibility
- Context manager for correlation ID: with correlation_context(correlation_id): ...
- Structlog processor to bind correlation ID from context: custom processor reads from contextvars
- Pass correlation ID in HTTP headers: X-Correlation-ID (for external systems)
- Log correlation ID at entry: logger.info("request_received", correlation_id=correlation_id, method="tools/call")
- Log at exit: logger.info("request_completed", correlation_id=correlation_id, duration_ms=duration)
- Example log search: grep '"correlation_id": "abc-123"' logs/rabbitmq-mcp-2025-11-16.log

---

## Story 7.4: Automatic Sensitive Data Sanitization

As a security engineer,
I want automatic detection and redaction of sensitive data (passwords, tokens, API keys) in all logs,
So that credentials never leak into log files, preventing security breaches and compliance violations.

**Acceptance Criteria:**

**Given** log entries containing sensitive data
**When** logs are written
**Then** passwords are redacted: "password=secret123" → "password=[REDACTED]"

**And** tokens are redacted: "token=abc123xyz" → "token=[REDACTED]"

**And** API keys are redacted: "api_key=sk_live_xyz" → "api_key=[REDACTED]"

**And** Authorization headers are redacted: "Authorization: Bearer token" → "Authorization: [REDACTED]"

**And** connection strings are sanitized: "amqp://user:pass@host" → "amqp://[REDACTED]@host"

**And** redaction is automatic (not optional) - security by default

**And** redaction patterns configurable via regex: SENSITIVE_PATTERNS = [r'password[=:][\w]+', r'token[=:][\w]+', ...]

**And** redaction occurs before writing (not at read time)

**And** 100% credential detection (no false negatives) - validated via security tests

**Prerequisites:** Story 7.2 (structured logging configuration)

**Technical Notes:**
- Implement structlog processor: sanitize_sensitive_data (placed in processor chain before JSONRenderer)
- Regex patterns for detection (defined in src/logging/sanitization.py):
  - password: r'password[=:]\s*["\']?[^"\'\s]+["\']?'
  - token: r'token[=:]\s*["\']?[^"\'\s]+["\']?'
  - api_key: r'api[_-]?key[=:]\s*["\']?[^"\'\s]+["\']?'
  - Authorization header: r'Authorization:\s*Bearer\s+\S+'
  - connection strings: r'amqp://([^:]+):([^@]+)@' → r'amqp://[REDACTED]@'
- Replacement: pattern.sub(r'\1[REDACTED]', message)
- Apply to all log fields: event message, structured fields, exception stack traces
- Test with security test suite containing known sensitive strings
- Document patterns in docs/SECURITY.md

---

## Story 7.5: File-Based Logging with Daily Rotation

As a DevOps engineer,
I want logs written to files with daily rotation and size limits,
So that logs are persistent, searchable, and don't consume unbounded disk space.

**Acceptance Criteria:**

**Given** application is running and logging events
**When** logs are written to disk
**Then** log files created in ./logs/ directory with pattern: rabbitmq-mcp-{date}.log

**And** new log file created daily at midnight UTC

**And** log file rotation also triggered when file reaches 100MB (whichever comes first)

**And** rotated files renamed: rabbitmq-mcp-2025-11-15.log → rabbitmq-mcp-2025-11-15.log.1

**And** rotated files compressed: rabbitmq-mcp-2025-11-15.log.1 → rabbitmq-mcp-2025-11-15.log.1.gz

**And** log retention: files older than 30 days are automatically deleted (configurable via LOG_RETENTION_DAYS)

**And** file permissions: 600 (read/write for owner only) on Unix systems

**And** directory permissions: 700 (owner only) for ./logs/ directory

**And** disk space monitoring: warn if available disk space <1GB

**Prerequisites:** Story 7.2 (structured logging configuration)

**Technical Notes:**
- Use logging.handlers.TimedRotatingFileHandler for time-based rotation
- Dual rotation triggers: TimedRotatingFileHandler(when='midnight', interval=1, utc=True) + maxBytes check in custom handler
- File naming pattern: filename='./logs/rabbitmq-mcp.log', suffix='%Y-%m-%d.log'
- Compression: implement custom namer/rotator callbacks: handler.namer = lambda name: name + '.gz', handler.rotator = compress_file_func
- Retention cleanup: scheduled task using threading.Timer (runs daily) to delete files older than LOG_RETENTION_DAYS
- Secure permissions: os.chmod(log_file, 0o600) after creation (Unix), use platform checks for Windows
- Create logs directory with secure permissions: os.makedirs('./logs', mode=0o700, exist_ok=True)
- Configuration: LOG_FILE_PATH (default: ./logs/rabbitmq-mcp.log), LOG_MAX_BYTES (default: 100MB), LOG_RETENTION_DAYS (default: 30)

---

## Story 7.6: Logging Performance Optimization

As a developer,
I want logging overhead ≤5ms per operation even under high load,
So that logging doesn't degrade application performance or increase operation latency.

**Acceptance Criteria:**

**Given** application under normal load (100 operations/sec)
**When** logging performance is measured
**Then** logging overhead per operation is <5ms (p95)

**And** logging throughput is ≥1000 logs/second on reference hardware

**And** asynchronous logging is used for non-critical logs (INFO, DEBUG)

**And** synchronous logging is used for critical logs (ERROR, WARN) to ensure delivery

**And** log buffer size is configurable: 1000 entries default (flushes when full)

**And** buffer flush triggers: buffer full, periodic (every 5s), application shutdown

**And** buffer saturation (full) blocks writes (zero log loss - backpressure)

**And** performance degrades gracefully: logging slows operations rather than dropping logs

**And** logging performance metrics tracked: log_writes_per_sec, avg_log_duration_ms, buffer_saturation_count

**Prerequisites:** Story 7.2 (structured logging configuration)

**Technical Notes:**
- Use logging.handlers.QueueHandler with QueueListener for async logging
- Handler chain: QueueHandler (in main thread) → Queue (thread-safe) → QueueListener (background thread) → FileHandler (writes to disk)
- Queue configuration: queue.Queue(maxsize=1000) - blocks producers when full (backpressure for zero log loss)
- Flush strategies: periodic flush (threading.Timer every 5s), atexit.register for graceful shutdown flush
- Performance measurement: time.perf_counter() before/after log call in benchmark tests
- Benchmark test: log 10,000 entries sequentially, measure total time, calculate per-entry overhead (target: <5ms)
- Reference hardware documented in performance tests: 4-core CPU, 8GB RAM, SSD
- Trade-off consideration: async improves throughput but adds complexity (thread management, queue monitoring)

---

## Story 7.7: Audit Trail for Operations

As a compliance officer,
I want complete audit trail of all creation/deletion operations with metadata,
So that I can track who did what, when, and provide evidence for security audits and incident investigations.

**Acceptance Criteria:**

**Given** any creation or deletion operation (queue, exchange, binding)
**When** operation is executed
**Then** audit log entry is written with fields: timestamp, correlation_id, action (queue.create, queue.delete, etc.), vhost, resource_name (queue/exchange/binding name), user (authenticated username), result (success/failure), parameters (operation details)

**And** audit logs are distinct from operational logs: level="AUDIT" or separate file ./logs/rabbitmq-mcp-audit-{date}.log

**And** audit logs cannot be disabled (always logged regardless of LOG_LEVEL)

**And** audit logs include before/after state for modifications: deleted queue had messages=100, consumers=0

**And** audit retention is longer than operational logs: 90 days minimum (configurable via AUDIT_RETENTION_DAYS)

**And** audit log format is immutable (fields never removed, only added)

**And** audit logs support: compliance reporting, security investigations, incident forensics

**Prerequisites:** Story 7.2 (structured logging), Story 7.3 (correlation IDs), Story 3.1-3.11 (topology operations)

**Technical Notes:**
- Separate logger for audit: audit_logger = structlog.get_logger("audit")
- Audit-specific handler: logging.FileHandler('./logs/rabbitmq-mcp-audit.log')
- Audit log level: custom logging level "AUDIT" (level value 35, between WARNING and ERROR)
- Audit events to log: operation start, operation complete, validation failures, safety overrides (--force flag)
- Required fields: {timestamp, correlation_id, action, vhost, resource_type, resource_name, user, source_ip, result, error_message, parameters, before_state, after_state}
- Track forced operations: {action: "queue.delete", forced: true, reason: "safety override with --force flag"}
- Immutable format guarantee: never change or remove existing field names, only add new optional fields
- Compliance standards addressed: GDPR (data access audit), SOC 2 (access control audit), ISO 27001 (security event logging)

---

## Story 7.8: OpenTelemetry Instrumentation

As a platform engineer,
I want OpenTelemetry distributed tracing and metrics,
So that I can monitor application performance, identify bottlenecks, and integrate with observability platforms (Jaeger, Prometheus, Datadog).

**Acceptance Criteria:**

**Given** application with OpenTelemetry instrumentation
**When** operations are executed
**Then** distributed traces are generated with spans for: MCP tool call, RabbitMQ operation, HTTP request, AMQP operation

**And** each span includes: trace_id, span_id, parent_span_id, operation_name, start_time, duration, status, attributes

**And** trace_id matches correlation_id for log correlation

**And** traces exported via OTLP (OpenTelemetry Protocol) to configurable endpoint

**And** metrics collected: operation counters (queues.list_count), latency histograms (p50/p95/p99), error rates, cache hit/miss ratios

**And** metrics exported to Prometheus or OTLP endpoint

**And** 95%+ of operations generate complete traces (coverage target)

**And** instrumentation overhead <10ms per operation

**And** OpenTelemetry configuration via environment: OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME, OTEL_TRACES_SAMPLER (always_on, trace_id_ratio)

**Prerequisites:** Story 7.2 (structured logging), Story 7.3 (correlation IDs)

**Technical Notes:**
- Dependencies: `uv add opentelemetry-sdk opentelemetry-exporter-otlp`
- Initialize tracer provider: from opentelemetry import trace; provider = TracerProvider(); trace.set_tracer_provider(provider)
- Create tracer: tracer = trace.get_tracer(__name__, version="1.0.0")
- Create spans: with tracer.start_as_current_span("operation_name") as span: ...
- Span attributes: span.set_attribute("operation", "queues.list"), span.set_attribute("vhost", "/"), span.set_attribute("correlation_id", correlation_id)
- Link trace_id to correlation_id: use correlation_id as trace_id for log-trace correlation
- OTLP exporter configuration: OTLPSpanExporter(endpoint="http://localhost:4318") or configure via OTEL_EXPORTER_OTLP_ENDPOINT
- Metrics instrumentation: use opentelemetry.metrics with Counter (operation_count), Histogram (operation_duration), Gauge (active_connections)
- Sampling configuration: trace_id_ratio sampler (0.1 = 10% sampling) or always_on for development
- Integration examples: Jaeger (tracing UI), Prometheus (metrics scraping), Datadog (unified observability)

---

## Story 7.9: Rate Limiting Implementation

As a system administrator,
I want rate limiting to prevent abuse and protect RabbitMQ from overload,
So that single clients can't monopolize resources or degrade service for others.

**Acceptance Criteria:**

**Given** MCP server with rate limiting enabled
**When** client exceeds rate limit
**Then** requests are throttled: 100 requests/minute per client (configurable via RATE_LIMIT_RPM)

**And** client identification priority: (1) MCP connection ID, (2) IP address, (3) global limit

**And** exceeded limits return error: {"error": {"code": -32000, "message": "Rate limit exceeded. Retry after 30s."}, "retry_after": 30}

**And** HTTP-style response: status 429 (Too Many Requests) with Retry-After header (if applicable)

**And** rate limit rejection latency is <5ms (fast fail)

**And** rate limits reset: sliding window (e.g., last 60 seconds) or fixed window (per minute)

**And** rate limit status exposed: {"requests_remaining": 50, "reset_at": "2025-11-16T10:31:00Z"}

**And** rate limits configurable per operation type: higher limits for read operations (list), lower for write operations (create/delete)

**And** rate limiting logged: {event: "rate_limit_exceeded", client_id: "...", limit: 100, window: "60s"}

**Prerequisites:** Story 7.2 (structured logging), Story 1.7 (MCP server)

**Technical Notes:**
- Algorithm choice: sliding window for fairness (no burst allowance) vs fixed window for simplicity
- Libraries: aiolimiter for async rate limiting (compatible with MCP server async architecture)
- Storage: in-memory dict for single instance, structure: {client_id: [(timestamp1, timestamp2, ...)]}
- Client identification priority: (1) MCP connection unique ID (from MCP protocol), (2) IP address from environment variables, (3) global fallback
- Sliding window implementation: track timestamps of last N requests, on new request check if count in last 60s exceeds limit
- Fixed window alternative: simpler but allows burst edge case (100 requests at 12:00:59, 100 at 12:01:00)
- Per-operation rate limits: RATE_LIMIT_READ_RPM=200 (queries), RATE_LIMIT_WRITE_RPM=50 (mutations), RATE_LIMIT_DEFAULT_RPM=100
- Exemptions: operations with rate_limit_exempt=true in operation registry (health checks, metrics)
- Monitoring metrics: rate_limit_exceeded_count (counter), clients_throttled (gauge), requests_per_client (histogram)

---

## Story 7.10: Security Logging & Monitoring

As a security engineer,
I want security-specific logging for authentication failures, unauthorized access, and suspicious activity,
So that I can detect and respond to security threats quickly.

**Acceptance Criteria:**

**Given** application handling authentication and authorization
**When** security events occur
**Then** authentication failures are logged: {event: "auth_failure", user: "...", reason: "invalid_password", source_ip: "..."}

**And** unauthorized access attempts logged: {event: "unauthorized_access", user: "...", attempted_operation: "queue.delete", resource: "production-queue"}

**And** suspicious patterns logged: {event: "suspicious_activity", pattern: "rapid_failed_logins", user: "...", count: 10, window: "60s"}

**And** credential changes logged: {event: "credential_change", user: "...", action: "password_updated"}

**And** security logs are high priority (ERROR or SECURITY level)

**And** security logs trigger alerts for: multiple auth failures (>5 in 10 minutes), unauthorized access, privilege escalation attempts

**And** security logs include: timestamp, correlation_id, event, user, source_ip, user_agent, resource, action, result, reason

**And** security monitoring dashboard tracks: failed_auth_count, unauthorized_access_count, suspicious_activity_alerts

**Prerequisites:** Story 7.2 (structured logging), Story 7.7 (audit trail)

**Technical Notes:**
- Dedicated security logger: security_logger = structlog.get_logger("security")
- Security log file: ./logs/rabbitmq-mcp-security-{date}.log (separate from operational logs)
- Security log retention: 90 days minimum (configurable via SECURITY_LOG_RETENTION_DAYS, default: 90)
- SIEM integration: ship security logs to Splunk (HTTP Event Collector), ELK (Filebeat), Datadog (agent)
- Pattern detection: implement SecurityMonitor class tracking failed login attempts, detecting brute force (threshold: >10 failures/minute from single IP)
- IP logging: log source IP for all authentication events, failed operations, suspicious activity
- User behavior analytics: track operation patterns per user (baseline: operations in last 30 days, alert on anomalies)
- Compliance requirements: GDPR (Article 32 - security logging), SOC 2 (CC6.1 - logical access), ISO 27001 (A.12.4 - logging and monitoring)

---

## Story 7.11: Log Aggregation & Search

As a DevOps engineer,
I want log aggregation and search capabilities,
So that I can quickly find relevant logs during troubleshooting without manually grep-ing files.

**Acceptance Criteria:**

**Given** structured JSON logs in files
**When** I query logs
**Then** logs are searchable by: correlation_id, timestamp range, log level, operation, vhost, user, error message

**And** search returns results in <1 second for typical queries (last 24 hours)

**And** search supports: exact match, regex patterns, field filters, time range

**And** search results are formatted: human-readable table or JSON output

**And** common queries documented: "Find all errors in last hour", "Trace request by correlation_id", "List all queue deletions by user"

**And** log aggregation integration: ship logs to ELK (Elasticsearch/Logstash/Kibana), Splunk, CloudWatch, or Datadog

**And** logs are parsable: JSON format, one entry per line (newline-delimited)

**And** integration examples provided: Filebeat config, Fluentd config, CloudWatch agent config

**Prerequisites:** Story 7.2 (structured logging), Story 7.5 (file-based logging)

**Technical Notes:**
- Local search using jq: cat logs/*.log | jq 'select(.correlation_id == "abc")' or jq 'select(.level == "ERROR" and (.timestamp | fromdateiso8601) > (now - 3600))'
- CLI search tool: rabbitmq-mcp-server logs search --correlation-id=abc --level=ERROR --since="1 hour ago" --operation="queues.delete"
- Log shipping options:
  - Filebeat: configure input (./logs/*.log), output (Elasticsearch), processors (JSON parsing)
  - Fluentd: configure tail plugin for log files, output to Elasticsearch/Splunk
  - CloudWatch agent: configure log group, log stream, JSON format parsing
- Elasticsearch integration: index pattern rabbitmq-mcp-*, mappings for timestamp (date), level (keyword), operation (keyword)
- Kibana dashboards: operation latency histogram, error rate over time, top 10 operations (by count), user activity heatmap
- Splunk queries: index="rabbitmq-mcp" | stats count by operation | sort -count | head 10
- CloudWatch Insights queries: fields @timestamp, @message, correlation_id, operation | filter level="ERROR" | sort @timestamp desc
- Document integration: create docs/LOGGING.md with setup instructions for each log aggregation system

---
