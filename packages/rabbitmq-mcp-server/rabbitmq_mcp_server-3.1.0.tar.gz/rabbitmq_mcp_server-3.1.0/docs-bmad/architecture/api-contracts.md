# API Contracts

## MCP Protocol (JSON-RPC 2.0)

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "call-id",
    "arguments": {
      "operation_id": "queues.list",
      "parameters": {
        "vhost": "/"
      }
    }
  }
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Queue list result..."
      }
    ],
    "isError": false
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "error_code": "VALIDATION_FAILED",
      "context": {"field": "vhost", "error": "Required field missing"}
    }
  }
}
```

## MCP Tools

**Tool 1: search-ids**
```python
Input Schema:
{
  "type": "object",
  "properties": {
    "query": {"type": "string", "description": "Natural language query"},
    "threshold": {"type": "number", "default": 0.7},
    "max_results": {"type": "integer", "default": 10}
  },
  "required": ["query"]
}

Output:
[
  {
    "operation_id": "queues.list",
    "description": "List all queues",
    "similarity_score": 0.89,
    "namespace": "queues"
  }
]
```

**Tool 2: get-id**
```python
Input Schema:
{
  "type": "object",
  "properties": {
    "operation_id": {"type": "string"}
  },
  "required": ["operation_id"]
}

Output:
{
  "operation_id": "queues.list",
  "http_method": "GET",
  "url_path": "/api/queues/{vhost}",
  "parameters": {...},
  "description": "...",
  "examples": [...]
}
```

**Tool 3: call-id**
```python
Input Schema:
{
  "type": "object",
  "properties": {
    "operation_id": {"type": "string"},
    "parameters": {"type": "object"}
  },
  "required": ["operation_id", "parameters"]
}

Output:
{
  "status": "success",
  "result": {...},  # Operation-specific result
  "correlation_id": "uuid"
}
```

## RabbitMQ Management API

**Queue Operations:**
```
GET    /api/queues/{vhost}/{name}     # Get queue details
PUT    /api/queues/{vhost}/{name}     # Create queue
DELETE /api/queues/{vhost}/{name}     # Delete queue
DELETE /api/queues/{vhost}/{name}/contents  # Purge queue
GET    /api/queues/{vhost}            # List queues in vhost
GET    /api/queues                    # List all queues
```

**Exchange Operations:**
```
GET    /api/exchanges/{vhost}/{name}  # Get exchange details
PUT    /api/exchanges/{vhost}/{name}  # Create exchange
DELETE /api/exchanges/{vhost}/{name}  # Delete exchange
GET    /api/exchanges/{vhost}         # List exchanges in vhost
```

**Binding Operations:**
```
GET    /api/bindings/{vhost}          # List all bindings
POST   /api/bindings/{vhost}/e/{exchange}/q/{queue}  # Create binding
DELETE /api/bindings/{vhost}/e/{exchange}/q/{queue}/{props}  # Delete binding
```

## AMQP Protocol Operations

**Message Publishing:**
```python
Operation: amqp.publish
Parameters:
  - exchange: str (required)
  - routing_key: str (required)
  - payload: Union[str, bytes, dict] (required)
  - properties: MessageProperties (optional)
  
Validation:
  - Exchange must exist (pre-check via HTTP API)
  - Payload must be serializable
  - Properties must be valid AMQP types
```

**Message Consumption:**
```python
Operation: amqp.consume
Parameters:
  - queue: str (required)
  - prefetch: int = 10
  - auto_ack: bool = False
  
Returns: Stream of messages
  - delivery_tag: int
  - exchange: str
  - routing_key: str
  - payload: Union[str, bytes, dict]
  - properties: MessageProperties
```

**Message Acknowledgment:**
```python
Operation: amqp.ack / amqp.nack / amqp.reject
Parameters:
  - delivery_tag: int (required)
  - requeue: bool = False (for nack/reject)
  
Validation:
  - delivery_tag must be from active consumer
  - No duplicate acknowledgments
```
