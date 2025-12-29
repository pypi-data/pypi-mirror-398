# Architecture Documentation

Comprehensive architecture guide for RabbitMQ MCP Server.

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [System Architecture](#system-architecture)
- [Component Diagram](#component-diagram)
- [MCP Pattern: Three Tools](#mcp-pattern-three-tools)
- [OpenAPI-Driven Architecture](#openapi-driven-architecture)
- [Vector Database for Semantic Search](#vector-database-for-semantic-search)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Performance Architecture](#performance-architecture)
- [Security Architecture](#security-architecture)
- [Testing Architecture](#testing-architecture)
- [Design Decisions](#design-decisions)

---

## Overview

The RabbitMQ MCP Server is a **Model Context Protocol (MCP) server with built-in CLI** that exposes RabbitMQ Management API operations through a semantic discovery pattern. It follows an **OpenAPI-driven architecture** where all operations are defined in OpenAPI specifications, automatically generating schemas, validations, and operation registries.

### Key Characteristics

- **Protocol**: MCP (Model Context Protocol) for LLM integration
- **Interface**: Both MCP tools and CLI commands
- **Discovery**: Semantic search using vector embeddings
- **Validation**: OpenAPI-based request/response validation
- **Safety**: Built-in validations prevent data loss
- **Performance**: Optimized for operations with 1000+ resources

---

## Design Principles

### 1. Constitution-First Development

All architectural decisions follow the project's `constitution.md`:

- **Tool limit**: Maximum 15 MCP tools per server (we use 3)
- **Performance**: < 200ms for basic operations, < 2s for complex operations
- **Testing**: Minimum 80% code coverage
- **Documentation**: All docs in English
- **Licensing**: LGPL v3.0 with headers in all source files

### 2. OpenAPI as Single Source of Truth

Every operation is defined in OpenAPI YAML specifications:

```
specs/003-essential-topology-operations/contracts/
├── queue-operations.yaml       # Queue operations
├── exchange-operations.yaml    # Exchange operations
└── binding-operations.yaml     # Binding operations
```

From these specs, we automatically generate:
- Pydantic schemas for validation
- Operation registry mappings
- Vector embeddings for semantic search
- API documentation

### 3. Semantic Discovery Pattern

Instead of exposing 50+ individual MCP tools (queues.list, queues.create, exchanges.list, etc.), we expose only **3 public tools**:

1. **search-ids**: Find operations semantically
2. **get-id**: Get operation schema
3. **call-id**: Execute operation

This pattern:
- Stays under the 15-tool limit
- Enables natural language discovery
- Supports unlimited operations
- Reduces cognitive load

### 4. Safety by Design

Operations include built-in safety validations:

- **Queue deletion**: Blocked if queue has messages (unless `--force`)
- **Exchange deletion**: Blocked if exchange has active bindings
- **System protection**: Cannot delete system exchanges (`amq.*`)
- **Virtual host validation**: All operations validate vhost exists first
- **Duplicate detection**: Prevents accidental resource duplication

### 5. Performance-First

Architecture optimized for scale:

- **Mandatory pagination**: All list operations use client-side pagination
- **Connection pooling**: HTTP keep-alive with persistent connections
- **Caching**: 60-second cache for vhost validation results
- **Memory efficiency**: < 1GB memory footprint per instance
- **Timeout strategy**: Separate timeouts for CRUD (5s) vs list (30s) operations

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RabbitMQ MCP Server                      │
│                                                               │
│  ┌────────────────┐           ┌─────────────────────────┐  │
│  │   MCP Tools    │           │      CLI Interface       │  │
│  │  (3 public)    │           │    (Built-in commands)   │  │
│  ├────────────────┤           ├─────────────────────────┤  │
│  │ • search-ids   │           │ • queue {list,create,..} │  │
│  │ • get-id       │           │ • exchange {list,...}    │  │
│  │ • call-id      │           │ • binding {list,...}     │  │
│  └───────┬────────┘           └──────────┬──────────────┘  │
│          │                               │                  │
│          └───────────┬───────────────────┘                  │
│                      │                                       │
│          ┌───────────▼──────────────┐                       │
│          │   Operation Router       │                       │
│          │  (OpenAPI-driven)        │                       │
│          └───────────┬──────────────┘                       │
│                      │                                       │
│          ┌───────────▼──────────────┐                       │
│          │   Operation Executors    │                       │
│          ├──────────────────────────┤                       │
│          │ • Queue Operations       │                       │
│          │ • Exchange Operations    │                       │
│          │ • Binding Operations     │                       │
│          └───────────┬──────────────┘                       │
│                      │                                       │
│          ┌───────────▼──────────────┐                       │
│          │   HTTP Client Executor   │                       │
│          │  (Connection Pool)       │                       │
│          └───────────┬──────────────┘                       │
└────────────────────────┼──────────────────────────────────┘
                         │
                         │ HTTP (Management API)
                         │
                  ┌──────▼──────┐
                  │  RabbitMQ   │
                  │   Server    │
                  └─────────────┘
```

### Component Layers

#### 1. Interface Layer
- **MCP Tools**: Three public tools for LLM integration
- **CLI Commands**: Human-friendly command-line interface

#### 2. Routing Layer
- **Operation Router**: Maps operation IDs to executors
- **OpenAPI Registry**: Indexed operation metadata

#### 3. Execution Layer
- **Operation Executors**: Business logic for each operation type
- **Validation**: Input/output validation using Pydantic
- **Error Handling**: Standardized error formatting

#### 4. Communication Layer
- **HTTP Client**: Requests-based client with connection pooling
- **Authentication**: HTTP Basic Auth
- **Timeout Management**: Separate timeouts for operation types

#### 5. Cross-Cutting Concerns
- **Logging**: Structured logging with structlog
- **Vector DB**: Semantic search with ChromaDB
- **Configuration**: Environment and file-based settings

---

## Component Diagram

### Core Components

```
┌──────────────────────────────────────────────────────────────┐
│                    Vector Database Layer                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  ChromaDB (Local File-Based)                           │  │
│  │  • Pre-computed embeddings from OpenAPI                │  │
│  │  • all-MiniLM-L6-v2 model for embeddings               │  │
│  │  • < 100ms search performance                          │  │
│  │  • Database size < 50MB (committed to repo)            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    OpenAPI Processing Layer                   │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────┐  │
│  │  Parser        │  │  Schema Generator│  │  Registry   │  │
│  │  • Load YAML   │  │  • Pydantic      │  │  • Index    │  │
│  │  • Validate    │  │  • Validation    │  │  • Lookup   │  │
│  └────────────────┘  └──────────────────┘  └─────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      Operation Layer                          │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────┐  │
│  │  Queues        │  │  Exchanges       │  │  Bindings   │  │
│  │  • list        │  │  • list          │  │  • list     │  │
│  │  • create      │  │  • create        │  │  • create   │  │
│  │  • delete      │  │  • delete        │  │  • delete   │  │
│  └────────────────┘  └──────────────────┘  └─────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   Validation & Safety Layer                   │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────┐  │
│  │  Input Valid.  │  │  VHost Check     │  │  Safety     │  │
│  │  • Name regex  │  │  • Existence     │  │  • Messages │  │
│  │  • Type enum   │  │  • Cache (60s)   │  │  • Bindings │  │
│  └────────────────┘  └──────────────────┘  └─────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     Logging & Audit Layer                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Structured Logging (structlog)                        │  │
│  │  • JSON output with correlation IDs                    │  │
│  │  • Automatic credential sanitization                   │  │
│  │  • Audit logs for create/delete operations             │  │
│  │  • Multiple output destinations (file, ES, Splunk)     │  │
│  │  • File rotation: daily + size-based (100MB)           │  │
│  │  • Retention: 30d (info), 90d (warn/error), 365d (audit)│ │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## MCP Pattern: Three Tools

### Why Three Tools?

The **three-tool pattern** is a deliberate architectural choice:

1. **Scalability**: Support unlimited operations without increasing tool count
2. **Discoverability**: Natural language search finds operations
3. **Flexibility**: Add new operations without changing MCP interface
4. **Compliance**: Stay well under 15-tool limit (constitution requirement)

### Tool Responsibilities

#### 1. search-ids (Semantic Search)

**Purpose**: Find operations using natural language queries

**Input**:
```json
{
  "query": "how do I list all queues",
  "limit": 10
}
```

**Output**:
```json
{
  "results": [
    {
      "operation_id": "queues.list",
      "summary": "List all queues with statistics",
      "tags": ["queues"],
      "score": 0.95
    }
  ]
}
```

**Implementation**:
- Uses ChromaDB for vector similarity search
- Embeddings generated from OpenAPI summaries and descriptions
- < 100ms performance requirement

---

#### 2. get-id (Schema Retrieval)

**Purpose**: Get detailed schema for a specific operation

**Input**:
```json
{
  "operation_id": "queues.create"
}
```

**Output**:
```json
{
  "operation_id": "queues.create",
  "summary": "Create a new queue",
  "parameters": {
    "connection": { "type": "object", "required": true },
    "vhost": { "type": "string", "required": true },
    "name": { "type": "string", "required": true },
    "options": { "type": "object", "required": false }
  },
  "response": {
    "type": "object",
    "properties": { ... }
  }
}
```

**Implementation**:
- Reads from operation registry (built from OpenAPI)
- Returns full schema with validation rules
- Includes examples and documentation

---

#### 3. call-id (Operation Execution)

**Purpose**: Execute an operation with validation

**Input**:
```json
{
  "operation_id": "queues.create",
  "parameters": {
    "connection": {
      "host": "localhost",
      "port": 15672,
      "user": "guest",
      "password": "guest"
    },
    "vhost": "/",
    "name": "my-queue",
    "options": {
      "durable": true
    }
  }
}
```

**Output**:
```json
{
  "success": true,
  "result": {
    "name": "my-queue",
    "vhost": "/",
    "durable": true
  }
}
```

**Implementation**:
- Routes to appropriate operation executor
- Validates input against OpenAPI schema
- Executes operation via HTTP client
- Returns standardized response

---

## OpenAPI-Driven Architecture

### Source of Truth

All operations are defined in OpenAPI 3.1.0 specifications:

```yaml
# Example: specs/003-essential-topology-operations/contracts/queue-operations.yaml
openapi: 3.1.0
info:
  title: RabbitMQ Queue Operations
  version: 1.0.0

paths:
  /queues:
    get:
      operationId: queues.list
      summary: List all queues
      parameters:
        - name: vhost
          in: query
          schema:
            type: string
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
      responses:
        '200':
          description: Paginated list of queues
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedQueueResponse'
```

### Code Generation Pipeline

```
┌─────────────────┐
│  OpenAPI YAML   │
│  (contracts/)   │
└────────┬────────┘
         │
         │ 1. Parse
         ▼
┌─────────────────┐
│  Python Script  │
│  generate_      │
│  schemas.py     │
└────────┬────────┘
         │
         │ 2. Generate
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Pydantic Models │     │ Operation       │     │ Vector          │
│ (src/schemas/)  │     │ Registry        │     │ Embeddings      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                                 │ 3. Use at runtime
                                 ▼
                       ┌─────────────────┐
                       │  MCP Server     │
                       │  (Runtime)      │
                       └─────────────────┘
```

### Benefits of OpenAPI-Driven Approach

1. **Single Source of Truth**: One place to define operations
2. **Automatic Validation**: Pydantic models enforce schemas
3. **Documentation**: API docs generated from specs
4. **Contract Testing**: Validate requests/responses match spec
5. **Version Control**: Schema changes tracked in git

---

## Vector Database for Semantic Search

### Why Vector Database?

Traditional keyword search fails for natural language queries:

- ❌ "show me queues" doesn't match "list queues"
- ❌ "create new exchange" doesn't match "exchanges.create"
- ✅ Vector embeddings understand semantic similarity

### ChromaDB Architecture

```
┌────────────────────────────────────────────────────────┐
│                   ChromaDB Instance                     │
│                  (Local File-Based)                     │
│                                                          │
│  Collection: "rabbitmq_operations"                      │
│  ┌────────────────────────────────────────────────┐   │
│  │ Document 1                                      │   │
│  │ • ID: "queues.list"                            │   │
│  │ • Text: "List all queues with statistics..."   │   │
│  │ • Embedding: [0.23, -0.15, 0.87, ...]         │   │
│  │ • Metadata: {tags: ["queues"], ...}           │   │
│  └────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────┐   │
│  │ Document 2                                      │   │
│  │ • ID: "queues.create"                          │   │
│  │ • Text: "Create a new queue with options..."   │   │
│  │ • Embedding: [0.19, -0.22, 0.91, ...]         │   │
│  │ • Metadata: {tags: ["queues"], ...}           │   │
│  └────────────────────────────────────────────────┘   │
│                        ...                              │
└────────────────────────────────────────────────────────┘
```

### Embedding Generation

**Model**: `all-MiniLM-L6-v2` (sentence-transformers)

**Why this model?**
- Fast inference (< 10ms per text)
- Good semantic understanding
- Small size (90MB)
- Runs locally without external API

**Embedding Process**:
```python
# 1. Extract text from OpenAPI
text = f"{operation.summary} {operation.description}"

# 2. Generate embedding
embedding = model.encode(text)

# 3. Store in ChromaDB
collection.add(
    documents=[text],
    embeddings=[embedding],
    metadatas=[{"operation_id": "queues.list", "tags": ["queues"]}],
    ids=["queues.list"]
)
```

### Search Algorithm

```python
# 1. User query
query = "how do I list queues with messages"

# 2. Generate query embedding
query_embedding = model.encode(query)

# 3. Vector similarity search
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10
)

# 4. Return ranked results
# Results sorted by cosine similarity
```

### Performance Characteristics

- **Search time**: < 100ms for typical queries
- **Index size**: < 50MB (committed to repository)
- **Accuracy**: > 90% for relevant operations
- **Cold start**: No initialization needed (pre-built index)

---

## Data Flow

### Operation Execution Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │
     │ 1. CLI command or MCP call
     │    "queue create --name my-queue"
     ▼
┌─────────────────┐
│  CLI Parser     │
│  (Click)        │
└────┬────────────┘
     │
     │ 2. Parse arguments
     ▼
┌─────────────────┐
│  Input          │
│  Validation     │
│  • Name regex   │
│  • Type check   │
└────┬────────────┘
     │
     │ 3. Validate inputs
     ▼
┌─────────────────┐
│  VHost          │
│  Validation     │
│  (Cached 60s)   │
└────┬────────────┘
     │
     │ 4. Check vhost exists
     ▼
┌─────────────────┐
│  Operation      │
│  Executor       │
│  (Queues)       │
└────┬────────────┘
     │
     │ 5. Build HTTP request
     ▼
┌─────────────────┐
│  HTTP Client    │
│  Executor       │
│  (Connection    │
│   Pool)         │
└────┬────────────┘
     │
     │ 6. PUT /api/queues/{vhost}/{name}
     ▼
┌─────────────────┐
│   RabbitMQ      │
│   Management    │
│   API           │
└────┬────────────┘
     │
     │ 7. Response
     ▼
┌─────────────────┐
│  Response       │
│  Validation     │
│  (Pydantic)     │
└────┬────────────┘
     │
     │ 8. Validate response schema
     ▼
┌─────────────────┐
│  Audit          │
│  Logging        │
│  (structlog)    │
└────┬────────────┘
     │
     │ 9. Log operation
     ▼
┌─────────────────┐
│  Output         │
│  Formatter      │
│  (Table/JSON)   │
└────┬────────────┘
     │
     │ 10. Display result
     ▼
┌──────────┐
│   User   │
└──────────┘
```

### Error Flow

```
┌─────────────────┐
│  Validation     │
│  Failure        │
└────┬────────────┘
     │
     │ ValidationError raised
     ▼
┌─────────────────┐
│  Error          │
│  Formatter      │
│  • code         │
│  • field        │
│  • expected     │
│  • actual       │
│  • action       │
└────┬────────────┘
     │
     │ Standardized error
     ▼
┌─────────────────┐
│  Structured     │
│  Logging        │
│  (ERROR level)  │
└────┬────────────┘
     │
     │ Log error context
     ▼
┌─────────────────┐
│  User Output    │
│  (Clear msg)    │
└─────────────────┘
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.12+ | Modern async support, type hints |
| **MCP SDK** | mcp | 1.0.0+ | Model Context Protocol implementation |
| **HTTP Client** | httpx | 0.27+ | Async HTTP with connection pooling |
| **CLI Framework** | click | (via mcp) | Command-line interface |
| **Validation** | pydantic | 2.0+ | Schema validation, type safety |
| **Logging** | structlog | 24.1+ | Structured JSON logging |
| **Vector DB** | chromadb | 0.4.24+ | Local semantic search |
| **Embeddings** | sentence-transformers | 2.6+ | Text embeddings generation |
| **AMQP Client** | aio-pika | 9.5-11 | Async AMQP protocol |

### Development Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Unit and integration testing |
| **pytest-cov** | Code coverage reporting |
| **pytest-asyncio** | Async test support |
| **testcontainers** | RabbitMQ integration tests |
| **black** | Code formatting |
| **ruff** | Fast linting |
| **mypy** | Static type checking |
| **pre-commit** | Git hooks for quality checks |

### Build & Deployment

| Tool | Purpose |
|------|---------|
| **uv** | Fast Python package installer |
| **hatchling** | Modern build backend |
| **semantic-release** | Automated versioning |

---

## Performance Architecture

### Performance Targets & Classification

| Operation Type | Target | Classification | Characteristics |
|---------------|--------|----------------|------------------|
| Semantic search | < 100ms | Basic | Vector similarity search |
| List operations | < 2s/page | Complex | Client-side pagination, aggregations |
| CRUD operations | < 1s | Complex | Validation, safety checks, audit logging |

### Optimization Strategies

#### 1. Connection Pooling

```python
# HTTP client with persistent connections
session = httpx.Client(
    timeout=httpx.Timeout(5.0),
    transport=httpx.HTTPTransport(
        retries=3,
        limits=httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20,
            keepalive_expiry=30.0
        )
    )
)
```

**Benefits**:
- Reduces TCP handshake overhead
- Reuses TLS sessions
- Improves latency by 50-200ms per request

---

#### 2. Client-Side Pagination

**Why client-side?**
- RabbitMQ Management API doesn't support server-side pagination
- Prevents memory exhaustion with large datasets
- Enables consistent pagination metadata

**Implementation**:
```python
def paginate_results(items: List[T], page: int, page_size: int) -> PaginatedResponse[T]:
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaginatedResponse(
        items=items[start:end],
        pagination=PaginationMetadata(
            page=page,
            pageSize=page_size,
            totalItems=total_items,
            totalPages=total_pages,
            hasNextPage=page < total_pages,
            hasPreviousPage=page > 1
        )
    )
```

**Memory efficiency**: Processes entire list in memory, but limits output size

---

#### 3. Virtual Host Validation Caching

**Problem**: Every operation validates vhost existence (HTTP GET)

**Solution**: 60-second cache

```python
# Cache structure
cache = {
    "vhost:/production": {
        "exists": True,
        "timestamp": 1633024800,
        "ttl": 60
    }
}

# Cache logic
def validate_vhost_exists(vhost: str, executor: RabbitMQExecutor) -> None:
    cache_key = f"vhost:{vhost}"
    
    if cache_key in cache:
        entry = cache[cache_key]
        if time.time() - entry["timestamp"] < entry["ttl"]:
            if entry["exists"]:
                return  # Cache hit
            # Cache indicates vhost doesn't exist, check again
    
    # Cache miss or expired, check RabbitMQ
    response = executor.get(f"/api/vhosts/{vhost}")
    
    if response.status_code == 200:
        cache[cache_key] = {"exists": True, "timestamp": time.time(), "ttl": 60}
    elif response.status_code == 404:
        # Don't cache 404, might be created soon
        raise ValidationError(code="VHOST_NOT_FOUND", ...)
```

**Benefits**:
- Reduces HTTP requests by ~95% for sequential operations
- 60-second TTL balances freshness and performance
- Invalidates on 404 to allow immediate retry after vhost creation

---

#### 4. Timeout Strategy

**Different timeouts for different operation types**:

```python
# CRUD operations (complex: validations, safety checks, audit logging)
CRUD_TIMEOUT = 5.0  # seconds

# List operations (complex: client-side pagination, memory processing)
LIST_TIMEOUT = 30.0  # seconds

# Semantic search (basic operation)
SEARCH_TIMEOUT = 0.1  # 100ms
```

**Retry strategy**:
```python
# Exponential backoff for network errors
retry_delays = [1, 2, 4]  # seconds
max_retries = 3
```

---

#### 5. Vector Search Optimization

**Pre-computed embeddings**: All operation embeddings generated at build time

**Index structure**: ChromaDB with HNSW (Hierarchical Navigable Small World) index

**Search optimization**:
- Limit results to top 10 (configurable)
- Use metadata filtering for tag-based refinement
- Index size < 50MB (fast to load)

---

## Security Architecture

### Authentication

**HTTP Basic Auth** (RabbitMQ standard):
```
Authorization: Basic base64(username:password)
```

**TLS/SSL Support**:
- Configurable per connection
- Validates server certificates
- Supports custom CA bundles

### Authorization

**Permission Model** (enforced by RabbitMQ):
- **configure**: Create/delete resources
- **write**: Publish messages, create bindings
- **read**: Read queue/exchange details, consume messages

### Credential Management

**Never log credentials**:
```python
# structlog processor sanitizes sensitive fields
def sanitize_credentials(logger, method_name, event_dict):
    for key in ["password", "token", "api_key", "secret"]:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"
    return event_dict
```

**Environment variables** (recommended):
```bash
RABBITMQ_HOST=localhost
RABBITMQ_PORT=15672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=secret  # Stored in secure vault, not committed
```

### Audit Logging

**All create/delete operations logged**:
```json
{
  "timestamp": "2025-10-16T12:34:56.789Z",
  "level": "INFO",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "operation": "queue.create",
  "vhost": "/production",
  "resource_name": "orders-queue",
  "user": "admin",
  "result": "success",
  "duration_ms": 234
}
```

**Retention policy**:
- **Audit logs**: 365 days (compliance)
- **Error logs**: 90 days
- **Info logs**: 30 days

---

## Testing Architecture

### Test Pyramid

```
         ┌──────────┐
         │   E2E    │  < 5% (manual testing with real RabbitMQ)
         └──────────┘
       ┌──────────────┐
       │ Integration  │  ~20% (testcontainers with RabbitMQ)
       └──────────────┘
    ┌──────────────────┐
    │   Unit Tests     │  ~75% (fast, isolated, mocked)
    └──────────────────┘
```

### Test Categories

#### 1. Unit Tests (`tests/unit/`)

**Coverage target**: 80% minimum

**Characteristics**:
- Fast (< 1s total runtime)
- Isolated (no external dependencies)
- Mocked HTTP responses

**Examples**:
```python
# tests/unit/test_validation.py
def test_validate_name_rejects_special_chars():
    with pytest.raises(ValidationError) as exc_info:
        validate_name("my queue!")
    
    assert exc_info.value.code == "INVALID_NAME"
    assert "Remove special characters" in exc_info.value.action
```

---

#### 2. Integration Tests (`tests/integration/`)

**Uses**: `testcontainers-python` to spin up real RabbitMQ

**Characteristics**:
- Slower (30-60s total runtime)
- Real RabbitMQ interactions
- Tests end-to-end flows

**Example**:
```python
# tests/integration/test_queue_operations.py
@pytest.fixture
def rabbitmq_container():
    with RabbitMQContainer() as container:
        yield container

def test_create_and_delete_queue(rabbitmq_container):
    executor = RabbitMQExecutor(
        host=rabbitmq_container.get_host(),
        port=rabbitmq_container.get_port("15672"),
        user="guest",
        password="guest"
    )
    
    # Create queue
    result = create_queue(executor, vhost="/", name="test-queue")
    assert result.name == "test-queue"
    
    # Verify exists
    queues = list_queues(executor, vhost="/")
    assert any(q.name == "test-queue" for q in queues)
    
    # Delete queue
    delete_queue(executor, vhost="/", name="test-queue")
    
    # Verify deleted
    queues = list_queues(executor, vhost="/")
    assert not any(q.name == "test-queue" for q in queues)
```

---

#### 3. Contract Tests (`tests/contract/`)

**Purpose**: Validate requests/responses match OpenAPI spec

**Uses**: `schemathesis` for property-based testing

**Example**:
```python
# tests/contract/test_openapi_compliance.py
import schemathesis

schema = schemathesis.from_path("specs/.../queue-operations.yaml")

@schema.parametrize()
def test_api_compliance(case):
    # Generates test cases from OpenAPI spec
    response = case.call()
    case.validate_response(response)
```

---

### Test Execution

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests (requires Docker)
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_validation.py

# Run with verbose output
pytest -v

# Run with specific markers
pytest -m "not slow"
```

---

## Design Decisions

### D1: Why MCP instead of REST API?

**Decision**: Implement MCP server with built-in CLI

**Rationale**:
- **LLM integration**: MCP designed for LLM tool use
- **Semantic discovery**: Natural language operation search
- **Future-proof**: MCP is emerging standard for AI agents
- **Dual interface**: MCP tools + CLI commands in one project

**Trade-offs**:
- Learning curve for MCP protocol
- Smaller ecosystem than REST
- But: Better alignment with AI/LLM use cases

---

### D2: Why OpenAPI as Source of Truth?

**Decision**: Define all operations in OpenAPI YAML, generate code

**Rationale**:
- **Single source**: One place for operation definitions
- **Automatic validation**: Pydantic enforces schemas
- **Documentation**: API docs from specs
- **Contract testing**: Validate against spec
- **Tooling**: Rich ecosystem (editors, validators, generators)

**Trade-offs**:
- Extra build step (generate schemas)
- But: Prevents schema drift, catches errors early

---

### D3: Why Three Tools Instead of Many?

**Decision**: Use semantic discovery pattern (3 tools)

**Rationale**:
- **Scalability**: Unlimited operations without tool explosion
- **Constitution compliance**: Stay under 15-tool limit
- **Discoverability**: Natural language finds operations
- **Maintenance**: Add operations without changing MCP interface

**Trade-offs**:
- Slight complexity in routing logic
- But: Massively improves scalability and maintainability

---

### D4: Why Client-Side Pagination?

**Decision**: Paginate results in application, not RabbitMQ API

**Rationale**:
- **RabbitMQ limitation**: Management API doesn't support pagination
- **Consistency**: Uniform pagination across all list operations
- **Memory efficiency**: Limits output size, prevents OOM
- **Performance**: Target < 2s per page achievable

**Trade-offs**:
- Loads full list into memory before paginating
- But: Acceptable for target scale (1000 resources)
- Future: Could optimize with streaming if needed

---

### D5: Why 60-Second VHost Cache?

**Decision**: Cache vhost validation for 60 seconds

**Rationale**:
- **Performance**: Reduces HTTP GET on every operation
- **Balance**: 60s is long enough to help, short enough to stay fresh
- **Industry standard**: Common in enterprise RabbitMQ apps
- **Invalidation**: Cache miss on errors allows immediate retry

**Trade-offs**:
- Potential 60s lag if vhost deleted
- But: Vhost deletion is rare, benefits outweigh risks

---

### D6: Why structlog Instead of Standard Logging?

**Decision**: Use structlog for structured JSON logging

**Rationale**:
- **Machine-readable**: JSON output for log aggregation systems
- **Rich context**: Correlation IDs, operation metadata
- **Processors**: Automatic sanitization, formatting
- **Performance**: Efficient structured logging

**Trade-offs**:
- Slightly more complex setup
- But: Essential for enterprise audit requirements

---

### D7: Why ChromaDB for Vector Search?

**Decision**: Use ChromaDB for semantic search, commit index to repo

**Rationale**:
- **Local**: No external service dependencies
- **Fast**: < 100ms search performance
- **Small**: Index < 50MB, fits in repo
- **Simple**: File-based, no server setup

**Trade-offs**:
- Not suitable for millions of operations
- But: Perfect for ~100 operations in this project

---

### D8: Why LGPL v3.0 License?

**Decision**: License under LGPL v3.0 (not MIT or Apache)

**Rationale**:
- **Copyleft**: Requires sharing modifications
- **Library exception**: Allows use in proprietary software
- **Community**: Encourages contributions
- **Compatibility**: Compatible with most projects

**Trade-offs**:
- More restrictive than MIT
- But: Aligns with open-source values while allowing commercial use

---

## Conclusion

This architecture prioritizes:

1. **Scalability**: Semantic discovery pattern supports unlimited operations
2. **Performance**: Optimizations for operations with 1000+ resources
3. **Safety**: Built-in validations prevent data loss
4. **Maintainability**: OpenAPI-driven design reduces duplication
5. **Observability**: Structured logging enables troubleshooting
6. **Testability**: High coverage with unit, integration, and contract tests

For implementation details, see:
- **API Reference**: `docs/API.md`
- **Usage Examples**: `docs/EXAMPLES.md`
- **Contributing**: `docs/CONTRIBUTING.md`

---

*Architecture version 1.0 - October 2025*
