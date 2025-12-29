# MVP Scope (Phase 1)

## Core Features (Specs 001-008)

**1. MCP Protocol Foundation (Spec 001)** ✅
- Three-tool semantic discovery pattern: `search-ids`, `get-id`, `call-id`
- JSON-RPC 2.0 compliance with MCP specification
- Stdio transport for AI assistant integration
- Error handling with MCP error codes

**2. RabbitMQ Connectivity (Spec 002)** ✅
- HTTP Management API client with authentication (username/password, TLS)
- Connection pooling and retry logic
- Health checks and connection monitoring
- Multi-vhost support

**3. Topology Operations (Spec 003)** ✅
- **Queue Operations**: List, create, delete, purge, get details
- **Exchange Operations**: List, create, delete, get details (direct, topic, fanout, headers)
- **Binding Operations**: List, create, delete with routing key support
- **Safety Validations**: Prevents deleting queues with messages, validates routing keys

**4. Message Publishing & Consumption (Spec 004)** ✅
- Publish messages to exchanges with routing keys
- Consume messages from queues (basic consume, ack/nack)
- Message property support (persistence, priority, headers)
- AMQP protocol via pika library

**5. Console Client (Spec 005)** ✅
- Standalone CLI: `uvx rabbitmq-mcp-server queue list`
- Command structure: `<resource> <operation> [options]`
- Rich terminal output with tables and colors
- Help system with examples

**6. Testing Framework (Spec 006)** ✅
- Unit tests for all tools and operations (pytest)
- Integration tests with real RabbitMQ (Docker testcontainers)
- Contract tests for MCP protocol compliance
- 80%+ code coverage minimum (95%+ for critical paths)

**7. Structured Logging (Spec 007)** ⏳ In Progress
- JSON-structured logs with correlation IDs
- Automatic sensitive data sanitization (passwords, tokens)
- File-based output with daily rotation
- Log levels: ERROR, WARN, INFO, DEBUG
- Performance: <5ms logging overhead per operation

**8. MVP Documentation (Spec 008)** Planned
- README with quick start (uvx examples)
- API reference with all operations
- Architecture documentation with diagrams
- Examples for common use cases
- Contributing guide for community

## Out of Scope for MVP (Phase 2)

**Advanced Features** (Specs 009-020):
- Pre-built vector database with sqlite-vec (Spec 009)
- Advanced retry and dead-letter queue patterns (Spec 010)
- Configuration import/export (Spec 011)
- Advanced monitoring and metrics (Prometheus, Grafana) (Spec 012)
- Advanced security (OAuth, RBAC, audit logs) (Spec 013)
- Multilingual console client (Spec 014)
- Comprehensive testing (performance, chaos, security) (Spec 015)
- Enterprise logging (ELK, Splunk, CloudWatch) (Spec 016)
- Performance optimizations and scalability (Spec 017)
- Advanced messaging (delayed messages, message priority, TTL) (Spec 018)
- Comprehensive documentation (video tutorials, interactive examples) (Spec 019)
- CI/CD quality pipeline (GitHub Actions, semantic release) (Spec 020)

**Enterprise Integration** (Future):
- LDAP/Active Directory authentication
- SSO integration (SAML, OIDC)
- Custom plugin system for organization-specific operations
- Multi-region/multi-cluster management
- Terraform provider or Kubernetes operator

## MVP Success Criteria

The MVP is considered complete when:

1. **All 8 specs implemented** with acceptance criteria met
2. **80%+ test coverage** across all critical components
3. **Zero linting warnings** (ruff, mypy, bandit)
4. **Documentation complete** (README, API reference, architecture, examples)
5. **Security validated** (no credential leaks, secure defaults, audit trails)
6. **Performance requirements met** (<100ms search, <200ms operations)
7. **MCP protocol compliance** verified with multiple AI assistants
8. **Community ready** (open source license, contribution guide, issue templates)

---
