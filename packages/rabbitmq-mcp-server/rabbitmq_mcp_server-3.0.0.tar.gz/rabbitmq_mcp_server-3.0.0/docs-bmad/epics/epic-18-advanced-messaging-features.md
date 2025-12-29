# Epic 18: Advanced Messaging Features

**Goal**: Implement advanced RabbitMQ messaging features including delayed messages, message priority, TTL (Time-To-Live), and message headers routing.

**Value**: Enables sophisticated messaging patterns required for complex event-driven architectures, scheduled tasks, and priority-based processing.

**Priority**: Low (Advanced feature)

---

## Story 18.1: Delayed Message Publishing

As a developer,
I want to publish messages with delivery delay,
So that I can implement scheduled tasks and deferred processing without external schedulers.

**Acceptance Criteria:**

**Given** RabbitMQ with delayed message exchange plugin installed
**When** I publish message with delay
**Then** message is delayed by specified duration before routing to queues

**And** delay configuration: --delay parameter (milliseconds) or x-delay message header

**And** delay range: 0ms to 24 hours (configurable max)

**And** delayed exchange type: x-delayed-message with arguments: {"x-delayed-type": "topic"}

**And** CLI command: rabbitmq-mcp-server message publish --exchange=delayed-events --routing-key=task --delay=60000 --payload='{"task": "cleanup"}'

**And** validation: verify delayed message exchange plugin enabled, error if not available

**And** use cases documented: scheduled notifications, retry with backoff, rate limiting

**Prerequisites:** Epic 4 complete (message publishing)

**Technical Notes:**
- Requires RabbitMQ delayed message exchange plugin: rabbitmq-plugins enable rabbitmq_delayed_message_exchange
- Create delayed exchange: PUT /api/exchanges/{vhost}/{name} with type: "x-delayed-message", arguments: {"x-delayed-type": "topic"}
- Publish with delay: set x-delay header: properties.headers = {"x-delay": 60000}
- Delay limits: plugin default max is 2^32ms (~50 days), configure via policy
- Performance: delayed messages consume memory (stored in plugin), monitor queue depth
- Alternative: use TTL + DLX pattern (message expires, routes to DLX, reprocessed)

---

## Story 18.2: Message Priority Queues

As a developer,
I want to publish messages with priority levels,
So that high-priority messages are processed before low-priority ones.

**Acceptance Criteria:**

**Given** queue configured with max-priority
**When** I publish messages with different priorities
**Then** messages are delivered to consumers in priority order (higher priority first)

**And** priority levels: 0 (lowest) to 10 (highest), configurable per queue

**And** queue configuration: x-max-priority argument (e.g., 10) when creating queue

**And** message priority: set priority property when publishing (0-10)

**And** CLI command: rabbitmq-mcp-server message publish --exchange=tasks --routing-key=job --priority=9 --payload='{"job": "urgent"}'

**And** consumer behavior: high-priority messages dequeued first, priorities respected across batches

**And** performance impact documented: priority queues have ~10% performance overhead vs standard queues

**And** use cases: urgent alerts, interactive requests vs batch jobs, SLA-based processing

**Prerequisites:** Epic 4 complete (message publishing), Story 3.2 (queue creation)

**Technical Notes:**
- Configure queue: PUT /api/queues/{vhost}/{name} with arguments: {"x-max-priority": 10}
- Publish with priority: properties.priority = 9 (0-10 range)
- Consumer prefetch: with priority queues, prefetch should be 1 to ensure priorities respected
- Performance: priority queues use more memory (maintain priority heaps), slower enqueue/dequeue
- Best practice: use 3-5 priority levels (not 10), reduce overhead
- Monitor: track message distribution across priorities (ensure not all high priority)

---

## Story 18.3: Message TTL (Time-To-Live)

As a developer,
I want to set TTL on messages and queues,
So that stale messages are automatically expired and removed.

**Acceptance Criteria:**

**Given** message or queue with TTL configured
**When** TTL expires
**Then** message is removed from queue (dead-lettered if DLX configured, otherwise discarded)

**And** message-level TTL: set expiration property when publishing (milliseconds as string, e.g., "60000")

**And** queue-level TTL: x-message-ttl argument when creating queue (applies to all messages)

**And** TTL precedence: message TTL overrides queue TTL (if message TTL < queue TTL)

**And** CLI command: rabbitmq-mcp-server message publish --exchange=events --routing-key=temp --ttl=60000 --payload='{"event": "temporary"}'

**And** expired messages logged: {event: "message_expired", queue: "...", count: 10}

**And** DLX integration: expired messages route to DLX if configured (x-dead-letter-exchange)

**And** use cases: cache invalidation, temporary data, event deduplication windows

**Prerequisites:** Epic 4 complete (message publishing), Story 10.2 (DLX)

**Technical Notes:**
- Message TTL: properties.expiration = "60000" (string format, milliseconds)
- Queue TTL: arguments: {"x-message-ttl": 60000} (integer format)
- Expiration: message expires when at head of queue (not based on publish time for efficiency)
- DLX routing: expired messages have x-death header: reason="expired"
- Queue TTL: x-expires argument (queue deleted if unused for duration)
- Monitor: track expired message count (GET /api/queues/{vhost}/{name} has message_stats.expire)

---
