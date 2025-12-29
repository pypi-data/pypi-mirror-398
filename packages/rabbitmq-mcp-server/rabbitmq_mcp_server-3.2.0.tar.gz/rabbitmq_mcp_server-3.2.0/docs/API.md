# API Reference

Complete API documentation for RabbitMQ MCP Server operations.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Pagination](#pagination)
- [Error Handling](#error-handling)
- [Queue Operations](#queue-operations)
- [Exchange Operations](#exchange-operations)
- [Binding Operations](#binding-operations)
- [Troubleshooting](#troubleshooting)

---

## Overview

The RabbitMQ MCP Server exposes RabbitMQ Management API operations through the Model Context Protocol (MCP) using a semantic discovery pattern with three core tools:

1. **search-ids**: Semantic search for available operations
2. **get-id**: Get detailed schema for a specific operation
3. **call-id**: Execute an operation with validation

All operations follow OpenAPI 3.1.0 specifications defined in `specs/003-essential-topology-operations/contracts/`.

### Performance Targets

| Operation Type | Target Latency | Classification |
|---------------|----------------|----------------|
| Semantic search (`search-ids`) | < 100ms | Basic operation |
| List operations (paginated) | < 2s per page | Complex operation |
| Create/Delete operations | < 1s | Complex operation |

---

## Authentication

All operations require RabbitMQ Management API credentials:

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/",
    "use_tls": false
  }
}
```

### Authentication Methods

- **HTTP Basic Auth**: Default authentication using username/password
- **TLS/SSL**: Enable with `use_tls: true` for secure connections

### Permission Requirements

| Operation | Required Permission |
|-----------|-------------------|
| `queues.list` | read on vhost |
| `queues.create` | configure on vhost |
| `queues.delete` | configure on vhost |
| `exchanges.list` | read on vhost |
| `exchanges.create` | configure on vhost |
| `exchanges.delete` | configure on vhost |
| `bindings.list` | read on vhost |
| `bindings.create` | read + write on resources |
| `bindings.delete` | read + write on resources |

---

## Pagination

**All list operations require mandatory pagination** to handle large datasets efficiently.

### Pagination Parameters

```json
{
  "pagination": {
    "page": 1,          // Page number (1-based, minimum: 1)
    "pageSize": 50      // Items per page (1-200, default: 50)
  }
}
```

### Pagination Response Metadata

All list operations return pagination metadata:

```json
{
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalItems": 237,
    "totalPages": 5,
    "hasNextPage": true,
    "hasPreviousPage": false
  },
  "items": [...]
}
```

### Pagination Limits

- **Minimum page size**: 1
- **Maximum page size**: 200
- **Default page size**: 50

---

## Error Handling

All errors follow a standardized format with four required elements:

```json
{
  "code": "ERROR_CODE",
  "field": "affected_field",
  "expected": "expected_value",
  "actual": "provided_value",
  "action": "Suggested corrective action"
}
```

### Common Error Codes

| Code | HTTP Status | Description | Action |
|------|-------------|-------------|--------|
| `INVALID_NAME` | 400 | Invalid resource name | Remove special characters, use alphanumeric only |
| `INVALID_EXCHANGE_TYPE` | 400 | Invalid exchange type | Use: direct, topic, fanout, or headers |
| `VHOST_NOT_FOUND` | 404 | Virtual host does not exist | Create vhost or specify valid vhost |
| `QUEUE_NOT_FOUND` | 404 | Queue does not exist | Verify queue name and vhost |
| `EXCHANGE_NOT_FOUND` | 404 | Exchange does not exist | Verify exchange name and vhost |
| `QUEUE_NOT_EMPTY` | 409 | Queue has messages | Use --force flag or drain queue first |
| `EXCHANGE_HAS_BINDINGS` | 409 | Exchange has active bindings | Remove all bindings before deleting exchange |
| `RESOURCE_EXISTS` | 409 | Resource already exists | Use different name or delete existing resource |
| `UNAUTHORIZED` | 401/403 | Insufficient permissions | Check user permissions on vhost |
| `CONNECTION_ERROR` | 503 | Network/connection failure | Verify RabbitMQ is running and accessible |

### Error Examples

#### Invalid Name

```json
{
  "code": "INVALID_NAME",
  "field": "queue_name",
  "expected": "alphanumeric characters, dots, dashes, underscores only",
  "actual": "my queue!",
  "action": "Remove special characters. Valid name example: my-queue"
}
```

#### Queue Not Empty

```json
{
  "code": "QUEUE_NOT_EMPTY",
  "field": "message_count",
  "expected": "0",
  "actual": "1523",
  "action": "Drain queue messages first or use --force flag to delete anyway"
}
```

---

## Queue Operations

### queues.list

List all queues with statistics and message counts.

**Operation ID**: `queues.list`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "pagination": {
    "page": 1,
    "pageSize": 50
  },
  "vhost": "/"  // Optional: filter by specific vhost
}
```

#### Response

```json
{
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalItems": 12,
    "totalPages": 1,
    "hasNextPage": false,
    "hasPreviousPage": false
  },
  "items": [
    {
      "name": "orders-queue",
      "vhost": "/",
      "durable": true,
      "auto_delete": false,
      "exclusive": false,
      "messages": 1523,
      "messages_ready": 1200,
      "messages_unacknowledged": 323,
      "consumers": 5,
      "state": "running",
      "memory": 4096000
    }
  ]
}
```

#### Column Order (Table Format)

1. Name
2. Durable/Exclusive/Auto-delete flags
3. Messages/Consumers/Memory statistics

---

### queues.create

Create a new queue with specified options.

**Operation ID**: `queues.create`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "vhost": "/",
  "name": "orders-queue",
  "options": {
    "durable": true,
    "auto_delete": false,
    "exclusive": false,
    "arguments": {
      "x-max-length": 10000,
      "x-message-ttl": 3600000
    }
  }
}
```

#### Queue Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `durable` | boolean | `true` | Queue survives broker restart |
| `auto_delete` | boolean | `false` | Queue deleted when last consumer disconnects |
| `exclusive` | boolean | `false` | Queue can only be used by one connection |
| `arguments` | object | `{}` | Additional queue arguments (see below) |

#### Common Queue Arguments

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `x-max-length` | integer | Maximum queue length | `10000` |
| `x-message-ttl` | integer | Message TTL in milliseconds | `3600000` (1 hour) |
| `x-expires` | integer | Queue expires after milliseconds of inactivity | `86400000` (1 day) |
| `x-max-priority` | integer | Enable priority queue (0-255) | `10` |
| `x-dead-letter-exchange` | string | Dead letter exchange name | `"dlx-exchange"` |
| `x-dead-letter-routing-key` | string | Dead letter routing key | `"failed"` |

#### Validation Rules

- **Name**: 1-255 characters, alphanumeric, dots, dashes, underscores only (`^[a-zA-Z0-9._-]{1,255}$`)
- **Virtual host**: Must exist before creating queue
- **Duplicate detection**: Returns 409 error if queue already exists

#### Response

```json
{
  "name": "orders-queue",
  "vhost": "/",
  "durable": true,
  "auto_delete": false,
  "exclusive": false,
  "arguments": {
    "x-max-length": 10000,
    "x-message-ttl": 3600000
  }
}
```

---

### queues.delete

Delete a queue with safety validation.

**Operation ID**: `queues.delete`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "vhost": "/",
  "name": "orders-queue",
  "force": false  // Optional: force delete even if queue has messages
}
```

#### Safety Validation

- **Message count check**: Blocks deletion if queue has messages (unless `force=true`)
- **Empty queues**: Always allowed to delete
- **Force flag**: Bypasses message count validation (use with caution)

#### Response

```json
{
  "success": true,
  "message": "Queue 'orders-queue' deleted successfully"
}
```

#### Error Cases

**Queue not empty (without --force)**:
```json
{
  "code": "QUEUE_NOT_EMPTY",
  "field": "message_count",
  "expected": "0",
  "actual": "1523",
  "action": "Drain queue messages first or use --force flag"
}
```

---

## Exchange Operations

### exchanges.list

List all exchanges with type and binding information.

**Operation ID**: `exchanges.list`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "pagination": {
    "page": 1,
    "pageSize": 50
  },
  "vhost": "/"  // Optional: filter by specific vhost
}
```

#### Response

```json
{
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalItems": 8,
    "totalPages": 1,
    "hasNextPage": false,
    "hasPreviousPage": false
  },
  "items": [
    {
      "name": "orders-exchange",
      "vhost": "/",
      "type": "topic",
      "durable": true,
      "auto_delete": false,
      "internal": false,
      "bindings_count": 12
    }
  ]
}
```

#### Column Order (Table Format)

1. Name
2. Type/Durable/Auto-delete flags
3. Bindings count (+ message stats with --verbose)

---

### exchanges.create

Create a new exchange with specified type and options.

**Operation ID**: `exchanges.create`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "vhost": "/",
  "name": "orders-exchange",
  "type": "topic",
  "options": {
    "durable": true,
    "auto_delete": false,
    "internal": false,
    "arguments": {
      "alternate-exchange": "fallback-exchange"
    }
  }
}
```

#### Exchange Types

| Type | Description | Use Case |
|------|-------------|----------|
| `direct` | Exact routing key match | Point-to-point messaging |
| `topic` | Pattern matching with wildcards | Pub/sub with flexible routing |
| `fanout` | Broadcast to all bindings | Broadcast messaging |
| `headers` | Match based on message headers | Complex routing logic |

#### Exchange Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `durable` | boolean | `true` | Exchange survives broker restart |
| `auto_delete` | boolean | `false` | Exchange deleted when last binding removed |
| `internal` | boolean | `false` | Exchange cannot receive published messages directly |
| `arguments` | object | `{}` | Additional exchange arguments |

#### Common Exchange Arguments

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `alternate-exchange` | string | Alternate exchange for unroutable messages | `"fallback-exchange"` |

#### Validation Rules

- **Name**: 1-255 characters, alphanumeric, dots, dashes, underscores only
- **Type**: Must be one of: `direct`, `topic`, `fanout`, `headers`
- **Virtual host**: Must exist before creating exchange
- **Duplicate detection**: Returns 409 error if exchange already exists

#### Response

```json
{
  "name": "orders-exchange",
  "vhost": "/",
  "type": "topic",
  "durable": true,
  "auto_delete": false,
  "internal": false
}
```

---

### exchanges.delete

Delete an exchange with safety validation.

**Operation ID**: `exchanges.delete`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "vhost": "/",
  "name": "orders-exchange"
}
```

#### Safety Validation

- **System exchanges**: Cannot delete exchanges starting with `amq.` or empty string `""`
- **Active bindings**: Blocks deletion if exchange has any bindings
- **Remove bindings first**: All bindings must be deleted before exchange can be removed

#### Response

```json
{
  "success": true,
  "message": "Exchange 'orders-exchange' deleted successfully"
}
```

#### Error Cases

**Exchange has bindings**:
```json
{
  "code": "EXCHANGE_HAS_BINDINGS",
  "field": "bindings_count",
  "expected": "0",
  "actual": "12",
  "action": "Remove all 12 bindings before deleting exchange. Use 'bindings.list' to see active bindings"
}
```

**System exchange protection**:
```json
{
  "code": "SYSTEM_EXCHANGE_PROTECTED",
  "field": "exchange_name",
  "expected": "user-created exchange",
  "actual": "amq.direct",
  "action": "System exchanges (amq.*) cannot be deleted"
}
```

---

## Binding Operations

### bindings.list

List all bindings between exchanges and queues.

**Operation ID**: `bindings.list`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "pagination": {
    "page": 1,
    "pageSize": 50
  },
  "vhost": "/"  // Optional: filter by specific vhost
}
```

#### Response

```json
{
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalItems": 24,
    "totalPages": 1,
    "hasNextPage": false,
    "hasPreviousPage": false
  },
  "items": [
    {
      "source": "orders-exchange",
      "destination": "orders-queue",
      "destination_type": "queue",
      "routing_key": "orders.*.created",
      "vhost": "/",
      "properties_key": "orders.*.created~orders-queue"
    }
  ]
}
```

#### Column Order (Table Format)

1. Source exchange / Destination queue
2. Routing key
3. VHost

---

### bindings.create

Create a binding between an exchange and a queue with routing key.

**Operation ID**: `bindings.create`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "vhost": "/",
  "exchange": "orders-exchange",
  "queue": "orders-queue",
  "routing_key": "orders.*.created",
  "arguments": {}
}
```

#### Routing Key Wildcards (Topic Exchanges)

Wildcards are only allowed for `topic` type exchanges:

| Wildcard | Matches | Example Pattern | Matches | Does Not Match |
|----------|---------|-----------------|---------|----------------|
| `*` | Exactly one word | `orders.*.created` | `orders.eu.created` | `orders.eu.us.created` |
| `#` | Zero or more words | `orders.#` | `orders.created`<br>`orders.eu.created`<br>`orders.eu.us.created` | N/A (matches all) |

#### Example Patterns

```bash
# Match orders from any single region
routing_key: "orders.*.created"
  ✓ orders.eu.created
  ✓ orders.us.created
  ✗ orders.eu.us.created (too many levels)

# Match all order events
routing_key: "orders.#"
  ✓ orders.created
  ✓ orders.eu.created
  ✓ orders.eu.us.created
  ✓ orders.eu.us.warehouse.created

# Match specific patterns
routing_key: "orders.eu.*.created"
  ✓ orders.eu.warehouse.created
  ✗ orders.us.warehouse.created
  ✗ orders.eu.warehouse.germany.created
```

#### Validation Rules

- **Exchange must exist**: Validates exchange existence before creating binding
- **Queue must exist**: Validates queue existence before creating binding
- **Wildcards**: Only allowed in `topic` exchanges
- **Duplicate detection**: Returns 409 error if binding already exists

#### Response

```json
{
  "source": "orders-exchange",
  "destination": "orders-queue",
  "routing_key": "orders.*.created",
  "vhost": "/",
  "properties_key": "orders.*.created~orders-queue"
}
```

#### Error Cases

**Exchange or queue does not exist**:
```json
{
  "code": "RESOURCE_NOT_FOUND",
  "field": "resources",
  "expected": "existing exchange and queue",
  "actual": "missing: exchange 'orders-exchange'",
  "action": "Create exchange 'orders-exchange' first using exchanges.create"
}
```

**Invalid wildcards for non-topic exchange**:
```json
{
  "code": "INVALID_ROUTING_KEY",
  "field": "routing_key",
  "expected": "no wildcards for direct exchange",
  "actual": "orders.*.created",
  "action": "Remove wildcards (* or #) or use a topic exchange instead"
}
```

---

### bindings.delete

Delete a specific binding.

**Operation ID**: `bindings.delete`

#### Parameters

```json
{
  "connection": {
    "host": "localhost",
    "port": 15672,
    "user": "guest",
    "password": "guest",
    "vhost": "/"
  },
  "vhost": "/",
  "exchange": "orders-exchange",
  "queue": "orders-queue",
  "properties_key": "orders.*.created~orders-queue"
}
```

#### Properties Key

The `properties_key` uniquely identifies a binding and can be obtained from `bindings.list` response. It typically combines the routing key and destination.

#### Response

```json
{
  "success": true,
  "message": "Binding deleted successfully"
}
```

---

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to RabbitMQ Management API

**Solutions**:
1. Verify RabbitMQ is running: `rabbitmq-diagnostics status`
2. Check Management plugin is enabled: `rabbitmq-plugins enable rabbitmq_management`
3. Verify port 15672 is accessible: `curl http://localhost:15672/api/overview`
4. Check firewall rules allow port 15672

### Authentication Failures

**Problem**: 401 Unauthorized or 403 Forbidden errors

**Solutions**:
1. Verify credentials are correct
2. Check user has required permissions: `rabbitmqctl list_permissions -p /`
3. Grant necessary permissions: `rabbitmqctl set_permissions -p / guest ".*" ".*" ".*"`

### Virtual Host Not Found

**Problem**: "Virtual host does not exist" error

**Solutions**:
1. List available vhosts: `rabbitmqctl list_vhosts`
2. Create vhost: `rabbitmqctl add_vhost /production`
3. Grant permissions: `rabbitmqctl set_permissions -p /production guest ".*" ".*" ".*"`

### Pagination Issues

**Problem**: List operations timeout or return incomplete results

**Solutions**:
1. Reduce `pageSize` parameter (try 25 or 10)
2. Filter by specific vhost to reduce result set
3. Check RabbitMQ server performance and memory

### Performance Degradation

**Problem**: Operations taking longer than expected

**Solutions**:
1. Enable connection pooling (keep-alive enabled by default)
2. Use pagination with smaller page sizes
3. Filter results by vhost to reduce processing
4. Check RabbitMQ server resources (CPU, memory, disk I/O)
5. Review RabbitMQ logs for performance warnings

### Wildcard Pattern Not Matching

**Problem**: Topic exchange bindings not routing messages correctly

**Solutions**:
1. Verify exchange type is `topic` (wildcards only work with topic exchanges)
2. Check routing key format: words separated by dots
3. Test patterns:
   - `*` matches exactly one word
   - `#` matches zero or more words
4. Verify message routing key matches the binding pattern

### Memory Issues

**Problem**: Application consuming excessive memory

**Solutions**:
1. Reduce pagination page size (use pageSize <= 50)
2. Process results in smaller batches
3. Check for memory leaks in custom integrations
4. Monitor memory usage stays under 1GB per instance

---

## Additional Resources

- **OpenAPI Specifications**: `specs/003-essential-topology-operations/contracts/`
- **Architecture Documentation**: `docs/ARCHITECTURE.md`
- **Usage Examples**: `docs/EXAMPLES.md`
- **Contributing Guide**: `docs/CONTRIBUTING.md`
- **RabbitMQ Management API**: https://www.rabbitmq.com/management.html
- **MCP Protocol**: https://modelcontextprotocol.io/

---

*Last Updated: October 2025*
