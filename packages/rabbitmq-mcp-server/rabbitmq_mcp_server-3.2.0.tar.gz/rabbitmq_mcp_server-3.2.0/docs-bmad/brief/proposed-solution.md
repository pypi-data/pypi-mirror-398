# Proposed Solution

## The RabbitMQ MCP Server Approach

**3-Tool Semantic Discovery Pattern**:
- **`search-ids`**: Natural language → relevant operations ("list slow queues" → `list_queue_operations`)
- **`get-id`**: Operation ID → full schema and documentation
- **`call-id`**: Operation ID + parameters → execute operation

**Result**: Unlimited RabbitMQ operations through just 3 MCP tools. No tool explosion. Natural language discovery.

## OpenAPI-Driven Architecture

**Build-Time Code Generation**:
1. **Source of Truth**: `./rabbitmq-http-api-openapi.yaml` (4800+ lines, 100+ operations)
2. **Generation Phase** (triggers on OpenAPI changes):
   - Pydantic models from `components.schemas`
   - Operation registry from `paths`
   - Vector embeddings for semantic search
3. **Artifacts Committed**: All generated code version-controlled
4. **Runtime**: Zero generation overhead, instant startup

**Advantages**:
- **Consistency**: Single source of truth for operations, schemas, and documentation
- **Maintainability**: API changes propagate automatically through generation
- **Performance**: Pre-computed embeddings enable <100ms semantic search
- **Reliability**: Generated code is tested and validated at build-time

## Developer Experience

**Natural Conversation Flow**:
```
Developer: "Show me queues with more than 1000 messages"
AI (via RabbitMQ MCP): 
  1. search-ids("queues with high message count") → finds "list_queues"
  2. get-id("list_queues") → understands parameters and filters
  3. call-id("list_queues", filters={"messages": {">": 1000}}) → returns results

Developer: "Purge the failed-orders queue"
AI: Executes purge operation with safety validation (checks for messages)
```

**Safety First**:
- Automatic validation (e.g., prevents deleting queues with messages without confirmation)
- Dry-run support for destructive operations
- Audit logging for compliance

## Key Differentiators

1. **Only RabbitMQ-Specific MCP Server**: Purpose-built for RabbitMQ with domain knowledge (vs generic HTTP proxies)

2. **Build-Time Generation Pattern**: Demonstrates scalable approach for API-based MCP servers (others generate at runtime)

3. **Semantic Discovery Without Tool Explosion**: 3 tools cover 100+ operations (vs 100+ individual MCP tools)

4. **Production-Ready from MVP**: 80% test coverage, structured logging, security, observability built-in

5. **Enterprise Compliance**: LGPL licensing, audit trails, sensitive data sanitization, configurable retention

6. **Python Ecosystem Leadership**: Reference implementation for Python MCP servers using modern tooling (uv, pydantic, structlog)

7. **Follows Bitbucket/Jira Pattern**: Proven architecture used successfully in bitbucket-dc-mcp and jira-dc-mcp projects

---
