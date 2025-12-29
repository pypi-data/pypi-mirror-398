# Product Scope

## MVP - Minimum Viable Product (Phase 1 - Specs 001-008)

**Core Capabilities**:

1. **MCP Protocol Foundation** ✅ Complete
   - 3-tool semantic discovery: `search-ids`, `get-id`, `call-id`
   - JSON-RPC 2.0 compliance with MCP specification
   - Stdio transport for AI assistant integration
   - Structured error handling with MCP error codes

2. **RabbitMQ Connectivity** ✅ Complete
   - HTTP Management API client (username/password, TLS)
   - Connection pooling and retry logic
   - Health checks and connection monitoring
   - Multi-vhost support

3. **Topology Operations** ✅ Complete
   - Queue operations: list, create, delete, purge, get details
   - Exchange operations: list, create, delete, get details (direct/topic/fanout/headers)
   - Binding operations: list, create, delete with routing key support
   - Safety validations: prevent data loss, validate parameters

4. **Message Publishing & Consumption** ✅ Complete
   - Publish messages to exchanges with routing keys
   - Consume messages from queues (basic consume, ack/nack)
   - Message properties (persistence, priority, headers)
   - AMQP protocol via pika library

5. **Console Client** ✅ Complete
   - Standalone CLI: `uvx rabbitmq-mcp-server queue list`
   - Command structure: `<resource> <operation> [options]`
   - Rich terminal output (tables, colors)
   - Help system with examples

6. **Testing Framework** ✅ Complete
   - Unit tests for all tools and operations (pytest)
   - Integration tests with real RabbitMQ (Docker testcontainers)
   - Contract tests for MCP protocol compliance
   - 80%+ code coverage (95%+ for critical paths)

7. **Structured Logging** ⏳ In Progress (Spec 007)
   - JSON-structured logs with correlation IDs
   - Automatic sensitive data sanitization
   - File-based output with daily rotation
   - Log levels: ERROR, WARN, INFO, DEBUG
   - Performance: <5ms logging overhead per operation

8. **MVP Documentation** 📋 Planned (Spec 008)
   - README with quick start (uvx examples)
   - API reference with all operations
   - Architecture documentation with diagrams
   - Examples for common use cases
   - Contributing guide for community

## Growth Features (Post-MVP - Phase 2)

**Advanced Features** (Specs 009-020):
- Pre-built vector database with sqlite-vec
- Advanced retry and dead-letter queue patterns
- Configuration import/export
- Advanced monitoring (Prometheus, Grafana)
- Advanced security (OAuth, RBAC, audit logs)
- Multilingual console client
- Comprehensive testing (performance, chaos, security)
- Enterprise logging integrations (ELK, Splunk, CloudWatch)
- Performance optimizations and scalability
- Advanced messaging (delayed messages, priority, TTL)
- Comprehensive documentation (video tutorials, interactive examples)
- CI/CD quality pipeline (GitHub Actions, semantic release)

## Vision (Future)

**Enterprise Integration**:
- LDAP/Active Directory authentication
- SSO integration (SAML, OIDC)
- Custom plugin system for organization-specific operations
- Multi-region/multi-cluster management
- Terraform provider or Kubernetes operator

**Ecosystem Expansion**:
- Multi-language support (TypeScript for Node.js)
- Plugin architecture for extensibility
- Infrastructure-as-code integrations
- Advanced RabbitMQ features (clustering, federation, shovel)

---
