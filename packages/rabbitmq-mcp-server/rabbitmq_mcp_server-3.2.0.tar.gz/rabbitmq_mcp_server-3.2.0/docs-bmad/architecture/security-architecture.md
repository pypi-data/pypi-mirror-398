# Security Architecture

## Authentication & Authorization

**Stdio Transport (Local):**
- Inherits security from parent process (Claude Desktop, terminal)
- No additional authentication layer needed
- Credentials managed via environment variables or config files
- File system permissions protect credentials

**HTTP Transport (Remote):**
- **Optional Bearer Token Authentication**
  - Token via `MCP_AUTH_TOKEN` environment variable
  - Validated on every HTTP request
  - Token format: random 32-character string (minimum)
- **TLS/SSL Support**
  - Required for production deployments
  - Certificate path configurable via `MCP_TLS_CERT` and `MCP_TLS_KEY`
  - Self-signed cert support for development (`--insecure` flag)
- **CORS (Cross-Origin Resource Sharing)**
  - Disabled by default
  - Enable with `--cors-origins` flag
  - Must expose `Mcp-Session-Id` header for browser clients

**RabbitMQ Credentials:**
- **Never hardcoded** - always from configuration
- **Pydantic SecretStr** type prevents accidental logging
- **Environment variables** (recommended):
  - `AMQP_USER`
  - `AMQP_PASSWORD`
- **Config file** (encrypted at rest recommended):
  - `config.toml` with restricted permissions (600)

## Credential Protection

**Automatic Sanitization (100% Coverage):**
```python
# Regex patterns detect and redact:
Patterns = [
    r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',  # password=secret
    r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',     # token=abc123
    r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',  # api_key=xyz
    r'Authorization:\s*Bearer\s+(\S+)',            # Authorization: Bearer token
    r'amqp://[^:]+:([^@]+)@',                      # amqp://user:pass@host
]

Replacement: [REDACTED]
```

**Sanitization Applied To:**
- All structured logs (structlog processors)
- Error messages returned to clients
- Stack traces (before logging)
- Configuration validation errors
- HTTP request/response logging

**Secure Storage:**
- Log files: 600 permissions (owner read/write only)
- Log directory: 700 permissions (owner access only)
- Config files: 600 permissions recommended
- No credentials in Git (`.env` in `.gitignore`)

## Audit Trail

**Complete Operation Logging:**
```python
# Every operation generates audit log entries:
{
  "event": "queue_deleted",
  "timestamp": "2025-11-16T12:00:00Z",
  "correlation_id": "abc-123",
  "user": "admin",  # From RabbitMQ credentials
  "vhost": "/",
  "resource_type": "queue",
  "resource_name": "orders",
  "operation": "DELETE",
  "result": "success",
  "client_id": "claude-desktop"
}
```

**Audit Log Retention:**
- Minimum 30 days (configurable via `LOG_RETENTION_DAYS`)
- Compressed after rotation (gzip)
- Searchable via structured JSON format
- Correlation IDs enable end-to-end tracing

**Compliance Features:**
- Immutable log files (append-only)
- Tamper-evident with checksums (optional)
- Export to SIEM systems (ELK, Splunk, CloudWatch)

## Network Security

**TLS/SSL Configuration:**
```toml
[security]
http_use_tls = true
http_verify_ssl = true
http_ca_bundle = "/path/to/ca-bundle.crt"

amqp_use_tls = true
amqp_verify_ssl = true
amqp_ca_bundle = "/path/to/ca-bundle.crt"
```

**No Plaintext Credentials:**
- TLS enforced for production
- Warning logged if TLS disabled
- Development mode only: `--insecure` flag
