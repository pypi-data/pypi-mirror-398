# Executive Summary

The RabbitMQ MCP Server architecture implements a production-ready AI-assisted infrastructure management tool using a dual-transport MCP protocol design. The system exposes 100+ RabbitMQ Management API operations through just 3 semantic MCP tools, solving the tool explosion problem while maintaining enterprise-grade security, performance, and observability.

**Core Architectural Approach:**
- **OpenAPI-Driven Code Generation**: Single source of truth drives all schemas, operations, and embeddings at build-time
- **Semantic Discovery Pattern**: 3-tool interface (search-ids, get-id, call-id) with <100ms natural language search
- **Dual Transport**: Stdio for AI assistants + Streamable HTTP for remote/browser clients
- **Zero Runtime Overhead**: Pre-computed embeddings and schemas enable <1s server startup
- **Production Security**: Automatic credential sanitization, structured audit logging, secure defaults

**Key Performance Targets:**
- Semantic search: <100ms (p95)
- Operation execution: <200ms for HTTP, <50ms for AMQP (p95)
- Server startup: <1 second
- Logging overhead: <5ms per operation
