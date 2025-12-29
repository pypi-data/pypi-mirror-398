# Functional Requirements Inventory

**FR-001**: MCP Protocol Foundation - 3 tools: `search-ids`, `get-id`, `call-id`
**FR-002**: Semantic Search - <100ms latency, ≥0.7 similarity threshold
**FR-003**: Operation Documentation - `get-id` with <50ms latency
**FR-004**: Operation Execution - `call-id` with validation, <200ms completion
**FR-005**: AMQP Protocol Operations - Publish, consume, ack/nack/reject
**FR-006**: Connection Management - Config precedence, TLS support
**FR-007**: Auto-Reconnection - Exponential backoff (1s→60s)
**FR-008**: Queue Operations - List, create, delete, purge with safety validations
**FR-009**: Exchange Operations - Direct/topic/fanout/headers with system protection
**FR-010**: Binding Operations - Wildcard support, duplicate prevention
**FR-011**: Message Publishing - <100ms, configurable properties
**FR-012**: Message Consumption - 100+ concurrent consumers, <50ms per message
**FR-013**: Message Acknowledgment - Ack/nack/reject with delivery tag validation
**FR-014**: Structured Logging - JSON format, correlation IDs, auto-sanitization
**FR-015**: Log Rotation & Retention - Daily/100MB rotation, 30-day retention
**FR-016**: Logging Performance - <5ms overhead, 1000 logs/sec
**FR-017**: Audit Trail - All operations tracked with correlation IDs
**FR-018**: Testing Framework - 80%+ coverage, <5min execution
**FR-019**: Observability - OpenTelemetry, distributed traces, metrics
**FR-020**: Rate Limiting - 100 req/min, <5ms rejection
**FR-021**: Multi-Version Support - RabbitMQ 3.11.x, 3.12.x, 3.13.x
**FR-022**: CLI Interface - `<command> <subcommand> <options>` structure
**FR-023**: Safety Validations - Block destructive ops, structured errors

---
