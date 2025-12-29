# Epic 3: Topology Operations

**Goal**: Implement comprehensive RabbitMQ topology management (queues, exchanges, bindings) with safety validations that prevent accidental data loss and resource misconfiguration.

**Value**: Enables users to manage RabbitMQ infrastructure declaratively with built-in guardrails, reducing the risk of destructive operations during incident response or routine maintenance. Delivers **zero context switching** - manage infrastructure without leaving AI conversation.

**Product Differentiator**: Built-in safety validations prevent destructive operations (queue deletion with messages, exchange deletion with active bindings) - enterprise-grade protection that competitors lack.

**Covered FRs**: FR-008, FR-009, FR-010, FR-023

---

## Story 3.1: List Queues Operation

As a DevOps engineer,
I want to list all queues in a vhost with statistics,
So that I can monitor queue health and identify issues like high message backlogs or idle queues.

**Acceptance Criteria:**

**Given** connected to RabbitMQ with queues in vhost "/"
**When** I execute "queues.list" operation for vhost="/"
**Then** I receive list of all queues with details: name, vhost, durable, auto_delete, arguments

**And** statistics include: messages, messages_ready, messages_unacknowledged, consumers, memory (bytes)

**And** response includes state: running, idle, flow (flow control active)

**And** operation completes in <200ms for up to 1000 queues

**And** empty vhost returns empty list [] (not error)

**And** non-existent vhost returns error: "Virtual host '{vhost}' does not exist"

**And** results can be filtered by: name_pattern (regex), state, consumer_count (e.g., consumers=0)

**And** results can be sorted by: name, messages, consumers, memory

**Prerequisites:** Story 2.3 (HTTP client)

**Technical Notes:**
- HTTP GET /api/queues/{vhost}
- Pagination support for large queue lists (page_size, page parameters)
- Include queue-level metrics: message_rates (publish, deliver, ack)
- Consider caching for frequent queries (TTL: 5s)
- Implement filters in query parameters: ?name=pattern&state=running
- Format memory values in human-readable units (KB, MB, GB)

---

## Story 3.2: Create Queue Operation

As a DevOps engineer,
I want to create queues with configurable properties (durability, TTL, DLX, etc.),
So that I can provision messaging infrastructure matching my application requirements.

**Acceptance Criteria:**

**Given** valid queue configuration
**When** I execute "queues.create" with name="orders", vhost="/", durable=true
**Then** queue is created on RabbitMQ server

**And** queue properties are set: durable, auto_delete, arguments (x-message-ttl, x-dead-letter-exchange, etc.)

**And** successful creation returns: status="success", queue_details={name, vhost, properties}

**And** duplicate queue with same properties is idempotent (no error)

**And** duplicate queue with different properties returns error: "Queue 'orders' already exists with different configuration"

**And** invalid queue name (special chars, >255 length) returns validation error before HTTP call

**And** queue name validation: alphanumeric, hyphen, underscore, period allowed; max 255 chars

**And** operation completes in <100ms

**Prerequisites:** Story 2.3 (HTTP client), Story 1.3 (Pydantic schemas)

**Technical Notes:**
- HTTP PUT /api/queues/{vhost}/{name}
- Request body: {"durable": true, "auto_delete": false, "arguments": {...}}
- Common arguments: x-message-ttl (milliseconds), x-max-length (max messages), x-dead-letter-exchange (DLX name), x-queue-type (classic/quorum)
- Validate arguments before sending (e.g., x-message-ttl must be positive integer)
- Document queue type differences (classic vs quorum) in operation description
- Test with various queue configurations

---

## Story 3.3: Delete Queue Operation with Safety Validation

As a DevOps engineer,
I want to delete queues with safety checks that prevent accidental data loss,
So that I don't inadvertently destroy queues containing important messages.

**Acceptance Criteria:**

**Given** a queue "orders" with messages=100 and consumers=2
**When** I attempt "queues.delete" without --force flag
**Then** operation is blocked with error: "Queue 'orders' has 100 messages and 2 consumers. Use --force to confirm deletion."

**And** --force flag allows deletion: "queues.delete" with force=true succeeds

**And** empty queue (messages=0, consumers=0) deletes without requiring --force

**And** successful deletion returns: status="success", message="Queue 'orders' deleted"

**And** non-existent queue returns error: "Queue 'orders' not found in vhost '/'"

**And** deletion operation completes in <100ms

**And** deletion is logged in audit trail with correlation ID

**Prerequisites:** Story 2.3 (HTTP client), Story 3.1 (list queues for validation)

**Technical Notes:**
- HTTP DELETE /api/queues/{vhost}/{name}
- Pre-deletion validation: GET queue details, check messages + consumers
- Query parameters: ?if-empty=true (server-side validation), ?if-unused=true
- Safety check can be bypassed only with explicit force=true parameter
- Consider dry-run mode: returns what would be deleted without executing
- Audit log entry: {action: "queue.delete", resource: "orders", vhost: "/", forced: true}

---

## Story 3.4: Purge Queue Operation

As a DevOps engineer,
I want to purge all messages from a queue without deleting the queue itself,
So that I can clear stuck messages during troubleshooting while preserving queue configuration and consumers.

**Acceptance Criteria:**

**Given** a queue "orders" with messages=500
**When** I execute "queues.purge" for queue="orders", vhost="/"
**Then** all messages are removed from the queue

**And** queue remains with same configuration (durable, arguments, etc.)

**And** active consumers remain connected

**And** operation returns: status="success", purged_message_count=500

**And** purge operation completes in <500ms for up to 10,000 messages

**And** purging empty queue succeeds with purged_message_count=0 (not error)

**And** non-existent queue returns error: "Queue 'orders' not found"

**And** purge is logged in audit trail

**Prerequisites:** Story 2.3 (HTTP client), Story 3.1 (list queues)

**Technical Notes:**
- HTTP DELETE /api/queues/{vhost}/{name}/contents
- Returns message_count from response body
- Consider confirmation prompt for queues with >1000 messages
- No undo possible - messages are permanently deleted
- Document use case: troubleshooting stuck messages, clearing test data
- Test with large message counts (10k, 100k)

---

## Story 3.5: List Exchanges Operation

As a DevOps engineer,
I want to list all exchanges in a vhost with their types and properties,
So that I can understand message routing topology and identify configuration issues.

**Acceptance Criteria:**

**Given** connected to RabbitMQ with exchanges in vhost "/"
**When** I execute "exchanges.list" operation for vhost="/"
**Then** I receive list of all exchanges with details: name, vhost, type (direct/topic/fanout/headers), durable, auto_delete, internal, arguments

**And** system exchanges are included: amq.direct, amq.topic, amq.fanout, amq.headers, amq.match, default exchange ("")

**And** statistics include: message_rates (publish_in, publish_out)

**And** operation completes in <200ms for up to 1000 exchanges

**And** empty vhost returns system exchanges only (amq.* + default)

**And** results can be filtered by: type, name_pattern

**And** results can be sorted by: name, type, message_rate

**Prerequisites:** Story 2.3 (HTTP client)

**Technical Notes:**
- HTTP GET /api/exchanges/{vhost}
- Exchange types: direct (exact routing key), topic (pattern matching with * and #), fanout (broadcast), headers (header-based routing)
- Default exchange "" routes to queue with matching name (special case)
- System exchanges (amq.* prefix) are built-in and cannot be deleted
- Include exchange message rates if available
- Document exchange type use cases in operation description

---

## Story 3.6: Create Exchange Operation

As a DevOps engineer,
I want to create exchanges with specific types and properties,
So that I can implement custom message routing patterns for my applications.

**Acceptance Criteria:**

**Given** valid exchange configuration
**When** I execute "exchanges.create" with name="events", vhost="/", type="topic", durable=true
**Then** exchange is created on RabbitMQ server

**And** exchange type is set: direct, topic, fanout, or headers

**And** exchange properties are set: durable, auto_delete, internal, arguments

**And** successful creation returns: status="success", exchange_details={name, vhost, type, properties}

**And** duplicate exchange with same properties is idempotent (no error)

**And** duplicate exchange with different type returns error: "Exchange 'events' already exists with type 'direct', cannot change to 'topic'"

**And** invalid exchange name (special chars, >255 length) returns validation error

**And** attempting to create system exchange (amq.* prefix) returns error: "Cannot create exchanges with 'amq.' prefix (reserved)"

**And** operation completes in <100ms

**Prerequisites:** Story 2.3 (HTTP client), Story 1.3 (Pydantic schemas)

**Technical Notes:**
- HTTP PUT /api/exchanges/{vhost}/{name}
- Request body: {"type": "topic", "durable": true, "auto_delete": false, "internal": false, "arguments": {...}}
- Exchange types: direct, topic, fanout, headers (validate before sending)
- Internal exchanges cannot be published to directly (only via bindings)
- Common arguments: alternate-exchange (for unroutable messages)
- Validate: name format, type in allowed list, arguments per exchange type
- Test each exchange type with appropriate routing scenarios

---

## Story 3.7: Delete Exchange Operation with Protection

As a DevOps engineer,
I want to delete exchanges with safety checks that prevent breaking active message routing,
So that I don't accidentally disrupt message flow in production.

**Acceptance Criteria:**

**Given** an exchange "events" with active bindings
**When** I attempt "exchanges.delete" without --force flag
**Then** operation is blocked with error: "Exchange 'events' has 5 active bindings. Use --force to confirm deletion."

**And** --force flag allows deletion: "exchanges.delete" with force=true succeeds

**And** exchange with no bindings deletes without requiring --force

**And** attempting to delete system exchange returns error: "Cannot delete system exchange 'amq.topic'"

**And** attempting to delete default exchange ("") returns error: "Cannot delete default exchange"

**And** successful deletion returns: status="success", message="Exchange 'events' deleted"

**And** deletion operation completes in <100ms

**And** deletion is logged in audit trail

**Prerequisites:** Story 2.3 (HTTP client), Story 3.5 (list exchanges), Story 3.8 (list bindings for validation)

**Technical Notes:**
- HTTP DELETE /api/exchanges/{vhost}/{name}
- Pre-deletion validation: GET /api/exchanges/{vhost}/{name}/bindings/source to check active bindings
- Query parameter: ?if-unused=true (server-side validation)
- Protect system exchanges: amq.direct, amq.topic, amq.fanout, amq.headers, amq.match, default ("")
- Safety check requires explicit force=true parameter
- Consider cascade deletion option (delete bindings too) vs error
- Audit log entry: {action: "exchange.delete", resource: "events", vhost: "/", bindings_count: 5, forced: true}

---

## Story 3.8: List Bindings Operation

As a DevOps engineer,
I want to list all bindings (exchange-to-queue and exchange-to-exchange),
So that I can understand complete message routing paths and debug routing issues.

**Acceptance Criteria:**

**Given** connected to RabbitMQ with bindings configured
**When** I execute "bindings.list" operation for vhost="/"
**Then** I receive list of all bindings with details: source (exchange), destination (queue or exchange), destination_type (queue/exchange), routing_key, arguments

**And** bindings can be filtered by: source (exchange name), destination (queue/exchange name), vhost

**And** operation returns: source="events", destination="orders-queue", routing_key="order.created", vhost="/", destination_type="queue"

**And** exchange-to-exchange bindings have destination_type="exchange"

**And** operation completes in <200ms for up to 10,000 bindings

**And** empty vhost with no bindings returns empty list []

**And** results can be sorted by: source, destination, routing_key

**Prerequisites:** Story 2.3 (HTTP client)

**Technical Notes:**
- HTTP GET /api/bindings or /api/bindings/{vhost}
- Can also query specific bindings: GET /api/exchanges/{vhost}/{exchange}/bindings/source
- Or queue bindings: GET /api/queues/{vhost}/{queue}/bindings
- Bindings are directional: source (exchange) → destination (queue/exchange)
- Routing key can be empty (fanout exchanges), exact match (direct), pattern (topic with * and #)
- Arguments used for headers exchange routing
- Include properties_key in response (unique binding identifier)

---

## Story 3.9: Create Binding Operation

As a DevOps engineer,
I want to create bindings between exchanges and queues (or exchanges and exchanges),
So that I can define custom message routing rules for my applications.

**Acceptance Criteria:**

**Given** existing exchange "events" (topic) and queue "orders-queue"
**When** I execute "bindings.create" with source="events", destination="orders-queue", routing_key="order.*", vhost="/"
**Then** binding is created on RabbitMQ server

**And** destination_type is inferred or specified: "queue" or "exchange"

**And** routing key supports wildcards for topic exchanges: * (one word), # (zero or more words)

**And** duplicate binding (same source, destination, routing_key) is idempotent (no error)

**And** binding to non-existent exchange returns error: "Source exchange 'events' not found"

**And** binding to non-existent queue returns error: "Destination queue 'orders-queue' not found"

**And** invalid routing key for exchange type returns validation error

**And** operation completes in <100ms

**And** binding creation is logged in audit trail

**Prerequisites:** Story 2.3 (HTTP client), Story 3.1 (list queues), Story 3.5 (list exchanges)

**Technical Notes:**
- HTTP POST /api/bindings/{vhost}/e/{exchange}/q/{queue} (exchange-to-queue)
- Or POST /api/bindings/{vhost}/e/{source}/e/{destination} (exchange-to-exchange)
- Request body: {"routing_key": "order.*", "arguments": {...}}
- Pre-creation validation: verify source exchange exists, verify destination exists
- Routing key validation per exchange type:
  - Fanout: routing key ignored (can be empty)
  - Direct: exact match (no wildcards)
  - Topic: supports * (one word), # (zero or more words), . separators
  - Headers: routing key optional, uses arguments for matching
- Test binding creation with each exchange type
- Document routing key patterns in operation description

---

## Story 3.10: Delete Binding Operation

As a DevOps engineer,
I want to delete specific bindings,
So that I can modify message routing without recreating entire topology.

**Acceptance Criteria:**

**Given** an existing binding: source="events", destination="orders-queue", routing_key="order.*"
**When** I execute "bindings.delete" with source, destination, routing_key, vhost
**Then** the specific binding is deleted from RabbitMQ

**And** other bindings between same source and destination (different routing keys) remain intact

**And** successful deletion returns: status="success", message="Binding deleted"

**And** non-existent binding returns error: "Binding not found: source='events', destination='orders-queue', routing_key='order.*'"

**And** deletion operation completes in <100ms

**And** deletion is logged in audit trail

**And** no confirmation required (bindings don't store data, low risk)

**Prerequisites:** Story 2.3 (HTTP client), Story 3.8 (list bindings)

**Technical Notes:**
- HTTP DELETE /api/bindings/{vhost}/e/{exchange}/q/{queue}/{properties_key}
- properties_key is unique identifier for binding (hash of routing_key + arguments)
- Alternative: DELETE with query parameters: ?routing_key=order.*&arguments_hash=...
- Pre-deletion validation: verify binding exists (optional optimization)
- Deleting binding doesn't delete exchange or queue
- Multiple bindings can exist between same source/destination with different routing keys
- Audit log entry: {action: "binding.delete", source: "events", destination: "orders-queue", routing_key: "order.*"}

---

## Story 3.11: Vhost Validation Middleware

As a developer,
I want all topology operations to validate vhost existence before execution,
So that operations fail fast with clear errors instead of obscure HTTP 404 responses.

**Acceptance Criteria:**

**Given** any topology operation (queues, exchanges, bindings)
**When** operation is executed with vhost="/invalid"
**Then** validation occurs before HTTP API call

**And** non-existent vhost returns error: "Virtual host '/invalid' does not exist. Available vhosts: [/, /staging, /prod]"

**And** validation check completes in <50ms

**And** validation result is cached (TTL: 5 minutes) to avoid repeated checks

**And** vhost existence check uses: GET /api/vhosts

**And** vhost list is refreshed when creation/deletion operations occur

**Prerequisites:** Story 2.3 (HTTP client)

**Technical Notes:**
- Implement as middleware or decorator: @validate_vhost
- Cache vhost list in memory with TTL (5 minutes default)
- Vhost validation happens before parameter validation (fail fast)
- Common vhosts: / (default), /staging, /prod, /dev
- Vhost names can contain: letters, digits, hyphen, underscore, period
- Special encoding for vhost in URLs: / → %2F (URL encoding)
- Provide helpful error messages listing available vhosts

---
