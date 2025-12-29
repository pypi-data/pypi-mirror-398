# Epic 10: Advanced Retry & Dead Letter Queue (DLQ) Patterns

**Goal**: Implement sophisticated retry mechanisms and DLQ handling patterns that provide resilience for message processing failures with configurable backoff strategies.

**Value**: Enables production-grade message reliability, automatic failure recovery, and observability into message processing issues - critical for enterprise adoption.

**Priority**: Medium (Post-MVP enhancement)

---

## Story 10.1: Exponential Backoff Retry for Message Publishing

As a developer,
I want automatic retry with exponential backoff when message publishing fails,
So that transient errors don't cause message loss.

**Acceptance Criteria:**

**Given** a message publish operation that fails
**When** retry logic executes
**Then** publish is retried with exponential backoff: 100ms, 200ms, 400ms, 800ms, 1600ms (max 5 attempts by default)

**And** retry count is configurable: PUBLISH_RETRY_MAX_ATTEMPTS (default: 5)

**And** backoff multiplier configurable: PUBLISH_RETRY_BACKOFF_MULTIPLIER (default: 2)

**And** max backoff configurable: PUBLISH_RETRY_MAX_BACKOFF_MS (default: 5000ms)

**And** retryable errors: connection failures, timeout errors, 503 service unavailable

**And** non-retryable errors: validation failures, 404 not found, authentication errors (fail immediately)

**And** retry attempts logged: {event: "publish_retry", attempt: 3, next_retry_in: "800ms", error: "timeout"}

**And** after max attempts, operation fails with error: "Failed to publish after 5 attempts"

**Prerequisites:** Epic 4 complete (message publishing)

**Technical Notes:**
- Use tenacity library for retry logic: @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=100, max=5000))
- Retry decision: if isinstance(error, (ConnectionError, TimeoutError, HTTPError(503))): retry
- Circuit breaker pattern: after N consecutive failures, open circuit (fail fast for period)
- Metrics: track retry_attempts, retry_success_rate, circuit_breaker_opens
- Idempotency: ensure retried publishes don't duplicate (use message_id)

---

## Story 10.2: Dead Letter Exchange (DLX) Configuration & Monitoring

As a DevOps engineer,
I want to configure queues with dead letter exchanges for failed messages,
So that I can capture, inspect, and retry failed messages without losing them.

**Acceptance Criteria:**

**Given** queue configuration with DLX settings
**When** I create queue with x-dead-letter-exchange argument
**Then** queue is configured to route failed/rejected messages to specified DLX

**And** DLX configuration includes: dead_letter_exchange (name), dead_letter_routing_key (optional)

**And** messages sent to DLX when: consumer rejects (nack with requeue=false), message TTL expires, queue length limit exceeded

**And** DLX messages include headers: x-death (array with death reason, queue, time, count)

**And** CLI command: rabbitmq-mcp-server queue create --name=orders --dlx=failed-orders-exchange

**And** monitoring command: rabbitmq-mcp-server queue inspect-dlx --queue=orders (shows DLX config and failed message count)

**And** DLX queue created automatically if doesn't exist (with naming convention: {queue}-dlx)

**Prerequisites:** Epic 3 complete (queue operations)

**Technical Notes:**
- DLX arguments: {"x-dead-letter-exchange": "failed-orders-exchange", "x-dead-letter-routing-key": "failed.orders"}
- Create DLX pattern: create exchange (type: topic), create DLX queue, bind queue to exchange
- x-death header: RabbitMQ adds automatically, contains: reason (rejected/expired/maxlen), queue, time, count (redelivery count)
- Monitor DLX: GET /api/queues/{vhost}/{queue}-dlx for message count
- Retry from DLX: consume from DLX queue, fix issue, republish to original exchange

---
