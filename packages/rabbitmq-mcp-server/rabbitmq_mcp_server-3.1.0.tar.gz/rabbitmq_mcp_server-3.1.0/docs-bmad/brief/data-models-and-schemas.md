# Data Models and Schemas

This section consolidates all data entities, Pydantic models, database schemas, and validation rules from the specifications.

## Feature 001: Base MCP Architecture - Data Models

**Operation Entity** (Core entity for all RabbitMQ operations):
```python
class Operation(BaseModel):
    operation_id: str  # Unique identifier: "{namespace}.{resource}.{action}" (e.g., "queues.list", "exchanges.create")
    namespace: str  # Logical category from OpenAPI tag (e.g., "queues", "exchanges", "bindings")
    http_method: str  # HTTP method: GET, POST, PUT, DELETE, PATCH
    url_path: str  # URL path template (e.g., "/api/queues/{vhost}/{name}")
    description: str  # Human-readable description from OpenAPI
    parameters: Dict[str, ParameterSchema]  # Parameter definitions (path, query, body)
    request_schema: Optional[Dict[str, Any]]  # JSON schema for request body
    response_schema: Optional[Dict[str, Any]]  # JSON schema for 2xx response
    examples: Optional[List[Dict[str, Any]]]  # Example requests/responses
    tags: List[str]  # OpenAPI tags for categorization
    requires_auth: bool = True  # Authentication required flag
    rate_limit_exempt: bool = False  # Exempt from rate limiting
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_id": "queues.create",
                "namespace": "queues",
                "http_method": "PUT",
                "url_path": "/api/queues/{vhost}/{name}",
                "description": "Create a new queue in the specified vhost",
                "parameters": {...},
                "requires_auth": True
            }
        }
```

**ParameterSchema Entity**:
```python
class ParameterSchema(BaseModel):
    name: str  # Parameter name
    in_location: Literal["path", "query", "body", "header"]  # Parameter location
    type: str  # JSON schema type: string, integer, boolean, object, array
    required: bool = False  # Required flag
    description: Optional[str] = None  # Parameter description
    default: Optional[Any] = None  # Default value
    enum: Optional[List[Any]] = None  # Allowed values
    pattern: Optional[str] = None  # Regex validation pattern
    minimum: Optional[float] = None  # Min value for numbers
    maximum: Optional[float] = None  # Max value for numbers
    minLength: Optional[int] = None  # Min length for strings
    maxLength: Optional[int] = None  # Max length for strings
```

**Namespace Entity**:
```python
class Namespace(BaseModel):
    namespace: str  # Unique namespace identifier
    display_name: str  # Human-readable name
    description: str  # Namespace description
    operation_count: int  # Number of operations in namespace
```

**Schema Entity** (Pydantic model storage):
```python
class Schema(BaseModel):
    schema_name: str  # Unique schema identifier: "{operation_id}_request" or "{operation_id}_response"
    operation_id: str  # Associated operation ID
    schema_type: Literal["request", "response"]  # Schema type
    pydantic_model: str  # Serialized Pydantic model code
    json_schema: Dict[str, Any]  # JSON schema representation
```

**Embedding Entity** (Vector search):
```python
class Embedding(BaseModel):
    operation_id: str  # Associated operation ID
    embedding_vector: List[float]  # 384-dimensional vector from sentence-transformers
    text_source: str  # Source text (operation description)
    created_at: datetime  # Generation timestamp
```

**SearchResult Entity**:
```python
class SearchResult(BaseModel):
    operation_id: str  # Matched operation ID
    similarity_score: float  # Cosine similarity score (0.0-1.0)
    operation: Operation  # Full operation details
    
    @validator('similarity_score')
    def validate_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity score must be between 0.0 and 1.0")
        if v < 0.7:
            raise ValueError("Similarity score below threshold 0.7")
        return v
```

**OperationExecution Entity** (Request/response tracking):
```python
class OperationExecution(BaseModel):
    execution_id: str  # Unique execution ID (UUID4)
    operation_id: str  # Executed operation ID
    parameters: Dict[str, Any]  # Provided parameters
    started_at: datetime  # Execution start time
    completed_at: Optional[datetime] = None  # Execution completion time
    duration_ms: Optional[float] = None  # Execution duration
    status: Literal["pending", "success", "error"]  # Execution status
    result: Optional[Dict[str, Any]] = None  # Success result
    error: Optional[ErrorDetail] = None  # Error details
    correlation_id: str  # Log correlation ID
```

**ErrorDetail Entity**:
```python
class ErrorDetail(BaseModel):
    error_code: str  # MCP error code (JSON-RPC 2.0: -32600, -32601, -32602, -32603, -32700)
    message: str  # Error message
    field: Optional[str] = None  # Field name for validation errors
    expected: Optional[str] = None  # Expected value/type
    actual: Optional[str] = None  # Actual value/type
    suggested_action: Optional[str] = None  # Corrective action suggestion
    internal_trace: Optional[str] = None  # Internal stack trace (not exposed to clients)
```



**AMQP Operation Schemas** (Manually maintained):
```python
class AmqpPublishParams(BaseModel):
    exchange: str = Field(description="Target exchange name")
    routing_key: str = Field(description="Message routing key")
    body: Union[str, bytes, Dict[str, Any]] = Field(description="Message payload")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Message properties")
    mandatory: bool = Field(default=False, description="Mandatory delivery flag")
    
class AmqpConsumeParams(BaseModel):
    queue: str = Field(description="Queue to consume from")
    consumer_tag: Optional[str] = Field(default=None, description="Consumer identifier")
    auto_ack: bool = Field(default=False, description="Automatic acknowledgment")
    prefetch_count: int = Field(default=10, ge=1, le=1000, description="Prefetch limit")
    
class AmqpAckParams(BaseModel):
    delivery_tag: int = Field(description="Message delivery tag", ge=1)
    multiple: bool = Field(default=False, description="Acknowledge multiple messages")
    
class AmqpNackParams(BaseModel):
    delivery_tag: int = Field(description="Message delivery tag", ge=1)
    multiple: bool = Field(default=False, description="Nack multiple messages")
    requeue: bool = Field(default=True, description="Requeue message")
    
class AmqpRejectParams(BaseModel):
    delivery_tag: int = Field(description="Message delivery tag", ge=1)
    requeue: bool = Field(default=False, description="Requeue message (false = send to DLX)")
```

---

## Feature 007: Basic Structured Logging - Data Models

**LogEntry Entity** (Core logging entity):
```python
class LogEntry(BaseModel):
    timestamp: datetime = Field(description="Log timestamp in ISO 8601 UTC format with Z suffix")
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(description="Log level")
    message: str = Field(description="Log message", max_length=102400)  # 100KB + truncation suffix
    correlation_id: str = Field(description="Unique correlation ID (UUID4 or timestamp-based fallback)")
    schema_version: str = Field(default="1.0.0", description="Log schema version (semantic versioning)")
    logger_name: Optional[str] = Field(default=None, description="Logger name")
    module: Optional[str] = Field(default=None, description="Python module name")
    function: Optional[str] = Field(default=None, description="Function name")
    line_number: Optional[int] = Field(default=None, description="Line number")
    process_id: Optional[int] = Field(default=None, description="Process ID")
    thread_id: Optional[int] = Field(default=None, description="Thread ID")
    exception: Optional[str] = Field(default=None, description="Exception info (stack trace as single string with \\n)")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Additional context fields")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v.tzinfo is None:
            raise ValueError("Timestamp must include timezone (UTC required)")
        return v
    
    @validator('message')
    def truncate_message(cls, v):
        if len(v) > 102400:
            return v[:102397] + "...[truncated]"
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat().replace('+00:00', 'Z')
        }
```

**LogConfig Entity** (Configuration model):
```python
class LogConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    format: Literal["json", "console"] = Field(default="json", description="Output format")
    output_file: Optional[str] = Field(default="./logs/rabbitmq-mcp-{date}.log", description="Log file path pattern")
    enable_console: bool = Field(default=True, description="Enable console output")
    enable_file: bool = Field(default=True, description="Enable file output")
    enable_rabbitmq: bool = Field(default=False, description="Enable RabbitMQ destination (P2 optional)")
    rotation_trigger: Literal["midnight", "size", "both"] = Field(default="both")
    rotation_size_mb: int = Field(default=100, ge=1, le=1000, description="Size-based rotation trigger")
    retention_days: int = Field(default=30, ge=1, le=365, description="Log retention period")
    compression_enabled: bool = Field(default=True, description="Compress rotated files")
    async_buffer_size: int = Field(default=10000, ge=100, le=100000, description="Async logging buffer size")
    rabbitmq_exchange: Optional[str] = Field(default="logs", description="RabbitMQ log exchange name")
    rabbitmq_routing_key_pattern: Optional[str] = Field(default="{level}.{category}", description="Routing key pattern")
    
    @validator('rotation_size_mb')
    def validate_rotation_size(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError("rotation_size_mb must be between 1 and 1000")
        return v
    
    @validator('retention_days')
    def validate_retention(cls, v):
        if v < 1:
            raise ValueError("retention_days must be at least 1")
        if v < 30:
            warnings.warn("retention_days < 30 days is not recommended for audit compliance")
        return v
```

**SensitiveDataPattern Entity** (Redaction rules):
```python
class SensitiveDataPattern(BaseModel):
    name: str = Field(description="Pattern name")
    regex: str = Field(description="Regex pattern for detection")
    replacement: str = Field(default="[REDACTED]", description="Replacement text")
    case_sensitive: bool = Field(default=False, description="Case-sensitive matching")
    
    @validator('regex')
    def validate_regex(cls, v):
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v
    
# Default patterns
DEFAULT_SENSITIVE_PATTERNS = [
    SensitiveDataPattern(name="password", regex=r"(password|passwd|pwd)[=:]\s*\S+", replacement="password=[REDACTED]"),
    SensitiveDataPattern(name="token", regex=r"(token|apikey|api_key)[=:]\s*\S+", replacement="token=[REDACTED]"),
    SensitiveDataPattern(name="authorization", regex=r"(Authorization|Bearer)[:\s]+\S+", replacement="Authorization: [REDACTED]"),
    SensitiveDataPattern(name="connection_string", regex=r"(amqp://)[^@]+@", replacement=r"\1[REDACTED]@"),
]
```

**CorrelationContext Entity** (Context propagation):
```python
class CorrelationContext(BaseModel):
    correlation_id: str  # Current correlation ID
    parent_correlation_id: Optional[str] = None  # Parent correlation ID for nested operations
    operation_id: Optional[str] = None  # MCP operation ID
    user_id: Optional[str] = None  # User identifier
    session_id: Optional[str] = None  # Session identifier
    started_at: datetime  # Context creation time
    
    @staticmethod
    def generate_id() -> str:
        """Generate unique correlation ID (UUID4 or timestamp-based fallback)"""
        try:
            return str(uuid.uuid4())
        except Exception:
            return f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}"
```

**LogFile Entity** (File management):
```python
class LogFile(BaseModel):
    file_path: Path  # Absolute file path
    created_at: datetime  # File creation time
    size_bytes: int  # Current file size
    is_compressed: bool = False  # Compression flag
    rotation_count: int = Field(default=0, ge=0)  # Number of rotations
    
    def should_rotate(self, max_size_mb: int) -> bool:
        """Check if file should be rotated based on size"""
        return self.size_bytes >= (max_size_mb * 1024 * 1024)
    
    def is_expired(self, retention_days: int) -> bool:
        """Check if file is expired based on retention policy"""
        return (datetime.now(timezone.utc) - self.created_at).days > retention_days
```

---
