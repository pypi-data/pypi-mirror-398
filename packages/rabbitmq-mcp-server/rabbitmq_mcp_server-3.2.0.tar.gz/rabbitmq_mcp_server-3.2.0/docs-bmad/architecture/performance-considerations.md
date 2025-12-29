# Performance Considerations

## Latency Targets

**MCP Operations:**
- Semantic search (search-ids): <100ms (p95), <150ms (p99)
- Operation lookup (get-id): <50ms (p95)
- Operation execution (call-id): <200ms for HTTP (p95), <50ms for AMQP (p95)

**Infrastructure:**
- Server startup: <1 second
- Health check: <1 second (p95)
- Logging overhead: <5ms per operation

**RabbitMQ Operations:**
- Message publish: <100ms (p95), 1000+ messages/minute
- Message consume: <50ms delivery latency (p95), 100+ concurrent consumers
- Topology operations: <200ms (p95)

## Throughput Targets

**Message Operations:**
- Publishing: 1000+ messages/minute per instance
- Consumption: 1000+ messages/minute per instance
- Concurrent consumers: 100+ simultaneous

**Logging:**
- 1000+ log entries/second (async handlers)
- No blocking on log writes (buffer saturation blocks)

## Optimization Strategies

**Pre-Computation (Build-Time):**
- Embeddings generated once, loaded at startup (<500ms)
- Pydantic schemas compiled at import time
- Operation registry cached in memory (O(1) lookup)

**Connection Pooling:**
```python
HTTP Connection Pool:
  - Size: 5 connections (configurable)
  - Timeout: 10 seconds to acquire connection
  - Keep-alive: 60 seconds idle timeout
  - Reuse: Automatic connection reuse
```

**Caching Strategy:**
```python
Query Embedding Cache:
  - Type: LRU cache
  - Max size: 100 queries
  - TTL: Session lifetime (stdio) or 1 hour (HTTP)
  - Hit rate target: >80%

Operation Registry:
  - Type: In-memory dict
  - Loaded once at startup
  - Immutable (no cache invalidation needed)
```

**Async I/O:**
- All network operations use asyncio
- Non-blocking HTTP client (httpx)
- Concurrent operation execution where possible
- No thread pool overhead

**Resource Limits:**
```toml
[performance]
max_request_body_size = 10_485_760  # 10MB
max_message_size = 1_048_576  # 1MB
request_timeout = 30  # seconds
connection_timeout = 5  # seconds
```

## Scalability

**Horizontal Scaling (HTTP Transport):**
- Stateless design enables multiple instances
- Load balancer distributes requests
- Session affinity not required
- Shared-nothing architecture

**Vertical Scaling:**
- Memory: ~500MB per instance under normal load
- CPU: I/O bound, scales with core count
- Disk: Logs only, predictable growth

**Rate Limiting:**
```python
**Rate Limiting:**
```python
# Per-client rate limits
default_limit = 100  # requests per minute
client_identification = [
    "MCP_connection_id",  # Primary
    "IP_address",         # Fallback
    "global"              # Last resort
]

# Rejection response
HTTP 429 Too Many Requests
Retry-After: 60  # seconds
```

## Production Monitoring Strategy

**Key Performance Metrics to Monitor:**

**Response Time Metrics:**
- `search_ids_latency_p95`: Alert if >100ms
- `search_ids_latency_p99`: Alert if >150ms
- `get_id_latency_p95`: Alert if >50ms
- `call_id_http_latency_p95`: Alert if >200ms
- `call_id_amqp_latency_p95`: Alert if >50ms

**Throughput Metrics:**
- `messages_published_per_min`: Alert if <1000
- `messages_consumed_per_min`: Monitor trend
- `operations_per_second`: Monitor capacity
- `concurrent_consumers`: Alert if >90 (approaching 100 limit)

**Resource Metrics:**
- `memory_usage_mb`: Alert if >1800MB (approaching 2GB limit)
- `cpu_usage_percent`: Alert if >80% sustained
- `log_disk_usage_gb`: Alert if >8GB (approaching 10GB retention)

**Reliability Metrics:**
- `rabbitmq_connection_failures`: Alert on any failure
- `auto_reconnection_attempts`: Alert if >5 consecutive
- `health_check_failures`: Alert if 3+ consecutive
- `operation_error_rate`: Alert if >5%

**Security Metrics:**
- `credential_sanitization_failures`: Alert immediately (P0)
- `authentication_failures`: Alert on spike (>10/min)
- `rate_limit_rejections`: Monitor for DoS patterns

**SLO Violation Thresholds:**
```python
# Alert severity levels
CRITICAL = {
    "search_latency_p95": ">200ms",  # 2x target
    "operation_error_rate": ">10%",
    "memory_usage": ">90%",
    "rabbitmq_disconnected": ">5min"
}

WARNING = {
    "search_latency_p95": ">120ms",  # 1.2x target
    "operation_error_rate": ">5%",
    "memory_usage": ">75%",
    "reconnection_attempts": ">3"
}
```

**Performance Degradation Detection:**
- Baseline: Collect 7 days of metrics after deployment
- Trend Analysis: Alert if p95 latency increases >20% over 24h
- Capacity Planning: Alert if throughput approaches 80% of target
- Anomaly Detection: Alert on sudden spikes (>3 standard deviations)

**Monitoring Implementation:**
- **Phase 1 (MVP):** Structured logs + basic metrics via OpenTelemetry (Story 7.8)
- **Phase 2:** Prometheus metrics exporter (Epic 12) + Grafana dashboards
- **Phase 3:** Advanced alerting with PagerDuty/Slack integration

**Dashboard Panels (Grafana Recommended):**
1. **Overview:** Request rate, error rate, latency (p50/p95/p99)
2. **MCP Operations:** search-ids, get-id, call-id latencies
3. **RabbitMQ Health:** Connection status, message throughput, consumer count
4. **Resource Usage:** CPU, memory, disk, network I/O
5. **Errors & Alerts:** Error rate trend, active alerts, recent incidents

````
```
