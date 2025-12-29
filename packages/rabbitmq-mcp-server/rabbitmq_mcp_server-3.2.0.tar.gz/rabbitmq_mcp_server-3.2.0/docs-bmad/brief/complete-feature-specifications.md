# Complete Feature Specifications

This section consolidates all detailed user stories, requirements, and implementation guidance from the original specifications. Each feature includes user stories with acceptance criteria, functional requirements, technical constraints, and success metrics.

## Feature 001: Base MCP Architecture

**Purpose**: Implement the fundamental MCP server architecture with the 3-tool semantic discovery pattern that enables natural language interaction with RabbitMQ operations.

### User Stories

**US1-1: Discover Available Operations (Priority: P1)**

As a developer integrating with RabbitMQ, I need to search for operations using natural language queries so I can quickly find functionality without knowing all available endpoints.

*Acceptance Criteria*:
- Given the MCP server is running, when I send a search for "list queues", then I receive relevant queue operations with descriptions and IDs
- Given a search for "exchanges", then I see multiple exchange operations ranked by relevance
- Given a search for nonexistent operations, then I receive an empty list or helpful suggestions
- Search results return in <100ms with similarity scores ≥0.7

**US1-2: Get Operation Details (Priority: P1)**

As a developer, I need to query complete documentation and parameter schemas for specific operations so I understand exactly how to use them before execution.

*Acceptance Criteria*:
- Given a valid operation ID, when I request details, then I receive complete parameter schema, types, and description
- Given operation has examples, when I request details, then examples are included
- Given an invalid operation ID, when I request details, then I receive clear error indicating operation doesn't exist
- Details returned in <50ms

**US1-3: Execute RabbitMQ Operations (Priority: P1)**

As a developer, I need to execute RabbitMQ operations with validated parameters so I can manage resources programmatically and reliably.

*Acceptance Criteria*:
- Given valid operation and parameters, when I execute, then action succeeds on RabbitMQ and I receive success result
- Given invalid parameters, when I attempt execution, then I receive validation error listing missing/invalid fields before any RabbitMQ call
- Given RabbitMQ is unavailable, when I execute, then I receive immediate connection error without retry
- Operations complete in <200ms under normal conditions

**US1-4: Receive Clear Error Feedback (Priority: P2)**

As a developer, I need standardized, descriptive error messages so I can quickly identify and correct problems.

*Acceptance Criteria*:
- Given validation failures, when operation fails, then error lists specific missing/invalid parameters with expected formats
- Given internal errors, when they occur, then I receive safe generic message without exposing sensitive details
- All errors follow JSON-RPC 2.0 format with appropriate error codes
- 95% of error messages enable problem resolution without consulting external documentation

### Functional Requirements

**Core Architecture**:
- FR-001: System MUST expose exactly 3 public MCP tools: search-ids (semantic search), get-id (documentation), call-id (execution)
- FR-002: All operations and schemas MUST derive from single OpenAPI specification source of truth
- FR-003: Parameter validation MUST occur before RabbitMQ execution, returning immediate errors listing specific missing/invalid fields (<10ms validation overhead)
- FR-004: Error codes MUST follow MCP protocol standards (JSON-RPC 2.0)
- FR-005: Operations MUST be organized in logical categories (namespaces) from OpenAPI tags

**Semantic Search**:
- FR-006: Search MUST use sentence-transformers model all-MiniLM-L6-v2 (384 dimensions) with similarity threshold ≥0.7
- FR-007: Search query "create queue" MUST return queues.create with score ≥0.9, reject users.create with score <0.7
- FR-008: Zero results (all scores <0.7) MUST return empty list with suggestion "Try broader search terms"
- FR-009: Results MUST be ordered by similarity score descending
- FR-010: Search latency MUST be <100ms (95th percentile)

**Operation Execution**:
- FR-011: Operation schemas MUST be stored in SQLite database, generated at build time, never at runtime
- FR-012: System MUST support AMQP protocol operations (publish, consume, ack, nack, reject) with manually maintained schemas
- FR-013: Authentication MUST use RabbitMQ credentials from environment variables (username/password)
- FR-014: Operations exceeding 30-second timeout MUST be aborted with descriptive error
- FR-015: Logging MUST be structured JSON with configurable levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- FR-016: Malformed RabbitMQ responses MUST return descriptive parsing errors without exposing internal details
- FR-017: Cache access MUST be thread-safe using asyncio.Lock to prevent race conditions
- FR-018: Connection failures MUST return immediately without automatic retry (fail-fast pattern)

**Observability**:
- FR-019: OpenTelemetry instrumentation is MANDATORY with OTLP exporter, optional Jaeger/Prometheus exporters
- FR-020: Distributed traces MUST cover 100% of operations with correlation IDs linking all log entries
- FR-021: Metrics MUST include: request counters, latency histograms (p50/p95/p99), cache hit/miss ratios, concurrent request gauges
- FR-022: Target: 95% of operations generate complete traces, 100% of errors must be traceable

**Rate Limiting**:
- FR-023: Rate limiting MUST be 100 requests/minute per client (configurable via RATE_LIMIT_RPM)
- FR-024: Client identification priority: (1) MCP connection ID, (2) IP address fallback, (3) global shared limit (debugging only)
- FR-025: Exceeded limits MUST return HTTP 429 with Retry-After header
- FR-026: Rate limit rejection latency MUST be <5ms

**Multi-Version Support**:
- FR-027: System MUST support one OpenAPI version per deployment, selectable via RABBITMQ_API_VERSION environment variable
- FR-028: Supported versions: 3.11.x (legacy), 3.12.x (LTS), 3.13.x (latest) - each with pre-generated schemas/embeddings
- FR-029: Invalid version MUST return error listing supported versions with setup instructions

**AMQP Operations** (not in OpenAPI):
- FR-030: amqp.publish - Publish message to exchange with routing key, properties (content_type, delivery_mode, priority, correlation_id, etc.)
- FR-031: amqp.consume - Subscribe to queue with consumer_tag, auto_ack options, returns message stream
- FR-032: amqp.ack - Acknowledge message processing with delivery_tag, multiple flag
- FR-033: amqp.nack - Negative acknowledge with requeue option
- FR-034: amqp.reject - Reject message (send to DLQ if configured)
- FR-035: AMQP operations MUST have manually maintained Pydantic schemas in schemas/amqp_operations.py



### Success Criteria

- SC-001: Developers discover relevant operations in <5 seconds using natural language search
- SC-002: System responds to basic requests in <200ms
- SC-003: Parameter validation adds <10ms overhead
- SC-004: Memory usage remains <1GB per instance
- SC-005: 100% of operations comply with MCP protocol (validated by contract tests)
- SC-006: Developers execute operations successfully on first attempt after reading documentation
- SC-007: 90% of errors enable problem resolution without external documentation (measured via early adopter surveys)
- SC-008: Operations exceeding 30s timeout are aborted with clear messages
- SC-009: JSON structured logs enable automated analysis in production
- SC-010: System maintains cache integrity under concurrent access
- SC-011: OpenTelemetry enables end-to-end monitoring with request correlation
- SC-012: Rate limiting protects RabbitMQ from overload, rejects excess requests in <5ms

---

## Feature 002: Basic RabbitMQ Connection

**Purpose**: Establish reliable, resilient connections to RabbitMQ via AMQP protocol with automatic reconnection and health monitoring.

### User Stories

**US2-1: Establish RabbitMQ Connection (Priority: P1)**

As an operator, I need to connect the application to RabbitMQ using valid credentials so operations can begin.

*Acceptance Criteria*:
- Given RabbitMQ is available with valid credentials, when connection is requested, then connection succeeds in <5 seconds
- Given invalid credentials, when connection is attempted, then clear authentication error is returned
- Given RabbitMQ is unreachable, when connection timeout is 30 seconds, then error returns after max 30 seconds

**US2-2: Monitor Connection Health (Priority: P2)**

As an operator, I need to verify RabbitMQ health and connection status so I can diagnose issues quickly.

*Acceptance Criteria*:
- Given an active connection, when health check is requested, then connection status returns in <1 second
- Given operational RabbitMQ, when health check runs, then availability is confirmed
- Given connection was lost, when status is checked, then failure is detected and reported

**US2-3: Automatic Connection Recovery (Priority: P3)**

As an operator, I want automatic reconnection when connection drops so manual intervention isn't needed.

*Acceptance Criteria*:
- Given connection is lost, when RabbitMQ becomes available, then auto-reconnect succeeds in <10 seconds using exponential backoff (1s→2s→4s→8s→16s→32s→60s max, infinite retries)
- Given multiple reconnection failures, when system continues trying, then logs are generated and interval remains at 60s maximum
- Given connection recovered, when operations are requested, then system functions normally

**US2-4: Connection Pool Management (Priority: P4)**

As a developer, I need connection pooling for concurrent operations so performance is optimized.

*Acceptance Criteria*:
- Given connection pool configured, when multiple operations run simultaneously, then available pool connections are used
- Given all pool connections busy, when new operation is requested, then system blocks until connection available (timeout: 10 seconds)
- Given operation completes, when connection is released, then connection returns to pool for reuse

### Functional Requirements

**Connection Management**:
- FR-001: AMQP 0-9-1 protocol MUST be used for RabbitMQ connection with host, port, user, password, vhost parameters
- FR-002: Configuration MUST load from multiple sources with precedence: programmatic args > env vars (AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASSWORD, AMQP_VHOST) > TOML file > defaults
- FR-003: Parameters MUST be validated: host non-empty, port 1-65535, timeout 1-300s, heartbeat 0-3600s, user/password non-empty, vhost starts with "/"
- FR-004: Connection establishment MUST complete in <5 seconds when server is available
- FR-005: Connection timeout MUST be 30 seconds, after which ConnectionTimeoutError triggers reconnection mode
- FR-006: Authentication errors MUST return clear, specific messages

**Health Monitoring**:
- FR-007: Clean disconnection MUST properly close all AMQP resources
- FR-008: Health check MUST complete in <1 second and return current connection state
- FR-009: Connection state MUST be monitored in real-time (connected, disconnected, reconnecting)
- FR-010: Connection loss detection MUST use hybrid mechanism: 60-second heartbeat AMQP + connection event callbacks

**Auto-Reconnection**:
- FR-011: Reconnection MUST be automatic with infinite retries using exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, then 60s maximum indefinitely
- FR-012: Successful reconnection MUST complete in <10 seconds when server returns
- FR-013: Connection pool MUST maintain default 5 connections (configurable), blocking when full with 10s default timeout

**Logging & Monitoring**:
- FR-014: Critical connection events MUST be logged in structured JSON: connection established, failures, disconnections, reconnection start
- FR-015: Credentials MUST be automatically sanitized in logs (passwords never shown)
- FR-016: Connection state changes MUST be observable through MCP interface using ChromaDB local mode for semantic operation discovery
- FR-017: Network errors MUST be handled gracefully without application crashes
- FR-018: Default configuration: localhost:5672, vhost "/" when not specified
- FR-019: Virtual host existence MUST be validated during connection (AMQP 530 NOT_ALLOWED error if missing) with specific error "VHost not found: {vhost}"

### Success Criteria

- SC-001: Operators connect to RabbitMQ with valid credentials: p95 <5s, p99 <7s (measured via 100+ test runs)
- SC-002: Health checks return in <1 second: p95 <1s, p99 <1.5s
- SC-003: Auto-reconnection completes in <10 seconds after server recovery: p95 <10s, p99 <15s (tested with simulated failures)
- SC-004: 100% of connection failures generate clear, actionable error messages
- SC-005: Connection loss detected within 60 seconds (heartbeat cycle) or immediately via event callbacks
- SC-006: Zero credential exposure in logs or error messages
- SC-007: System supports 10+ concurrent operations using connection pool without performance degradation
- SC-008: Connection success rate is 100% when server is available and credentials valid
- SC-009: Clean disconnections release all resources without leaks (memory, file descriptors)
- SC-010: Operators diagnose connection problems from logs in <2 minutes (avg <60s via usability study)

---

## Feature 003: Essential Topology Operations

**Purpose**: Enable management of RabbitMQ topology (queues, exchanges, bindings) through safe, validated operations with comprehensive error handling.

### User Stories

**US3-1: View and Monitor Infrastructure (Priority: P1)**

As an operator, I need to view all queues, exchanges, and bindings with statistics so I understand infrastructure state and identify problems.

*Acceptance Criteria*:
- Given system with multiple queues, when list requested, then all queues shown with name, message count, consumer count, memory usage
- Given different exchange types, when list requested, then all exchanges shown with name, type (direct/topic/fanout/headers), binding count
- Given bindings exist, when list requested, then all bindings shown with source exchange, destination queue, routing key
- Given queue with 1000 messages, when statistics viewed, then exact message count and processing rate displayed
- Given 1000 queues, when list requested, then all results returned in <2 seconds

**US3-2: Create Routing Infrastructure (Priority: P2)**

As an operator, I need to create queues, exchanges, and bindings with proper configurations so message flows can be established.

*Acceptance Criteria*:
- Given empty vhost, when creating queue with name and options (durable, exclusive, auto-delete), then queue created with specified config and appears in listing
- Given vhost, when creating exchange with name and type, then exchange created correctly and available for bindings
- Given queue and exchange exist, when creating binding with routing key, then messages route correctly from exchange to queue
- Given valid creation parameters, when operation executes, then completes in <1 second
- Given duplicate name, when attempting creation with different config, then clear conflict message returned

**US3-3: Remove Obsolete Infrastructure Safely (Priority: P3)**

As an operator, I need to remove obsolete resources with safety validations so data loss and service interruptions are prevented.

*Acceptance Criteria*:
- Given empty queue without consumers, when deletion requested, then queue removed and disappears from listing
- Given queue with pending messages, when deletion attempted without --force, then blocked with clear warning about message presence
- Given exchange without bindings, when deletion requested, then exchange removed successfully
- Given exchange with active bindings, when deletion attempted, then error indicates bindings must be removed first
- Given existing binding, when deletion requested, then binding removed and message flow stops
- Given valid deletion, when executed, then completes in <1 second

### Functional Requirements

**Queue Operations**:
- FR-001: List all queues in specific vhost or all vhosts MUST be supported
- FR-002: Queue statistics MUST display mandatory fields: messages (total), messages_ready, messages_unacknowledged, consumers, memory; optional fields (if present in API response): message_stats.publish, message_stats.deliver_get, message_stats.ack, node, exclusive_consumer_tag, policy, slave_nodes
- FR-003: Queue creation MUST accept name and basic options: durable, exclusive, auto-delete
- FR-004: Queue names MUST be validated: alphanumeric, hyphen, underscore, period only; max 255 characters
- FR-005: Duplicate queue names in same vhost MUST be prevented
- FR-006: Queue deletion MUST validate: messages=0 and consumers=0 before allowing deletion
- FR-007: Empty queue validation: messages=0 AND consumers=0 MUST both be true
- FR-008: Force deletion flag (--force) MUST allow deletion of queues with messages (converts to API query parameter if-empty=false)

**Exchange Operations**:
- FR-009: List all exchanges MUST show exchange type information
- FR-010: Exchange statistics MUST include mandatory fields: type, durable, auto_delete; optional fields (if present): message_stats.publish_in, message_stats.publish_out, message_stats.confirm, message_stats.return_unroutable, policy, internal
- FR-011: Exchange creation MUST accept name and type parameter
- FR-012: Supported exchange types: direct, topic, fanout, headers
- FR-013: Exchange names MUST be validated: alphanumeric, hyphen, underscore, period; max 255 characters; valid type specified
- FR-014: Duplicate exchange names MUST be prevented
- FR-015: Exchange deletion MUST be supported
- FR-016: Active bindings MUST block exchange deletion with error requiring explicit binding removal first
- FR-017: System exchanges (amq.* prefix) and default exchange ("") MUST be protected from deletion

**Binding Operations**:
- FR-018: List all bindings MUST show source exchange, destination queue, routing key
- FR-019: Binding creation MUST validate that both exchange and queue exist (order: validate exchange first, then queue)
- FR-020: Existence validation priority explained: exchanges are more commonly forgotten than queues, so validating exchange first provides faster error discovery
- FR-021: Topic exchange bindings MUST support wildcard patterns (* and #) in routing keys
- FR-022: Binding deletion MUST support removing specific exchange-to-queue links
- FR-023: Duplicate bindings MUST be prevented (same exchange, queue, routing key)

**Safety & Validation**:
- FR-024: Virtual host existence MUST be validated before topology operations (cached 60s to reduce overhead)
- FR-024a: HTTP 429 (rate limiting) MUST trigger retry with exponential backoff: max 3 retries, delays 1s/2s/4s, logging each attempt at WARNING level
- FR-025: Validation failures MUST return structured errors with: error code, field context, expected vs actual values, suggested corrective action
- FR-026: All creation and deletion operations MUST be logged for audit (fields: timestamp, correlation_id, operation, vhost, resource_name, user, result)
- FR-027: Permission validation MUST be delegated to RabbitMQ; authorization errors propagated with clear messages and logged at WARNING level for audit

**CLI Interface**:
- FR-028: CLI syntax MUST follow format: `<command> <subcommand> <options>`
- FR-028a: Single operation per CLI invocation (stateless execution model); no batch operations in MVP
- FR-029: Credentials MUST be accepted via CLI arguments (--host, --port, --user, --password) or environment variables
- FR-029a: TLS/SSL connections MUST be supported with certificate verification enabled by default; --insecure flag to disable for self-signed certs
- FR-030: Output MUST be formatted for humans (tables, lists) with optional JSON via --format flag
- FR-030a: Table column order MUST follow pattern: Identity (name) → Configuration (durable, type) → Metrics (messages, consumers)
- FR-031: Exit codes MUST be appropriate: 0 for success, non-zero for errors
- FR-032: Help text MUST be accessible via --help for all commands and subcommands



### Success Criteria

- SC-001: Operators view complete infrastructure state in <2 seconds
- SC-002: Queue/exchange/binding creation completes in <1 second
- SC-003: Queue/exchange/binding deletion completes in <1 second
- SC-004: 100% prevention of queue deletion with messages (without explicit --force confirmation)
- SC-005: 100% blocking of exchange deletion with active bindings
- SC-006: System handles 1000 queues and 1000 exchanges efficiently
- SC-007: 95% of failed operations provide clear errors (code, field, expected value, corrective action) enabling operator resolution without external documentation
- SC-008: All creation/deletion operations logged for complete audit trail
- SC-009: 100% of input parameters validated before execution, preventing inconsistent states

---

## Feature 004: Message Publishing and Consumption

**Purpose**: Enable message publishing to exchanges and consumption from queues with proper acknowledgment handling.

### User Stories

**US4-1: Send Messages to Systems (Priority: P1)**

As an operator, I need to publish messages to exchanges with routing keys and properties so systems can communicate asynchronously.

*Acceptance Criteria*:
- Given configured exchange, when publishing JSON message, then message delivered to exchange successfully in <100ms
- Given custom headers specified, when message published, then headers preserved in delivered message
- Given message marked persistent, when published, then message survives broker restarts
- Given invalid routing key, when attempting publish, then validation error returned before send attempt

**US4-2: Receive Messages from Queues (Priority: P2)**

As an operator, I need to consume messages from queues so I can process incoming information in real-time.

*Acceptance Criteria*:
- Given queue contains messages, when subscribing, then messages delivered in real-time with <50ms latency
- Given multiple messages queued, when prefetch limit is 10, then max 10 unacknowledged messages delivered simultaneously
- Given subscription active, when new message arrives, then delivered immediately to consumer
- Given queue doesn't exist, when attempting consumption, then clear error indicating queue not found

**US4-3: Confirm Message Processing (Priority: P3)**

As an operator, I need to acknowledge successful processing or reject failures so message reliability is maintained.

*Acceptance Criteria*:
- Given message received, when acknowledging (ack), then message permanently removed from queue
- Given processing failed, when rejecting with requeue enabled, then message returns to queue for retry
- Given critical failure, when rejecting without requeue, then message removed (sent to DLX if configured)
- Given duplicate ack attempt, when sent, then system ignores gracefully without error
- Given invalid delivery tag, when ack attempted, then clear error about tag not found

### Functional Requirements

**Message Publishing**:
- FR-001: Publish messages to exchanges MUST accept: content, exchange name, routing key
- FR-002: Payload types supported: JSON, plain text, binary data
- FR-003: Message properties MUST be configurable: custom headers, content-type, correlation ID
- FR-004: Persistence MUST be supported via delivery_mode flag for survival across restarts
- FR-005: Exchange existence MUST be validated before publishing
- FR-006: Publish operations MUST complete in <100ms under normal conditions

**Message Consumption**:
- FR-007: Queue subscription MUST support specific queue targeting
- FR-008: Messages MUST be delivered in real-time as they arrive
- FR-009: Message metadata MUST be preserved: headers, delivery tag, routing key, properties
- FR-010: Prefetch limit MUST be configurable (default: 10 messages)
- FR-011: Consumption latency MUST remain <50ms per message
- FR-012: Successful message processing MUST support acknowledgment (ack)
- FR-013: Failed processing MUST support negative acknowledgment (nack) with requeue option
- FR-014: Delivery tags MUST be tracked for reliable acknowledgment
- FR-015: Duplicate acknowledgments MUST be prevented
- FR-016: Delivery tag validation MUST occur before acknowledgment processing
- FR-017: Connection failures MUST be handled gracefully during operations
- FR-018: System MUST support at least 100 concurrent consumers
- FR-019: Throughput MUST be at least 1000 messages per minute
- FR-020: Queue existence MUST be validated before starting consumption
- FR-021: All message operations MUST be logged with correlation IDs for tracing
- FR-022: Consumers MUST choose between automatic or manual acknowledgment

### Success Criteria

- SC-001: Operators publish messages and confirm delivery in <100ms
- SC-002: Message consumption latency max 50ms per message
- SC-003: Throughput maintains 1000+ messages/minute under normal load
- SC-004: System supports 100 concurrent consumers without performance degradation
- SC-005: Zero message loss during normal operations (correct acknowledgment)
- SC-006: Operators trace complete message lifecycle (publish → consume → ack) through logs
- SC-007: 95% of publish operations succeed on first attempt
- SC-008: System recovers automatically from connection failures in <5 seconds
- SC-009: Rejected messages with requeue return to queue in <100ms
- SC-010: Operators process different payload types (JSON, text, binary) without additional configuration

---

## Feature 005: Basic Console Client

**Purpose**: Provide built-in command-line interface for interactive RabbitMQ management without requiring external MCP clients.

### User Stories

**US5-1: Connect and Check Health (Priority: P1)**

As a system operator, I need to verify RabbitMQ accessibility and status before executing operations.

*Acceptance Criteria*:
- Given RabbitMQ running, when executing connection command with valid credentials, then system confirms successful connection and displays status
- Given RabbitMQ unreachable, when attempting connection, then clear error message indicates connection failure
- Given connection established, when executing health check, then current server status returned in <100ms

**US5-2: Manage Queues and Exchanges (Priority: P2)**

As a developer, I need to create and manage queues/exchanges to configure messaging topology.

*Acceptance Criteria*:
- Given established connection, when listing queues, then all queues displayed with basic properties
- Given connection, when creating new queue with valid name, then queue created and appears in listing
- Given empty queue, when requesting deletion, then queue removed and operation confirmed
- Given connection, when creating exchange with valid type, then exchange created and confirmed
- Given exchange exists, when listing exchanges, then created exchange displayed with its type

**US5-3: Publish and Subscribe Messages (Priority: P3)**

As an operator, I need to send test messages and monitor queue consumption to verify message flow.

*Acceptance Criteria*:
- Given exchange and bound queue, when publishing message with routing key, then system confirms delivery
- Given queue contains messages, when subscribing, then messages delivered in real-time
- Given message received, when acknowledging, then message removed from queue
- Given publish error, when attempting send, then clear error message indicates the problem

**US5-4: View Status and Metrics (Priority: P4)**

As an administrator, I want to monitor connection state and basic operational metrics for troubleshooting.

*Acceptance Criteria*:
- Given active connection, when querying status, then connection state and basic metrics displayed
- Given no connection, when checking status, then indicates no active connection
- Given operations performed, when checking status, then recent operations reflected

### Functional Requirements

**Connection Management**:
- FR-001: User MUST be able to connect to RabbitMQ providing host, port, credentials
- FR-002: Connection success/failure MUST be clearly indicated
- FR-003: Explicit disconnection MUST be supported
- FR-004: Health check MUST verify connection and return server status

**Resource Operations**:
- FR-005: List all queues MUST be supported
- FR-006: Queue creation MUST accept name and basic options (durability, auto-delete)
- FR-007: Queue deletion MUST be supported
- FR-008: List all exchanges MUST be supported
- FR-009: Exchange creation MUST accept name and type (direct, topic, fanout, headers)
- FR-010: Exchange deletion MUST be supported

**Messaging**:
- FR-011: Message publishing MUST accept exchange, routing key, payload
- FR-012: Queue subscription MUST deliver messages in real-time
- FR-013: Message acknowledgment MUST support delivery tag-based confirmation
- FR-014: Connection and operational status MUST be displayable
- FR-015: Integrated help MUST be available for all commands and options
- FR-016: Command history MUST persist between sessions
- FR-017: Operation failures MUST provide clear, actionable error messages
- FR-018: Input validation MUST occur before operation execution (valid names, required parameters)
- FR-019: Long operations MUST show progress indicators
- FR-020: Output MUST use formatted, colored display for readability

### Success Criteria

- SC-001: Users connect to RabbitMQ and receive confirmation in <2 seconds
- SC-002: Simple commands (list, create, delete) respond in <100ms after connection
- SC-003: Interactive mode remains responsive during prolonged message subscription
- SC-004: 95% of users execute basic operations (connect, create queue, publish message) using only integrated help
- SC-005: Error messages enable users to identify and correct problems without external documentation
- SC-006: Users complete full message flow (publish and receive test message) in <1 minute
- SC-007: Command history persists and enables reuse of previous commands between sessions
- SC-008: System operates without memory leaks during prolonged use (8+ hours continuous operation)
- SC-009: Colored, formatted interface improves task completion rate by 30% vs plain text output
- SC-010: All commands discoverable through help system without consulting external documentation

---

## Feature 006: Basic Testing Framework

**Purpose**: Establish comprehensive testing framework ensuring quality, reliability, and specification compliance through unit, integration, contract, and performance tests.

### User Stories

**US6-1: Validate Critical Component Quality (Priority: P1)**

As a developer, I need automated tests for critical components (connection management, message operations, queue operations) so functionality is verified before production.

*Acceptance Criteria*:
- Given modified critical component, when executing test suite, then all tests pass with coverage >80%
- Given new critical component, when tests written before implementation (TDD), then tests fail until implementation complete
- Given complete test suite execution, when finished, then detailed coverage report shows percentages by component

**US6-2: Validate Integration with Real RabbitMQ (Priority: P2)**

As a developer, I need integration tests using actual RabbitMQ instance so real-world behavior is verified.

*Acceptance Criteria*:
- Given isolated RabbitMQ instance, when executing integration tests, then system connects, creates queues, publishes and consumes messages successfully
- Given integration test completion, when tests finish, then environment cleaned automatically without residual data
- Given parallel test execution, when multiple tests run, then no interference occurs and all pass deterministically

**US6-3: Validate MCP Protocol Compliance (Priority: P1)**

As a developer, I need contract tests validating MCP specification adherence so interoperability is guaranteed.

*Acceptance Criteria*:
- Given implemented MCP tool, when executing contract tests, then tool validates against OpenAPI spec and passes all scenarios
- Given Pydantic models generated, when executing schema tests, then models correctly validate against OpenAPI schemas
- Given new MCP tool implementation, when running conformance tests, then any protocol deviation is detected

**US6-4: Measure Critical Operation Performance (Priority: P3)**

As a developer, I need performance tests measuring latency and throughput so performance requirements are met.

*Acceptance Criteria*:
- Given critical operation implemented, when executing performance tests, then latency and throughput metrics collected
- Given message throughput tests, when completed, then messages-per-second rate reported
- Given memory usage tests, when multiple connections open, then memory usage monitored and reported over time

**US6-5: Execute Tests Rapidly in CI/CD (Priority: P2)**

As a developer, I need complete test suite executing in <5 minutes so feedback is rapid during development and in pipelines.

*Acceptance Criteria*:
- Given complete test suite, when executing all tests, then total execution time <5 minutes
- Given parallel test execution, when suite runs, then multiple tests execute simultaneously without conflicts
- Given test failure, when CI/CD pipeline runs, then build fails and prevents merge until tests pass

### Functional Requirements

**Test Execution**:
- FR-001: Unit tests MUST cover all critical components (connection management, message operations, queue operations)
- FR-002: Integration tests MUST use real RabbitMQ instance
- FR-003: Contract tests MUST validate MCP protocol compliance
- FR-004: Performance tests MUST measure latency and throughput
- FR-005: Parallel test execution MUST be supported
- FR-006: Complete test suite MUST execute in <5 minutes

**Test Coverage**:
- FR-007: Minimum 80% coverage for critical tools (connection management, message pub/consume, queue operations)
- FR-008: 100% coverage for authentication flows
- FR-009: 100% coverage for error handling
- FR-010: 100% coverage for MCP protocol compliance
- FR-011: Coverage reports MUST show percentages by component

**Test Environment**:
- FR-012: Isolated test environment MUST be provided for each execution
- FR-013: Isolated RabbitMQ instance MUST be started for integration tests
- FR-014: Test data MUST be cleaned automatically after execution
- FR-015: Consistent test fixtures and data MUST be provided

**Test Quality**:
- FR-016: All tests MUST be deterministic and repeatable
- FR-017: Flaky tests MUST NOT be allowed in suite
- FR-018: Complete isolation MUST be guaranteed between parallel tests
- FR-019: Contract validation MUST verify against OpenAPI specification
- FR-020: Pydantic model validation MUST verify against OpenAPI schemas

**TDD Workflow**:
- FR-021: Development process MUST follow Red-Green-Refactor cycle (tests written → approved → fail → implementation)
- FR-022: Tests MUST be written before implementation
- FR-023: CI/CD pipeline MUST require 100% test success before allowing merge

**Performance Testing**:
- FR-024: Individual operation latency MUST be measured
- FR-025: Bulk message operation throughput MUST be measured
- FR-026: Memory usage MUST be monitored during tests
- FR-027: Connection pool under load MUST be tested

**Test Categories**:
- FR-028: Tests MUST cover connection establishment, failure, and recovery
- FR-029: Tests MUST cover queue/exchange creation, deletion, and listing
- FR-030: Tests MUST cover message publishing, consuming, and acknowledgment
- FR-031: Tests MUST cover console client functionality and user experience

### Success Criteria

- SC-001: Developers execute complete test suite in <5 minutes
- SC-002: Minimum 80% coverage achieved for all critical components
- SC-003: 100% coverage for authentication, error handling, MCP compliance
- SC-004: 100% of tests pass before any merge in CI/CD pipeline
- SC-005: Zero flaky tests detected in 100 consecutive complete suite executions
- SC-006: Developers receive test feedback in <1 minute after modification (for relevant tests)
- SC-007: Integration tests execute successfully with real RabbitMQ in 100% of runs
- SC-008: Performance tests report critical operation latency with millisecond precision
- SC-009: System detects 100% of MCP protocol violations through contract tests
- SC-010: Test environment cleaned completely after execution with zero residual data in 100% of cases

---

## Feature 007: Basic Structured Logging

**Purpose**: Implement production-ready structured logging with automatic credential sanitization, audit trails, performance monitoring, and configurable output destinations.

### User Stories

**US7-1: System Observability for Operations (Priority: P1)**

As an operations engineer, I need structured logs to monitor system health and diagnose issues so production incidents can be quickly resolved.

*Acceptance Criteria*:
- Given system starting, when connecting to RabbitMQ, then connection events logged with details, timestamp, and status
- Given system running, when MCP tool operations execute, then logs capture tool name, parameters, execution time, and result
- Given error occurs, when handled, then error logs include exception type, message, stack trace, and context
- Given logs written, when opening log file, then all entries are valid JSON parseable by standard tools

**US7-2: Security Compliance and Audit Trail (Priority: P1)**

As a security officer, I need automatic sensitive data redaction and complete audit trail so security policies are followed and incidents can be investigated.

*Acceptance Criteria*:
- Given connection string with password, when logged, then password replaced with "[REDACTED]" in all output
- Given any operation involving credentials, when logged, then no credential values appear in any field
- Given MCP tool invoked, when reviewing logs, then unique correlation ID generated at invocation and shared by all related log entries for complete traceability
- Given security audit requested, when reviewing logs, then all operations have complete audit trail (who, what, when, outcome)
- Given log files created, when checking permissions, then files have secure permissions (600 on Unix) preventing unauthorized access

**US7-3: Performance Monitoring and Optimization (Priority: P2)**

As a performance engineer, I need timing information and resource metrics so performance bottlenecks can be identified and optimized.

*Acceptance Criteria*:
- Given any operation executes, when completed, then logs include operation duration in milliseconds
- Given operations running, when reviewing performance logs, then timing shows logging overhead <5ms per operation
- Given high-throughput scenarios, when many operations concurrent, then asynchronous logging prevents blocking

**US7-4: Log Management and Organization (Priority: P2)**

As a system administrator, I need automatic log rotation and organized files so disk space is maintained and logs from specific periods are easily located.

*Acceptance Criteria*:
- Given system runs across midnight, when new day starts, then new log file created with current date in filename
- Given log file reaches 100MB, when more logs written, then file rotated and new file started
- Given log files older than 30 days, when retention policy runs, then old files removed or archived
- Given logs rotated, when compression enabled, then old files compressed with gzip

**US7-5: Debugging and Development Support (Priority: P3)**

As a developer, I need detailed debug-level logs during development so system behavior can be understood and issues troubleshooted.

*Acceptance Criteria*:
- Given log level set to DEBUG, when operations execute, then detailed internal state and variable values logged
- Given log level set to INFO, when operations execute, then debug logs suppressed to reduce noise
- Given issue needs investigation, when sending SIGHUP/SIGUSR1 signal or updating config (Windows polling), then new log level takes effect immediately without process restart

**US7-6: RabbitMQ Log Streaming (Priority: P2 - Optional for MVP)**

As a platform engineer, I need logs published to RabbitMQ exchange in real-time so distributed log aggregation pipelines can be built with multiple independent consumers.

*Acceptance Criteria*:
- Given RabbitMQ destination enabled, when log written, then published to configured topic exchange with routing key {level}.{category} within 500ms
- Given consumer subscribed to "error.*", when ERROR logs generated, then consumer receives only error logs filterable by category
- Given RabbitMQ broker unavailable, when logs written, then system falls back to console without blocking operations and automatically reconnects when broker recovers
- Given multiple consumers with separate queues, when logs published, then all receive copies independently without interference

### Functional Requirements

**Core Logging**:
- FR-001: All logs MUST be structured JSON format with consistent schema
- FR-002: Log levels supported: ERROR, WARN, INFO, DEBUG
- FR-003: Logs MUST write to files in ./logs/ directory with pattern rabbitmq-mcp-{date}.log
- FR-004: Sensitive data (passwords, tokens, API keys, credentials) MUST be automatically redacted before writing; messages >100KB MUST be truncated with "...[truncated]" suffix
- FR-005: Unique correlation IDs MUST be generated at MCP tool invocation and propagated across all log entries for that operation's lifecycle
- FR-006: Connection events MUST be logged (attempts, successes, failures, disconnections)
- FR-007: All MCP tool operations MUST be logged (tool name, parameters, execution time, results)
- FR-008: Error conditions MUST be logged with exception type, message, stack trace, contextual information
- FR-009: Security events MUST be logged (authentication and authorization attempts)
- FR-010: Performance metrics MUST be logged including operation duration (duration_ms field mandatory); minimum throughput: 1000 logs/second on reference hardware (4-core CPU, 8GB RAM, SSD)
- FR-011: All timestamps MUST be ISO 8601 UTC format with Z suffix to avoid timezone/DST ambiguities
- FR-012: Log files MUST rotate based on dual triggers: (1) daily at midnight UTC, (2) when reaching 100MB size
- FR-013: Logs MUST be retained minimum 30 days (configurable)
- FR-014: Secure file permissions (600 files, 700 directories) MUST be attempted; failure MUST log warning to stderr and continue with OS defaults
- FR-015: Logging operations MUST complete in <5ms overhead per operation
- FR-016: Asynchronous logging MUST be supported for high throughput; buffer saturation MUST block writes (zero log loss)
- FR-017: Rotated log files MUST be compressed using gzip
- FR-018: Complete operation lifecycle audit trail MUST be created
- FR-019: When file logging fails, MUST fall back to stderr/console without blocking operations
- FR-020: Multi-line messages (stack traces) MUST be stored as single JSON strings with escaped newlines (\n)
- FR-021: Correlation ID generation failure MUST fall back to timestamp-based ID (timestamp + random) ensuring uniqueness
- FR-022: Concurrent file access MUST use write-through approach, continuing writes while external tools access files
- FR-023: Runtime configuration reload (log level, output settings) MUST be supported via OS signals (SIGHUP/SIGUSR1 on Unix, file polling on Windows) without restart
- FR-024: Schema version field MUST be included in every log entry (semantic versioning: "MAJOR.MINOR.PATCH", starting "1.0.0") for backward-compatible parsing
- FR-025: Graceful shutdown (SIGTERM, SIGINT, normal termination) MUST flush all buffered async logs with max 30s timeout to maintain zero log loss
- FR-026: RabbitMQ AMQP destination MUST be configurable (Priority P2 - optional for MVP); logs published to durable topic exchange with routing keys {level}.{category}; max 500ms latency; connection failures fall back to console; persistent messages (delivery_mode=2) with automatic reconnection (exponential backoff: 3 attempts, 1s base, 2x backoff, 10s max)

### Success Criteria

- SC-001: Operations teams diagnose 90% of production issues using logs alone (measured via post-implementation survey after 30 days)
- SC-002: Security audits trace complete operation lifecycle through correlation IDs with 100% coverage (automated test validation)
- SC-003: Log writing adds <5ms overhead to operations (performance benchmark with 1000-operation sample)
- SC-004: Zero credential/sensitive data instances in logs (automated regex scanning in CI/CD + manual audit)
- SC-005: System maintains continuous operation with controlled disk usage through automatic rotation/retention (7-day test run)
- SC-006: 95% of error investigations start with structured log queries vs code inspection (developer survey after 30 days)
- SC-007: Log files parseable by standard JSON tools without custom parsers (verified with jq, Python json, Elasticsearch ingestion)
- SC-008: Performance bottlenecks identifiable in <10 minutes using logged timing metrics (timed exercise with operations team)

---

## Feature 008: MVP Documentation

**Purpose**: Provide comprehensive, tested documentation enabling users to understand, install, configure, and use the system effectively.

### Documentation Components

**Core Documentation (Constitution Mandated)**:
- README.md: Project overview, installation, quick start (MUST include uvx usage examples, 5-minute quick start)
- docs/API.md: Complete API documentation with TypeScript interfaces for all 3 MCP tools, internal operation documentation, request/response schemas, error codes
- docs/EXAMPLES.md: Practical usage examples (debugging in dev, command-line bash/PowerShell, MCP client config Cursor/VS Code); all examples MUST be tested and functional
- docs/ARCHITECTURE.md: System architecture with diagrams (semantic discovery pattern, OpenAPI generation flow, vector database integration), architectural decisions (ADRs), technical choice justifications
- docs/CONTRIBUTING.md: Contribution guidelines (constitution requirement)
- docs/DEPLOYMENT.md: Deployment guide with env vars, build process (schema/embedding generation), multi-environment deployment, OpenTelemetry config, troubleshooting

**API Documentation (OpenAPI-Driven)**:
- Tool schemas: Complete input/output schemas for search-ids, get-id, call-id
- Operation documentation: Detailed docs for internal operations (auto-generated from OpenAPI)
- Parameter descriptions: Comprehensive parameter docs (extracted from OpenAPI)
- Error codes: Complete error code reference (from OpenAPI responses)
- OpenAPI reference: Document all operations derived from rabbitmq-http-api-openapi.yaml
- AMQP operations: Separately document AMQP protocol operations (not in OpenAPI)

**Usage Examples**:
- CLI examples: Command-line usage for all operations
- MCP client examples: Integration examples for MCP clients
- Common scenarios: Typical use cases and workflows
- Troubleshooting: Common issues and solutions

**Installation Guide**:
- System requirements: Python version, dependencies, system requirements
- Installation methods: pip, uvx, development installation
- Configuration: Environment variables, configuration files
- Quick start: 5-minute getting started guide

### Technical Requirements

**Documentation Format**:
- Markdown format for all documentation
- Consistent structure and formatting
- Code examples with syntax highlighting
- Cross-references and internal links

**Content Quality**:
- Clear, concise, accurate information
- Step-by-step instructions with expected outcomes
- Complete code examples that work out-of-the-box
- Regular updates matching code changes

**Accessibility**:
- Clear language and structure
- Comprehensive examples for different skill levels
- Troubleshooting sections for common issues
- Multiple installation and usage paths

**Maintenance**:
- Documentation versioned with code
- Automated documentation generation where possible
- Regular review and updates
- Community contribution guidelines

### Success Criteria

- New users can get started in <10 minutes
- Examples cover common use cases
- Troubleshooting guide is comprehensive
- Documentation is searchable and navigable
- All code examples are tested and functional (constitution requirement)
- Documentation stays current with code (constitution requirement)
- LGPL license is properly referenced
- uvx usage examples are provided (constitution requirement)

---
