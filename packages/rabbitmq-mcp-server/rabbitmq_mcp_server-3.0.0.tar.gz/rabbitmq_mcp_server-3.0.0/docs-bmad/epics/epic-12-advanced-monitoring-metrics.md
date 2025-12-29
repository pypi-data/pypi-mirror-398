# Epic 12: Advanced Monitoring & Metrics

**Goal**: Enhance observability with Prometheus metrics export, Grafana dashboard templates, and advanced alerting for production monitoring.

**Value**: Provides production-grade monitoring capabilities that enable proactive incident detection, capacity planning, and SLA compliance tracking.

**Priority**: High (Production requirement)

---

## Story 12.1: Prometheus Metrics Exporter

As a platform engineer,
I want Prometheus-compatible metrics endpoint,
So that I can scrape metrics and integrate with existing monitoring infrastructure.

**Acceptance Criteria:**

**Given** MCP server with metrics endpoint enabled
**When** Prometheus scrapes metrics endpoint
**Then** metrics are exposed at: http://localhost:9090/metrics (configurable via METRICS_PORT)

**And** metrics include operation counters: rabbitmq_mcp_operations_total{operation="queues.list", status="success"}

**And** metrics include latency histograms: rabbitmq_mcp_operation_duration_seconds{operation="queues.list", quantile="0.95"}

**And** metrics include connection metrics: rabbitmq_mcp_connections_active, rabbitmq_mcp_connection_errors_total

**And** metrics include cache metrics: rabbitmq_mcp_cache_hits_total, rabbitmq_mcp_cache_misses_total

**And** metrics format follows Prometheus conventions: snake_case naming, _total suffix for counters, _seconds suffix for durations

**And** metrics endpoint returns: Content-Type: text/plain; version=0.0.4

**And** metrics include labels: operation, vhost, status (success/error), error_type

**Prerequisites:** Epic 7 complete (observability)

**Technical Notes:**
- Use prometheus_client library: from prometheus_client import Counter, Histogram, Gauge, generate_latest
- Define metrics: operations_counter = Counter('rabbitmq_mcp_operations_total', 'Total operations', ['operation', 'status'])
- Instrument code: operations_counter.labels(operation='queues.list', status='success').inc()
- HTTP endpoint: serve metrics via simple HTTP server or integrate with existing server
- Buckets for histogram: [.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0]
- Prometheus config: add scrape target to prometheus.yml

---

## Story 12.2: Grafana Dashboard Templates

As a DevOps engineer,
I want pre-built Grafana dashboards for visualizing RabbitMQ MCP metrics,
So that I can quickly set up monitoring without building dashboards from scratch.

**Acceptance Criteria:**

**Given** Grafana with Prometheus data source configured
**When** I import dashboard template
**Then** dashboard displays: operation latency (p50/p95/p99), operation throughput (ops/sec), error rate (%), connection health, cache performance

**And** dashboard templates provided: ./dashboards/rabbitmq-mcp-overview.json, ./dashboards/rabbitmq-mcp-operations.json

**And** dashboards are importable: Grafana UI → Import → paste JSON

**And** dashboards support variables: $vhost, $operation for filtering

**And** dashboards include: time-series graphs, stat panels, gauge panels, table panels

**And** alerts configured: high error rate (>5%), high latency (p95 >500ms), connection failures

**And** dashboards documented: ./docs/MONITORING.md with setup instructions, screenshots, alert configuration

**Prerequisites:** Story 12.1 (Prometheus metrics)

**Technical Notes:**
- Create dashboards in Grafana UI, export as JSON
- Dashboard structure: rows for Operations, Connections, Performance, Errors
- Queries: rate(rabbitmq_mcp_operations_total[5m]), histogram_quantile(0.95, rabbitmq_mcp_operation_duration_seconds)
- Variables: vhost (query: label_values(rabbitmq_mcp_operations_total, vhost))
- Alerts: use Grafana alerting or Prometheus alertmanager
- Templates stored in ./dashboards/ directory
- Document: prerequisites (Grafana, Prometheus), import steps, customization options

---
