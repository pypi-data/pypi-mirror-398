# Epic 4: Message Publishing & Consumption

**Goal**: Implement AMQP messaging operations (publish, consume, acknowledge) that enable sending and receiving messages through RabbitMQ with proper flow control and acknowledgment handling.

**Value**: Completes the MCP server functionality by adding actual messaging capabilities alongside topology management, enabling full-cycle message queue operations from AI assistants. Enables **incident resolution without leaving conversation** - inspect, publish, consume all in AI assistant.

**Product Differentiator**: First RabbitMQ MCP server with complete AMQP messaging support - not just topology management but actual message operations with enterprise-grade validation.

**Covered FRs**: FR-005, FR-011, FR-012, FR-013

---

## Story 4.1: Publish Message to Exchange

As a developer,
I want to publish messages to exchanges with routing keys and configurable properties,
So that I can send messages into RabbitMQ message flows for processing by consumers.

**Acceptance Criteria:**

**Given** connected via AMQP to RabbitMQ with existing exchange "events"
**When** I execute "amqp.publish" with exchange="events", routing_key="order.created", payload={"order_id": 123}
**Then** message is published to RabbitMQ via AMQP protocol

**And** payload types supported: JSON object (serialized), plain text string, binary data (base64)

**And** message properties configurable: content_type, content_encoding, delivery_mode (1=transient, 2=persistent), priority (0-9), correlation_id, reply_to, expiration (TTL in ms), message_id, timestamp, type, user_id, app_id, headers (dict)

**And** successful publish returns: status="success", message_id={generated_or_provided}

**And** exchange existence is validated before publish

**And** non-existent exchange returns error: "Exchange 'events' not found"

**And** publish operation completes in <100ms

**And** publish is logged with: correlation_id, exchange, routing_key, payload_size (bytes)

**Prerequisites:** Story 2.2 (AMQP connection), Story 3.5 (list exchanges for validation)

**Technical Notes:**
- Use pika.BasicProperties for message properties
- Default content_type: application/json (if payload is dict/list), text/plain (if string)
- Default delivery_mode: 2 (persistent) for durability
- Serialize JSON payloads automatically: json.dumps(payload)
- Support binary payloads: base64 encoded strings decoded before publish
- Validate: exchange exists, routing_key format, payload size (<1MB default limit)
- Publisher confirms optional (confirms not required for MVP but document for future)
- Log payload size, not content (security - avoid leaking sensitive data)

---

## Story 4.2: Consume Messages from Queue

As a developer,
I want to subscribe to queues and receive messages as they arrive,
So that I can monitor message flow, inspect message content, or trigger automated actions.

**Acceptance Criteria:**

**Given** connected via AMQP to RabbitMQ with existing queue "orders-queue"
**When** I execute "amqp.consume" with queue="orders-queue", prefetch_count=10
**Then** consumer is registered on the queue

**And** messages are delivered asynchronously as they arrive

**And** each message includes: delivery_tag, exchange, routing_key, payload (decoded), properties, redelivered (bool)

**And** prefetch_count limits unacknowledged messages (flow control): default=10, max=1000

**And** consumer handles at least 100 concurrent messages without blocking

**And** message delivery latency <50ms per message

**And** queue existence is validated before consuming

**And** non-existent queue returns error: "Queue 'orders-queue' not found"

**And** consume operation returns: consumer_tag, queue, prefetch_count

**Prerequisites:** Story 2.2 (AMQP connection), Story 3.1 (list queues for validation)

**Technical Notes:**
- Use pika.channel.basic_consume for subscription
- Prefetch count via channel.basic_qos(prefetch_count=10)
- Consumer callback: def on_message(ch, method, properties, body)
- Decode payload based on content_type: application/json → json.loads(), text/plain → str, else binary
- Consumer tag: unique identifier for this consumer (generated or provided)
- Support multiple consumers on same queue (round-robin delivery)
- No automatic acknowledgment (manual ack required via Story 4.3)
- Redelivered flag indicates message was previously delivered but not acknowledged
- Handle consumer cancellation gracefully

---

## Story 4.3: Acknowledge Messages (Ack/Nack/Reject)

As a developer,
I want to acknowledge, negatively acknowledge, or reject messages after processing,
So that RabbitMQ knows message processing status and can handle failures appropriately (requeue or DLX).

**Acceptance Criteria:**

**Given** consumed message with delivery_tag=123
**When** I execute "amqp.ack" with delivery_tag=123
**Then** message is positively acknowledged and removed from queue

**And** "amqp.nack" with delivery_tag=123, requeue=true returns message to queue for redelivery

**And** "amqp.nack" with delivery_tag=123, requeue=false sends message to DLX (if configured) or discards

**And** "amqp.reject" with delivery_tag=123 is equivalent to nack with requeue=false

**And** multiple=true parameter acknowledges all messages up to delivery_tag

**And** invalid delivery_tag returns error: "Invalid delivery tag: {tag}"

**And** duplicate acknowledgment returns error: "Message {tag} already acknowledged"

**And** acknowledgment operations complete in <10ms

**And** acknowledgments are logged with: correlation_id, delivery_tag, action (ack/nack/reject), requeue

**Prerequisites:** Story 4.2 (consume messages)

**Technical Notes:**
- Use pika methods: basic_ack(delivery_tag), basic_nack(delivery_tag, requeue=True/False), basic_reject(delivery_tag, requeue=False)
- Delivery tags are channel-specific and sequential (1, 2, 3, ...)
- Multiple=True: acks all messages with delivery_tag ≤ specified tag (batch ack)
- Nack with requeue=True: message returns to queue (potentially redelivered to same or different consumer)
- Nack with requeue=False: message goes to DLX if configured, otherwise discarded permanently
- Track delivery tags in-flight to prevent duplicate acks
- Handle edge case: consumer cancelled before ack (delivery tag no longer valid)
- Document DLX setup for failed message handling

---

## Story 4.4: Message Property Validation

As a developer,
I want message properties validated before publishing,
So that I catch configuration errors before messages enter RabbitMQ (e.g., invalid priority, bad TTL format).

**Acceptance Criteria:**

**Given** publish operation with message properties
**When** properties are validated
**Then** delivery_mode accepts: 1 (transient) or 2 (persistent) only

**And** priority accepts: 0-9 (10 levels) or null

**And** expiration (TTL) accepts: positive integer (milliseconds) as string (e.g., "60000" for 1 minute)

**And** timestamp accepts: Unix timestamp (integer) or ISO 8601 datetime string

**And** content_type accepts: standard MIME types (application/json, text/plain, application/octet-stream, etc.)

**And** correlation_id, message_id, type, app_id, user_id accept: strings ≤255 chars

**And** headers accepts: dict with string keys and simple values (str, int, bool, null)

**And** invalid properties return validation error before AMQP call: "Property 'priority' must be 0-9, got: 15"

**Prerequisites:** Story 4.1 (publish message)

**Technical Notes:**
- Implement Pydantic model: MessageProperties with field validators
- Expiration quirk: RabbitMQ expects string (not integer): "60000" not 60000
- Headers support nested structures but keep simple for MVP (avoid deep nesting)
- Standard content types: application/json, text/plain, text/csv, application/xml, application/octet-stream
- User_id requires authentication (must match connected username or have impersonation permission)
- Timestamp: if not provided, RabbitMQ doesn't auto-generate (application responsibility)
- Document property semantics in operation description

---

## Story 4.5: Payload Size Limits and Validation

As a developer,
I want payload size limits enforced before publishing,
So that I don't crash RabbitMQ or degrade performance with oversized messages.

**Acceptance Criteria:**

**Given** publish operation with payload
**When** payload size is checked
**Then** payloads ≤1MB (1,048,576 bytes) are accepted by default

**And** payloads >1MB return error: "Payload size {size}MB exceeds limit of 1MB. Consider splitting or using external storage."

**And** payload size limit is configurable via MAX_MESSAGE_SIZE env var (in bytes)

**And** size check occurs before serialization (operates on original data structure size estimate)

**And** binary payloads (base64 encoded) are decoded to calculate actual size

**And** compressed payloads are supported (content_encoding: gzip) and size refers to compressed size

**And** size validation completes in <5ms

**Prerequisites:** Story 4.1 (publish message)

**Technical Notes:**
- Default limit: 1MB (RabbitMQ default is 128MB but 1MB is sensible application default)
- Calculate size: len(json.dumps(payload).encode('utf-8')) for JSON
- For large messages: recommend chunking, external storage (S3, blob storage), or streaming protocols
- Document alternative approaches: chunk messages, reference pattern (message contains URL to data)
- Consider warning threshold: >100KB warns but allows (approaching limit)
- RabbitMQ max_message_size config: frame_max (131072 bytes default) can be increased server-side

---

## Story 4.6: Consumer Lifecycle Management

As a developer,
I want to start, stop, and monitor consumers,
So that I can control message consumption dynamically (pause during maintenance, resume after fix).

**Acceptance Criteria:**

**Given** active consumer with consumer_tag="consumer-123" on queue="orders-queue"
**When** I execute "amqp.consumer.cancel" with consumer_tag="consumer-123"
**Then** consumer is stopped gracefully

**And** no new messages are delivered to this consumer

**And** in-flight messages (already delivered, unacknowledged) remain valid until acknowledged or timeout

**And** consumer cancel returns: status="success", consumer_tag="consumer-123", queue="orders-queue"

**And** non-existent consumer_tag returns error: "Consumer 'consumer-123' not found"

**And** consumer status is queryable via "amqp.consumer.list": returns active consumers with consumer_tag, queue, prefetch_count, message_count (delivered)

**And** consumer restart uses same queue with new consumer_tag

**Prerequisites:** Story 4.2 (consume messages)

**Technical Notes:**
- Use pika.channel.basic_cancel(consumer_tag) for graceful shutdown
- Consumer tags: auto-generated (UUID) or user-provided (must be unique per channel)
- Track active consumers in memory: {consumer_tag: {queue, prefetch, started_at, message_count}}
- Consumer cancellation doesn't acknowledge in-flight messages (manual ack still required)
- Server-side consumer cancellation (queue deleted, connection lost) triggers callback
- Implement consumer monitoring: message rate, last delivery timestamp, consumer lag
- Document consumer recovery after reconnection (consumers don't survive connection loss)

---

## Story 4.7: Message Routing Validation (Pre-Publish)

As a developer,
I want validation that messages will route successfully before publishing,
So that I catch routing issues early (e.g., routing key doesn't match any binding).

**Acceptance Criteria:**

**Given** publish operation with exchange="events", routing_key="order.created"
**When** routing validation is enabled
**Then** system checks if routing key matches at least one binding from the exchange

**And** direct exchange: exact match required between routing_key and binding routing_key

**And** topic exchange: pattern match required (routing_key matches binding pattern with * and #)

**And** fanout exchange: routing ignored (always routes to all bound queues)

**And** headers exchange: header matching logic (complex, skip for MVP validation)

**And** unroutable message (no matching bindings) returns warning: "Message may not route: no bindings match routing_key 'order.created' on exchange 'events'"

**And** validation is optional (WARNING_ONLY mode: warns but publishes, STRICT mode: blocks publish)

**And** validation check completes in <50ms

**Prerequisites:** Story 4.1 (publish message), Story 3.8 (list bindings)

**Technical Notes:**
- Validation mode configurable: NONE (skip), WARNING (log but allow), STRICT (block publish)
- Retrieve bindings from exchange: GET /api/exchanges/{vhost}/{exchange}/bindings/source
- Topic pattern matching: implement wildcard logic (* = one word, # = zero or more words)
- Cache bindings per exchange (TTL: 1 minute) to avoid repeated API calls
- Consider performance: skip validation for high-throughput scenarios (configurable)
- Alternative: use mandatory flag in AMQP publish (message returned if unroutable)
- Document validation limitations (doesn't guarantee consumer is listening)

---

## Story 4.8: AMQP Operation Schemas (Manual)

As a developer,
I want manually maintained Pydantic schemas for AMQP operations,
So that publish, consume, and acknowledge operations have type-safe parameters like HTTP operations.

**Acceptance Criteria:**

**Given** AMQP operations not in OpenAPI specification
**When** schemas are defined manually
**Then** PublishSchema includes: exchange (str, required), routing_key (str, default=""), payload (Any, required), properties (MessageProperties, optional)

**And** ConsumeSchema includes: queue (str, required), prefetch_count (int, default=10, range 1-1000), consumer_tag (str, optional), no_ack (bool, default=False)

**And** AckSchema includes: delivery_tag (int, required), multiple (bool, default=False)

**And** NackSchema includes: delivery_tag (int, required), requeue (bool, default=True), multiple (bool, default=False)

**And** RejectSchema includes: delivery_tag (int, required), requeue (bool, default=False)

**And** all schemas use Pydantic validators for type safety and validation

**And** schemas generate JSON Schema for MCP tool definitions

**Prerequisites:** Story 1.3 (Pydantic schemas understanding)

**Technical Notes:**
- Create file: src/schemas/amqp_schemas.py
- MessageProperties nested model: delivery_mode, priority, content_type, etc. (from Story 4.4)
- Payload validation: accept dict/list (JSON), str (text), bytes (binary)
- Consumer_tag validation: alphanumeric, hyphen, underscore; max 255 chars
- Delivery_tag validation: positive integer (starts at 1)
- Schemas used by MCP tools: amqp.publish, amqp.consume, amqp.ack, amqp.nack, amqp.reject
- Test schema validation with valid and invalid inputs

---
