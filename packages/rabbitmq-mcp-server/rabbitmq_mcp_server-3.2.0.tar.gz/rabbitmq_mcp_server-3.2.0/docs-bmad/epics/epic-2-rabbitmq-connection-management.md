# Epic 2: RabbitMQ Connection Management

**Goal**: Implement robust RabbitMQ connection handling with configuration management, health monitoring, and automatic reconnection with exponential backoff for production reliability.

**Value**: Ensures the MCP server maintains stable connections to RabbitMQ even in unstable network conditions, preventing operation failures and enabling seamless recovery from connection disruptions. Delivers **production-ready infrastructure automation** through enterprise-grade reliability.

**Product Differentiator**: Production security by default - automatic credential sanitization, secure configuration management, and audit trails make this enterprise-ready from day 1.

**Covered FRs**: FR-006, FR-007

---

## Story 2.1: Configuration Management System

As a developer,
I want flexible configuration loading from multiple sources (CLI args, environment variables, TOML files, defaults),
So that I can easily configure RabbitMQ connection parameters for different environments without code changes.

**Acceptance Criteria:**

**Given** multiple configuration sources are available
**When** the server starts
**Then** configuration is loaded with precedence: CLI args > environment variables > TOML config file > built-in defaults

**And** supported parameters include: AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASSWORD, AMQP_VHOST, AMQP_USE_TLS, AMQP_VERIFY_CERT, HTTP_HOST, HTTP_PORT, HTTP_USER, HTTP_PASSWORD, HTTP_USE_TLS

**And** TOML config file location: `./config/config.toml` or path from `CONFIG_FILE` env var

**And** sensitive values (passwords) are never logged in plaintext

**And** configuration validation occurs at startup with clear error messages for invalid values

**And** missing required parameters return error: "Required parameter 'AMQP_HOST' not configured"

**And** config loading completes in <100ms

**Prerequisites:** Story 1.1 (project setup)

**Technical Notes:**
- Use tomli library for TOML parsing (Python 3.11+ has tomllib built-in)
- Config class uses Pydantic BaseSettings for validation
- Example config.toml.example provided in repository
- Support both AMQP (5672) and Management API (15672) configurations
- Document all configuration options in README.md
- CI/CD tests various configuration scenarios

---

## Story 2.2: AMQP Connection Establishment

As a developer,
I want to establish AMQP 0-9-1 protocol connection to RabbitMQ,
So that I can publish and consume messages for messaging operations.

**Acceptance Criteria:**

**Given** valid RabbitMQ connection configuration
**When** the server establishes AMQP connection
**Then** connection succeeds within 5 seconds when RabbitMQ is available

**And** connection uses pika library with AMQP 0-9-1 protocol

**And** authentication uses configured username and password

**And** connection targets configured vhost (default: "/")

**And** TLS/SSL is enabled if AMQP_USE_TLS=true with certificate verification based on AMQP_VERIFY_CERT

**And** connection failures return immediate error: "Failed to connect to RabbitMQ at {host}:{port}: {error_details}"

**And** connection timeout is 30 seconds (configurable)

**And** successful connection logs: "Connected to RabbitMQ at {host}:{port} vhost={vhost}"

**Prerequisites:** Story 2.1 (configuration management)

**Technical Notes:**
- Use pika.BlockingConnection or pika.SelectConnection for async
- Connection parameters: heartbeat=60s, blocked_connection_timeout=300s
- Support connection string format: amqp://user:pass@host:port/vhost
- Handle authentication failures gracefully
- Implement connection state enum: DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING
- Create dedicated connection module: src/rabbitmq_mcp_connection/connection.py

---

## Story 2.3: HTTP Management API Client

As a developer,
I want an HTTP client for RabbitMQ Management API operations,
So that I can perform topology management (queues, exchanges, bindings) alongside AMQP messaging.

**Acceptance Criteria:**

**Given** valid Management API configuration (typically host:15672)
**When** the server creates HTTP client
**Then** client is configured with base URL: http(s)://{host}:{port}/api

**And** HTTP Basic Auth header is set using configured username and password

**And** TLS/SSL is enabled if HTTP_USE_TLS=true

**And** certificate verification follows HTTP_VERIFY_CERT setting

**And** client timeout is 30 seconds (configurable)

**And** client includes User-Agent header: "rabbitmq-mcp-server/{version}"

**And** connection pooling maintains up to 5 concurrent connections (configurable)

**And** client retries on connection errors: 0 retries (fail-fast)

**Prerequisites:** Story 2.1 (configuration management)

**Technical Notes:**
- Use httpx.AsyncClient for async operations
- Base URL format: http://localhost:15672/api
- Content-Type: application/json for requests
- Accept: application/json for responses
- Handle 401 Unauthorized with clear auth error message
- Handle 404 Not Found for missing resources
- Implement request/response logging with correlation IDs
- Create dedicated HTTP client module: src/rabbitmq_mcp_connection/http_client.py

---

## Story 2.4: Connection Health Checks

As a developer,
I want periodic health checks for RabbitMQ connections,
So that I can detect connection failures quickly and trigger reconnection logic.

**Acceptance Criteria:**

**Given** established RabbitMQ connections (AMQP + HTTP)
**When** health check runs
**Then** AMQP connection health is verified via pika.connection.is_open check

**And** HTTP API health is verified via GET /api/healthchecks/node request

**And** health checks complete in <1 second

**And** health check runs every 30 seconds (configurable)

**And** failed health checks log warning: "Health check failed: {reason}"

**And** consecutive failures (3+) trigger reconnection logic

**And** health check exposes status: {amqp_connected: bool, http_connected: bool, last_check: timestamp}

**And** health status is available via MCP tools/call: "connection.health"

**Prerequisites:** Story 2.2 (AMQP connection), Story 2.3 (HTTP client)

**Technical Notes:**
- Use asyncio.create_task for background health checks
- Health check interval configurable via HEALTH_CHECK_INTERVAL env var
- Implement connection watchdog pattern
- Track metrics: successful_checks, failed_checks, average_check_duration
- Don't overwhelm RabbitMQ with checks (respect interval)
- Log health check failures but don't spam logs (rate limiting)

---

## Story 2.5: Automatic Reconnection with Exponential Backoff

As a developer,
I want automatic reconnection when RabbitMQ connection is lost,
So that the MCP server recovers gracefully from network disruptions without manual intervention.

**Acceptance Criteria:**

**Given** a connection loss event (network failure, RabbitMQ restart, etc.)
**When** reconnection logic triggers
**Then** reconnection attempts follow exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, then 60s max

**And** reconnection attempts continue indefinitely until successful

**And** each attempt logs: "Reconnection attempt {n} in {delay}s..."

**And** successful reconnection completes in <10 seconds after RabbitMQ becomes available

**And** reconnection re-establishes both AMQP and HTTP connections

**And** in-flight operations receive error: "Connection lost, please retry after reconnection"

**And** after reconnection, server logs: "Reconnected to RabbitMQ successfully"

**And** reconnection state is exposed: {state: "reconnecting", attempt: 5, next_attempt_in: "32s"}

**Prerequisites:** Story 2.2 (AMQP connection), Story 2.3 (HTTP client), Story 2.4 (health checks)

**Technical Notes:**
- Implement reconnection state machine: CONNECTED → DISCONNECTED → RECONNECTING → CONNECTED
- Use asyncio.sleep for backoff delays (non-blocking)
- Track reconnection metrics: attempts, total_downtime, last_reconnect_timestamp
- Prevent reconnection storms (respect backoff schedule)
- Reset backoff to 1s after successful connection lasting >5 minutes
- Broadcast reconnection events to subscribers (if any)
- Handle partial reconnection failures (AMQP ok, HTTP failed)

---

## Story 2.6: Connection Pooling for HTTP with Cache Invalidation Strategy

As a developer,
I want HTTP connection pooling to reuse connections across multiple API calls,
So that I reduce connection overhead and improve operation throughput.

**Acceptance Criteria:**

**Given** multiple concurrent HTTP Management API operations
**When** operations execute
**Then** HTTP client reuses existing connections from pool (up to 5 connections)

**And** connection pool blocks when full with 10s timeout (configurable)

**And** idle connections are closed after 60s (connection timeout)

**And** pool size is configurable via MAX_HTTP_CONNECTIONS env var

**And** pool metrics are tracked: active_connections, pool_size, wait_time

**And** pool exhaustion logs warning: "HTTP connection pool exhausted, waiting for available connection"

**And** pool status exposed via "connection.pool_status" operation

**And** stale connections are automatically detected and evicted based on error patterns

**And** configuration changes trigger pool flush and reconnection

**And** connection health is validated proactively via background checks

**Prerequisites:** Story 2.3 (HTTP client)

**Technical Notes:**
- httpx.AsyncClient includes connection pooling by default
- Configure pool: limits=httpx.Limits(max_connections=5, max_keepalive_connections=5)
- Monitor pool usage for performance tuning
- Consider dynamic pool sizing based on load
- Document pool configuration in performance tuning guide
- Test pool behavior under concurrent load (100+ operations)

**Cache Invalidation Strategy:**
```python
# Connection eviction triggers
1. Stale Connection Detection:
   - HTTP 503 Service Unavailable → Immediate eviction
   - Connection timeout (30s) → Immediate eviction
   - Socket error (ECONNRESET, EPIPE) → Immediate eviction
   - SSL/TLS errors → Immediate eviction

2. Health-Based Eviction:
   - Failed health check on connection → Mark for eviction
   - 3 consecutive errors on same connection → Force eviction
   - Connection age >5 minutes + idle >60s → Eligible for eviction

3. Configuration Change Detection:
   - RabbitMQ credentials changed → Flush entire pool
   - RabbitMQ host/port changed → Flush entire pool
   - TLS certificate updated → Flush entire pool
   - Triggered by SIGHUP or config file watch

4. Proactive Refresh:
   - Background task validates idle connections every 30s
   - Send lightweight GET /api/overview to validate
   - Evict connections that fail validation
   - Prevents serving stale connections to requests
```

**Connection Failure Handling:**
- On connection failure: Remove from pool, log error, retry with new connection
- Max retries: 0 (fail-fast pattern, let auto-reconnection handle it)
- Circuit breaker: After 5 consecutive pool-wide failures, trigger reconnection (Story 2.5)
- Metrics: Track eviction rate, failure reasons, pool health score

**Pool Health Monitoring:**
```python
pool_health = {
    "size": 5,
    "active": 3,
    "idle": 2,
    "evictions_last_hour": 12,
    "avg_connection_age_seconds": 180,
    "health_score": 0.95  # (successful_requests / total_requests)
}
# Alert if health_score < 0.90 (indicates connection quality issues)
```

---

## Story 2.7: TLS/SSL Certificate Handling

As a security-conscious user,
I want TLS/SSL support for both AMQP and HTTP connections with certificate verification,
So that my RabbitMQ credentials and data are encrypted in transit.

**Acceptance Criteria:**

**Given** TLS/SSL is enabled (AMQP_USE_TLS=true, HTTP_USE_TLS=true)
**When** connections are established
**Then** AMQP connection uses SSL context with TLS 1.2+ protocol

**And** HTTP client uses HTTPS with TLS 1.2+ protocol

**And** certificate verification is enabled by default (VERIFY_CERT=true)

**And** self-signed certificates can be allowed via VERIFY_CERT=false (logs warning)

**And** custom CA certificates can be specified via CA_CERT_PATH env var

**And** certificate verification failures return clear error: "SSL certificate verification failed: {details}"

**And** TLS handshake completes within connection timeout (30s)

**And** TLS connections log: "Using TLS/SSL for {protocol} connection (verify={verify_mode})"

**Prerequisites:** Story 2.2 (AMQP connection), Story 2.3 (HTTP client)

**Technical Notes:**
- Use ssl.create_default_context() for secure defaults
- Support cert_reqs=ssl.CERT_REQUIRED (default) or ssl.CERT_NONE (insecure)
- Load custom CA certs: ssl_context.load_verify_locations(cafile=ca_cert_path)
- Document certificate setup in security guide
- Warn users about insecure mode: "WARNING: Certificate verification disabled - use only for testing"
- Test with self-signed certs in development

---
