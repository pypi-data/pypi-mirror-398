# Implementation Patterns

These patterns ensure consistent implementation across all AI agents building this project:

## Naming Conventions

**Python Code:**
- **Modules/Packages**: lowercase_with_underscores (snake_case)
  - Example: `rabbitmq_connection`, `mcp_server`, `queue_ops.py`
- **Classes**: PascalCase
  - Example: `HTTPClient`, `AMQPConnection`, `QueueOperation`
- **Functions/Methods**: lowercase_with_underscores (snake_case)
  - Example: `get_queue_details()`, `publish_message()`, `validate_vhost()`
- **Constants**: UPPERCASE_WITH_UNDERSCORES
  - Example: `NWS_API_BASE`, `DEFAULT_TIMEOUT`, `MAX_RETRY_ATTEMPTS`
- **Private Members**: Leading underscore
  - Example: `_connection_pool`, `_sanitize_password()`

**RabbitMQ Resources:**
- **Queue Names**: lowercase-with-hyphens (kebab-case)
  - Example: `orders-queue`, `payment-processing`, `dead-letter-queue`
- **Exchange Names**: lowercase-with-hyphens (kebab-case)
  - Example: `orders-exchange`, `events-topic`, `dlx-exchange`
- **Routing Keys**: dot.separated.lowercase
  - Example: `order.created`, `payment.processed`, `user.signup`

**MCP Tools:**
- **Operation IDs**: namespace.resource.action (dot-separated)
  - Example: `queues.list`, `exchanges.create`, `messages.publish`
- **Tool Names**: snake_case in code, but displayed as operation IDs
  - Example: `search_ids` → exposed as "search-ids" tool

**Configuration:**
- **Environment Variables**: UPPERCASE_WITH_UNDERSCORES
  - Example: `AMQP_HOST`, `AMQP_PORT`, `LOG_LEVEL`, `MCP_AUTH_TOKEN`
- **Config File Keys**: lowercase_with_underscores (TOML/YAML)
  - Example: `amqp_host`, `log_level`, `max_connections`

**File Naming:**
- **Python Files**: lowercase_with_underscores.py
  - Example: `http_client.py`, `queue_ops.py`, `test_search.py`
- **Test Files**: test_*.py prefix
  - Example: `test_queue_ops.py`, `test_sanitizers.py`
- **Config Files**: lowercase-with-hyphens or underscores
  - Example: `config.toml`, `logging_config.yaml`, `.env.example`

## Code Organization

**Module Structure Pattern:**
```python
# Standard library imports (alphabetical)
import asyncio
import json
from typing import Any, Dict, List, Optional

# Third-party imports (alphabetical)
import httpx
from pydantic import BaseModel, Field
import structlog

# Local application imports (alphabetical by module)
from rabbitmq_mcp_server.config import settings
from rabbitmq_mcp_server.logging import get_logger
from rabbitmq_mcp_server.models import ErrorResponse

# Module-level constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Module-level logger
logger = get_logger(__name__)
```

**Class Structure Pattern:**
```python
class ExampleClass:
    """Class docstring explaining purpose."""
    
    # Class-level constants
    DEFAULT_VALUE = "default"
    
    def __init__(self, param: str):
        """Initialize with required parameters."""
        self.param = param
        self._private_attr = None
    
    # Public methods first
    async def public_method(self) -> str:
        """Public method docstring."""
        return await self._private_method()
    
    # Private methods after public
    async def _private_method(self) -> str:
        """Private method docstring."""
        return self.param
    
    # Properties at the end
    @property
    def computed_value(self) -> str:
        """Property docstring."""
        return f"Value: {self.param}"
```

**Test Organization:**
```python
# tests/unit/test_example.py

import pytest
from rabbitmq_mcp_server.example import ExampleClass

class TestExampleClass:
    """Test suite for ExampleClass."""
    
    @pytest.fixture
    def example_instance(self):
        """Fixture providing ExampleClass instance."""
        return ExampleClass(param="test")
    
    def test_public_method_success(self, example_instance):
        """Test public_method with valid input."""
        result = await example_instance.public_method()
        assert result == "test"
    
    def test_public_method_error(self, example_instance):
        """Test public_method error handling."""
        with pytest.raises(ValueError):
            await example_instance.public_method()
```

**Directory Organization Rules:**
- Tests mirror source structure: `tests/unit/test_module.py` for `src/module.py`
- One class per file for complex classes, multiple related classes OK for simple ones
- `__init__.py` exports public API only
- Avoid circular imports: use TYPE_CHECKING for type hints

## Error Handling

**Error Response Schema (All Errors):**
```python
{
    "error_code": str,          # Enum: "QUEUE_NOT_FOUND", "INVALID_PARAMS", etc.
    "message": str,             # Human-readable error message
    "context": Dict[str, Any],  # Additional error context
    "correlation_id": str,      # Request correlation ID
    "timestamp": str            # ISO 8601 timestamp
}
```

**Error Code Categories:**
- `CONNECTION_*`: Connection failures (CONNECTION_FAILED, CONNECTION_TIMEOUT)
- `VALIDATION_*`: Input validation (VALIDATION_FAILED, INVALID_PARAMS)
- `NOT_FOUND_*`: Resource not found (QUEUE_NOT_FOUND, EXCHANGE_NOT_FOUND)
- `PERMISSION_*`: Authorization (PERMISSION_DENIED, VHOST_ACCESS_DENIED)
- `OPERATION_*`: Operation failures (OPERATION_FAILED, OPERATION_TIMEOUT)
- `INTERNAL_*`: Server errors (INTERNAL_ERROR, CONFIGURATION_ERROR)

**Exception Hierarchy:**
```python
# Base exception
class RabbitMQMCPError(Exception):
    """Base exception for all RabbitMQ MCP errors."""
    error_code: str
    context: Dict[str, Any]

# Specific exceptions
class ConnectionError(RabbitMQMCPError):
    error_code = "CONNECTION_FAILED"

class ValidationError(RabbitMQMCPError):
    error_code = "VALIDATION_FAILED"

class ResourceNotFoundError(RabbitMQMCPError):
    error_code = "NOT_FOUND"
```

**Error Handling Pattern:**
```python
async def operation(params: Dict) -> Result:
    """Perform operation with proper error handling."""
    logger.info("operation_started", params=params)
    
    try:
        # Validate inputs
        validated = validate_params(params)
        
        # Execute operation
        result = await execute(validated)
        
        logger.info("operation_completed", result=result)
        return result
        
    except ValidationError as e:
        logger.error("validation_failed", error=str(e), params=params)
        raise
        
    except httpx.TimeoutException as e:
        logger.error("operation_timeout", error=str(e))
        raise OperationError(
            error_code="OPERATION_TIMEOUT",
            message=f"Operation timed out after {DEFAULT_TIMEOUT}s",
            context={"timeout": DEFAULT_TIMEOUT}
        )
        
    except Exception as e:
        logger.error("unexpected_error", error=str(e), exc_info=True)
        raise OperationError(
            error_code="INTERNAL_ERROR",
            message="Unexpected error occurred",
            context={"original_error": str(e)}
        )
```

## Logging Strategy

**Structured Logging Pattern:**
```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Structured with context
logger.info(
    "queue_created",
    queue_name="orders",
    vhost="/",
    durable=True,
    correlation_id=request.correlation_id
)

# Bad: Unstructured string
logger.info(f"Created queue orders in vhost /")
```

**Log Levels:**
- **DEBUG**: Detailed diagnostic information (parameter values, intermediate states)
- **INFO**: Normal operation events (requests started/completed, resources created)
- **WARNING**: Unexpected but recoverable situations (retry attempts, deprecated features)
- **ERROR**: Operation failures that need attention (connection failures, validation errors)

**Required Log Fields:**
- `timestamp`: ISO 8601 format (added automatically)
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `logger`: Logger name (module path)
- `event`: Event name (snake_case action)
- `correlation_id`: Request correlation ID (added via context)

**Optional Context Fields:**
- Resource identifiers: `queue_name`, `exchange_name`, `vhost`
- Operation parameters: `durable`, `auto_delete`, `routing_key`
- Results: `message_count`, `consumer_count`, `status`
- Timing: `duration_ms`, `latency_ms`

**Sensitive Data Sanitization (Automatic):**
```python
# These patterns are automatically redacted in all logs:
- Passwords: password=SECRET → password=[REDACTED]
- Tokens: token=abc123 → token=[REDACTED]
- API Keys: api_key=xyz → api_key=[REDACTED]
- Authorization headers: Authorization: Bearer xyz → Authorization: [REDACTED]
- Connection strings: amqp://user:pass@host → amqp://[REDACTED]@host
```

**Correlation ID Propagation:**
```python
# Generated once per request, flows through entire operation
correlation_id = str(uuid.uuid4())

# Bound to logger context
logger = logger.bind(correlation_id=correlation_id)

# All subsequent logs automatically include correlation_id
logger.info("operation_started")  # Includes correlation_id
logger.info("operation_completed")  # Includes correlation_id
```
