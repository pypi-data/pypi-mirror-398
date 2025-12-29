# Consistency Rules

## API Response Format

**Success Response (HTTP Operations):**
```json
{
  "status": "success",
  "data": { /* operation result */ },
  "correlation_id": "uuid-here",
  "timestamp": "2025-11-16T12:00:00Z"
}
```

**Error Response (HTTP Operations):**
```json
{
  "status": "error",
  "error_code": "QUEUE_NOT_FOUND",
  "message": "Queue 'orders' not found in vhost '/'",
  "context": {
    "vhost": "/",
    "queue": "orders"
  },
  "correlation_id": "uuid-here",
  "timestamp": "2025-11-16T12:00:00Z"
}
```

**MCP Tool Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Operation result as formatted text"
    }
  ],
  "isError": false
}
```

## Date/Time Handling

**All timestamps must be:**
- UTC timezone
- ISO 8601 format: `YYYY-MM-DDTHH:MM:SS.sssZ`
- Generated via: `datetime.now(timezone.utc).isoformat()`

**No local timezones in logs or API responses.**

## Async/Await Pattern

**All I/O operations must be async:**
```python
# Good: Async I/O
async def fetch_queues(vhost: str) -> List[Queue]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/queues/{vhost}")
        return parse_response(response)

# Bad: Blocking I/O
def fetch_queues(vhost: str) -> List[Queue]:
    response = requests.get(f"/api/queues/{vhost}")
    return parse_response(response)
```

## Type Hints (Mandatory)

**All functions must have type hints:**
```python
# Good: Full type hints
async def get_queue(vhost: str, name: str) -> Optional[Queue]:
    """Get queue by name."""
    pass

# Bad: No type hints
async def get_queue(vhost, name):
    """Get queue by name."""
    pass
```

## Docstrings (Mandatory for Public API)

**Format: Google-style docstrings:**
```python
def complex_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """Short one-line summary.
    
    Longer description explaining what the function does,
    its purpose, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        ConnectionError: When RabbitMQ is unreachable
        
    Example:
        >>> result = complex_function("test", 20)
        >>> print(result["status"])
        "success"
    """
    pass
```
