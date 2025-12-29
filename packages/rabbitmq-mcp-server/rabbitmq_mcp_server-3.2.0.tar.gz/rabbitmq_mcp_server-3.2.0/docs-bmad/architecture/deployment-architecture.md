# Deployment Architecture

## Deployment Modes

**Mode 1: Local Development (Stdio)**
```bash
# Direct execution for local testing
uv run python -m rabbitmq_mcp_server

# Claude Desktop integration
# Configured in claude_desktop_config.json
# Runs as subprocess of Claude Desktop
```

**Mode 2: Remote Server (HTTP)**
```bash
# Standalone HTTP server
uv run python -m rabbitmq_mcp_server \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --cors-origins "https://app.example.com"

# With TLS
uv run python -m rabbitmq_mcp_server \
  --transport http \
  --host 0.0.0.0 \
  --port 8443 \
  --tls-cert /path/to/cert.pem \
  --tls-key /path/to/key.pem
```

**Mode 3: Docker Container**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "rabbitmq_mcp_server", \
     "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
```

**Mode 4: ASGI Server (Production)**
```python
# Mount on existing Starlette/FastAPI app
from starlette.applications import Starlette
from starlette.routing import Mount
from rabbitmq_mcp_server.mcp_server import mcp

app = Starlette(
    routes=[
        Mount("/mcp", app=mcp.streamable_http_app()),
    ]
)

# Run with uvicorn
# uvicorn myapp:app --host 0.0.0.0 --port 8000 --workers 4
```

## Infrastructure Requirements

**Minimum Requirements:**
- Python 3.12+
- 512MB RAM
- 1 CPU core
- 100MB disk space (excluding logs)

**Recommended Production:**
- Python 3.12+
- 2GB RAM
- 2-4 CPU cores
- 10GB disk space (with log rotation)

**Network Requirements:**
- RabbitMQ Management API: Port 15672 (HTTP/HTTPS)
- RabbitMQ AMQP: Port 5672 (or 5671 for TLS)
- MCP HTTP Server: Port 8000 (or custom)

## Environment Variables

**Required:**
```bash
AMQP_HOST=rabbitmq.example.com
AMQP_PORT=5672
AMQP_USER=admin
AMQP_PASSWORD=secure_password
```

**Optional:**
```bash
# RabbitMQ Configuration
AMQP_VHOST=/
AMQP_USE_TLS=false
HTTP_PORT=15672
HTTP_USE_TLS=false

# MCP Server Configuration
MCP_TRANSPORT=stdio  # or http
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
MCP_AUTH_TOKEN=secure_token_here

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_RETENTION_DAYS=30

# Performance
CONNECTION_POOL_SIZE=5
REQUEST_TIMEOUT=30
RATE_LIMIT_RPM=100

# OpenTelemetry (optional)
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=rabbitmq-mcp-server
```

## High Availability (Phase 2)

**Multi-Instance Deployment:**
```
                    [Load Balancer]
                           |
        +------------------+------------------+
        |                  |                  |
   [Instance 1]       [Instance 2]       [Instance 3]
        |                  |                  |
        +------------------+------------------+
                           |
                   [RabbitMQ Cluster]
```

**Session Management:**
- Stateless mode: No session storage needed
- Stateful mode: Redis for distributed sessions (Phase 2)

## Load Balancing Strategy

**Recommended Load Balancers:**

**Option 1: nginx (Recommended for HTTP transport)**
```nginx
upstream rabbitmq_mcp {
    least_conn;  # Route to instance with fewest active connections
    server instance1.example.com:8000 max_fails=3 fail_timeout=30s;
    server instance2.example.com:8000 max_fails=3 fail_timeout=30s;
    server instance3.example.com:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name mcp.example.com;

    ssl_certificate /etc/ssl/certs/mcp.crt;
    ssl_certificate_key /etc/ssl/private/mcp.key;

    location /mcp {
        proxy_pass http://rabbitmq_mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffering (disable for SSE)
        proxy_buffering off;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://rabbitmq_mcp/mcp/health;
        access_log off;
    }
}
```

**Option 2: HAProxy (Advanced features)**
```haml
frontend mcp_frontend
    bind *:8000 ssl crt /etc/ssl/mcp.pem
    mode http
    option forwardfor
    http-request add-header X-Forwarded-Proto https
    default_backend mcp_backend

backend mcp_backend
    mode http
    balance leastconn
    option httpchk GET /mcp/health
    http-check expect status 200
    
    server instance1 10.0.1.10:8000 check inter 5s fall 3 rise 2
    server instance2 10.0.1.11:8000 check inter 5s fall 3 rise 2
    server instance3 10.0.1.12:8000 check inter 5s fall 3 rise 2
```

**Option 3: Cloud Load Balancers**
- **AWS ALB:** Application Load Balancer with target groups
- **GCP Load Balancer:** HTTP(S) Load Balancing
- **Azure Load Balancer:** Application Gateway

**Load Balancing Algorithm Recommendations:**
- **Least Connections:** Best for HTTP transport (requests vary in duration)
- **Round Robin:** Acceptable if request durations are uniform
- **IP Hash:** Avoid (breaks stateless design, no session affinity needed)
- **Weighted:** Use if instances have different capacities

**Health Check Configuration:**

**Endpoint:** `GET /mcp/health` (to be implemented in Story 2.4)

**Expected Response:**
```json
{
  "status": "healthy",
  "amqp_connected": true,
  "http_connected": true,
  "timestamp": "2025-11-16T12:00:00Z"
}
```

**Health Check Parameters:**
- **Interval:** 5 seconds (frequent enough to detect failures quickly)
- **Timeout:** 2 seconds (must respond quickly)
- **Unhealthy Threshold:** 3 consecutive failures (avoid false positives)
- **Healthy Threshold:** 2 consecutive successes (return to rotation quickly)
- **HTTP Status:** 200 = healthy, 503 = unhealthy

**Session Affinity Requirements:**
- **HTTP Transport:** Session affinity **NOT required** (stateless design per ADR-005)
- **Stdio Transport:** Not applicable (direct process execution)
- **Client Identification:** Use X-Forwarded-For header for rate limiting per-client

**Scaling Triggers (Auto-Scaling):**
```yaml
# Kubernetes HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rabbitmq-mcp-server
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rabbitmq-mcp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
```

**Load Testing Before Production:**
- Use k6 to simulate expected load (see test-design-system.md)
- Test with 2x expected peak load to ensure headroom
- Verify load balancer distributes traffic evenly
- Validate health checks remove unhealthy instances
- Confirm no request failures during instance restart (rolling deployment)

````
