# Data Architecture

## Core Data Models

**Operation Registry Model:**
```python
class Operation(BaseModel):
    """Metadata for a single RabbitMQ operation."""
    operation_id: str  # Format: "namespace.resource.action"
    namespace: str  # Logical grouping: "queues", "exchanges", "messages"
    http_method: str  # GET, POST, PUT, DELETE, PATCH
    url_path: str  # URL template: "/api/queues/{vhost}/{name}"
    description: str  # Human-readable description for semantic search
    parameters: Dict[str, ParameterSchema]  # Parameter definitions
    request_schema: Optional[Dict[str, Any]]  # Request body schema
    response_schema: Optional[Dict[str, Any]]  # Response schema
    examples: Optional[List[Dict[str, Any]]]  # Example requests/responses
    tags: List[str]  # OpenAPI tags
    requires_auth: bool = True
    rate_limit_exempt: bool = False
```

**Semantic Embedding Model:**
```python
class Embedding(BaseModel):
    """Semantic embedding for an operation."""
    operation_id: str
    vector: List[float]  # 384-dimensional vector
    model: str = "all-MiniLM-L6-v2"
    generated_at: datetime
```

**Connection Configuration Model:**
```python
class ConnectionConfig(BaseModel):
    """RabbitMQ connection configuration."""
    # HTTP Management API
    http_host: str = "localhost"
    http_port: int = 15672
    http_use_tls: bool = False
    http_verify_ssl: bool = True
    http_timeout: int = 30
    
    # AMQP Protocol
    amqp_host: str = "localhost"
    amqp_port: int = 5672
    amqp_use_tls: bool = False
    amqp_vhost: str = "/"
    
    # Credentials
    username: str = "guest"
    password: SecretStr = "guest"  # Pydantic SecretStr type
    
    # Connection Pool
    pool_size: int = 5
    pool_timeout: int = 10
```

**Error Response Model:**
```python
class ErrorResponse(BaseModel):
    """Standardized error response."""
    error_code: str  # Enum string
    message: str  # Human-readable error
    context: Dict[str, Any] = {}  # Additional context
    correlation_id: str  # Request correlation ID
    timestamp: datetime  # UTC timestamp
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**Queue Model (Example Resource):**
```python
class Queue(BaseModel):
    """RabbitMQ queue representation."""
    name: str
    vhost: str
    durable: bool
    auto_delete: bool
    exclusive: bool = False
    arguments: Dict[str, Any] = {}
    
    # Statistics (read-only)
    messages: Optional[int] = None
    messages_ready: Optional[int] = None
    messages_unacknowledged: Optional[int] = None
    consumers: Optional[int] = None
    memory: Optional[int] = None
```

**Message Model:**
```python
class Message(BaseModel):
    """AMQP message representation."""
    payload: Union[str, bytes, Dict[str, Any]]
    properties: MessageProperties = MessageProperties()
    
class MessageProperties(BaseModel):
    """AMQP message properties."""
    content_type: str = "application/json"
    content_encoding: Optional[str] = None
    headers: Dict[str, Any] = {}
    delivery_mode: int = 1  # 1=non-persistent, 2=persistent
    priority: Optional[int] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expiration: Optional[str] = None
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    type: Optional[str] = None
    user_id: Optional[str] = None
    app_id: Optional[str] = None
```

## Data Relationships

```
Operation Registry (operations.json)
  ├── Operations (100+)
  │   ├── operation_id (unique key)
  │   ├── parameters (0..n)
  │   ├── request_schema (0..1)
  │   └── response_schema (0..1)
  └── Used by: get-id tool, call-id tool

Semantic Embeddings (embeddings.json)
  ├── Embeddings (100+)
  │   ├── operation_id (FK to Operation)
  │   └── vector (384 floats)
  └── Used by: search-ids tool

RabbitMQ Resources (runtime)
  ├── Virtual Hosts
  │   ├── Queues (0..n per vhost)
  │   ├── Exchanges (0..n per vhost)
  │   └── Bindings (0..n per vhost)
  ├── Messages (0..n per queue)
  └── Connections (0..n per server)
```

## Data Storage Strategy

**Build-Time Artifacts (Committed to Git):**
- `data/operations.json`: Operation registry (~500KB)
- `data/embeddings.json`: Pre-computed vectors (~2MB)
- `data/openapi-*.yaml`: OpenAPI specifications (~200KB each)
- `src/schemas/generated_schemas.py`: Pydantic models (~1MB)

**Runtime Data (Memory):**
- Operation registry: Loaded at startup, immutable
- Embeddings: Loaded at startup, immutable
- Connection pools: Managed in memory, auto-cleanup
- Request correlation IDs: Thread-local or async context

**Persistent Data (File System):**
- Logs: `./logs/rabbitmq-mcp-YYYY-MM-DD.log`
- Configuration: `config.toml`, `.env` (optional)

**No Database Required** - All operational data lives in RabbitMQ itself.
