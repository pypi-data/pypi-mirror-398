# Usage Examples

Practical examples and use cases for RabbitMQ MCP Server.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Examples](#cli-examples)
- [MCP Tool Examples](#mcp-tool-examples)
- [Common Use Cases](#common-use-cases)
- [Advanced Scenarios](#advanced-scenarios)
- [Integration Examples](#integration-examples)
- [Debugging Tips](#debugging-tips)
- [Shell Integration](#shell-integration)

---

## Installation

### Using uvx (Recommended)

**uvx** runs Python CLI tools in isolated environments without installation:

```bash
# No installation needed! Run directly:
uvx rabbitmq-mcp-server queue list
```

### Using uv (For development)

```bash
# Clone repository
git clone https://github.com/guercheLE/rabbitmq-mcp-server.git
cd rabbitmq-mcp-server

# Install with uv
uv pip install -e ".[dev]"

# Run directly
rabbitmq-mcp-server queue list
```

### Using pip (Traditional)

```bash
pip install rabbitmq-mcp-server

# Run
rabbitmq-mcp-server queue list
```

---

## Quick Start

### 1. Check RabbitMQ is Running

```bash
# Check if RabbitMQ Management API is accessible
curl http://localhost:15672/api/overview
```

### 2. List Queues

```bash
uvx rabbitmq-mcp-server queue list \
  --host localhost \
  --port 15672 \
  --user guest \
  --password guest
```

### 3. Create a Queue

```bash
uvx rabbitmq-mcp-server queue create \
  --host localhost \
  --user guest \
  --password guest \
  --name my-first-queue \
  --durable
```

### 4. Create an Exchange

```bash
uvx rabbitmq-mcp-server exchange create \
  --host localhost \
  --user guest \
  --password guest \
  --name my-exchange \
  --type topic \
  --durable
```

### 5. Create a Binding

```bash
uvx rabbitmq-mcp-server binding create \
  --host localhost \
  --user guest \
  --password guest \
  --exchange my-exchange \
  --queue my-first-queue \
  --routing-key "orders.*.created"
```

---

## CLI Examples

### Queue Operations

#### List All Queues

```bash
# Basic list (first page, 50 items)
uvx rabbitmq-mcp-server queue list

# Specific page
uvx rabbitmq-mcp-server queue list --page 2 --page-size 25

# Filter by virtual host
uvx rabbitmq-mcp-server queue list --vhost /production

# JSON output
uvx rabbitmq-mcp-server queue list --format json

# Verbose output (more columns)
uvx rabbitmq-mcp-server queue list --verbose
```

#### Create Queue with Options

```bash
# Basic durable queue
uvx rabbitmq-mcp-server queue create \
  --name orders-queue \
  --durable

# Queue with message TTL (1 hour)
uvx rabbitmq-mcp-server queue create \
  --name temp-queue \
  --arguments '{"x-message-ttl": 3600000}'

# Priority queue (priorities 0-10)
uvx rabbitmq-mcp-server queue create \
  --name priority-queue \
  --arguments '{"x-max-priority": 10}'

# Queue with max length
uvx rabbitmq-mcp-server queue create \
  --name limited-queue \
  --arguments '{"x-max-length": 10000}'

# Dead letter queue setup
uvx rabbitmq-mcp-server queue create \
  --name main-queue \
  --arguments '{
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "failed"
  }'
```

#### Delete Queue

```bash
# Delete empty queue (safe)
uvx rabbitmq-mcp-server queue delete --name temp-queue

# Force delete queue with messages (use with caution!)
uvx rabbitmq-mcp-server queue delete --name orders-queue --force
```

---

### Exchange Operations

#### List All Exchanges

```bash
# Basic list
uvx rabbitmq-mcp-server exchange list

# Filter by vhost
uvx rabbitmq-mcp-server exchange list --vhost /staging

# With verbose stats
uvx rabbitmq-mcp-server exchange list --verbose
```

#### Create Exchanges

```bash
# Direct exchange (exact routing key match)
uvx rabbitmq-mcp-server exchange create \
  --name orders-direct \
  --type direct \
  --durable

# Topic exchange (pattern matching with wildcards)
uvx rabbitmq-mcp-server exchange create \
  --name orders-topic \
  --type topic \
  --durable

# Fanout exchange (broadcast to all bindings)
uvx rabbitmq-mcp-server exchange create \
  --name notifications-fanout \
  --type fanout \
  --durable

# Headers exchange (match on message headers)
uvx rabbitmq-mcp-server exchange create \
  --name analytics-headers \
  --type headers \
  --durable

# Exchange with alternate exchange (for unroutable messages)
uvx rabbitmq-mcp-server exchange create \
  --name primary-exchange \
  --type topic \
  --arguments '{"alternate-exchange": "fallback-exchange"}'
```

#### Delete Exchange

```bash
# Delete exchange (fails if has bindings)
uvx rabbitmq-mcp-server exchange delete --name temp-exchange

# NOTE: Cannot use --force on exchanges
# Must remove all bindings first
```

---

### Binding Operations

#### List All Bindings

```bash
# Basic list
uvx rabbitmq-mcp-server binding list

# Filter by vhost
uvx rabbitmq-mcp-server binding list --vhost /production

# Paginate through results
uvx rabbitmq-mcp-server binding list --page 1 --page-size 100
```

#### Create Bindings

```bash
# Simple binding (direct exchange)
uvx rabbitmq-mcp-server binding create \
  --exchange orders-direct \
  --queue orders-queue \
  --routing-key "order.created"

# Wildcard binding - single word (*)
uvx rabbitmq-mcp-server binding create \
  --exchange orders-topic \
  --queue eu-orders-queue \
  --routing-key "orders.*.created"
# Matches: orders.eu.created, orders.us.created
# Does NOT match: orders.eu.warehouse.created

# Wildcard binding - multiple words (#)
uvx rabbitmq-mcp-server binding create \
  --exchange orders-topic \
  --queue all-orders-queue \
  --routing-key "orders.#"
# Matches: orders.created, orders.eu.created, orders.eu.warehouse.created

# Complex pattern
uvx rabbitmq-mcp-server binding create \
  --exchange events-topic \
  --queue audit-queue \
  --routing-key "*.*.audit.#"
# Matches: user.login.audit.success, order.create.audit.validation.failed

# Binding with arguments (headers exchange)
uvx rabbitmq-mcp-server binding create \
  --exchange analytics-headers \
  --queue high-priority-queue \
  --arguments '{"x-match": "all", "priority": "high", "type": "order"}'
```

#### Delete Binding

```bash
# Delete specific binding
uvx rabbitmq-mcp-server binding delete \
  --exchange orders-topic \
  --queue orders-queue \
  --properties-key "orders.*.created~orders-queue"

# Get properties-key from binding list output
```

---

## MCP Tool Examples

### Using search-ids (Semantic Search)

```json
// Find operations related to queues
{
  "tool": "search-ids",
  "arguments": {
    "query": "how do I list all queues",
    "limit": 5
  }
}

// Response:
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

### Using get-id (Get Operation Schema)

```json
// Get details for queue creation
{
  "tool": "get-id",
  "arguments": {
    "operation_id": "queues.create"
  }
}

// Response:
{
  "operation_id": "queues.create",
  "summary": "Create a new queue",
  "parameters": {
    "connection": {
      "type": "object",
      "required": true,
      "properties": {
        "host": {"type": "string"},
        "port": {"type": "integer"},
        "user": {"type": "string"},
        "password": {"type": "string"}
      }
    },
    "vhost": {"type": "string", "required": true},
    "name": {"type": "string", "required": true},
    "options": {
      "type": "object",
      "properties": {
        "durable": {"type": "boolean"},
        "auto_delete": {"type": "boolean"}
      }
    }
  }
}
```

### Using call-id (Execute Operation)

```json
// Create a queue via MCP
{
  "tool": "call-id",
  "arguments": {
    "operation_id": "queues.create",
    "parameters": {
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
        "arguments": {
          "x-max-length": 10000
        }
      }
    }
  }
}

// Response:
{
  "success": true,
  "result": {
    "name": "orders-queue",
    "vhost": "/",
    "durable": true
  }
}
```

---

## Common Use Cases

### Use Case 1: Monitoring Queue Depths

**Goal**: Check which queues have messages waiting

```bash
#!/bin/bash

# List queues with verbose output
uvx rabbitmq-mcp-server queue list --verbose --format json > queues.json

# Use jq to filter queues with messages
cat queues.json | jq '.items[] | select(.messages > 0) | {name, messages, consumers}'
```

**Output**:
```json
{
  "name": "orders-queue",
  "messages": 1523,
  "consumers": 2
}
{
  "name": "notifications-queue",
  "messages": 87,
  "consumers": 0
}
```

**Alert on zero consumers**:
```bash
# Find queues with messages but no consumers
cat queues.json | jq -r '.items[] | select(.messages > 0 and .consumers == 0) | .name'
```

---

### Use Case 2: Setting Up Event-Driven Architecture

**Goal**: Create topic exchange with multiple queue bindings for different services

```bash
# 1. Create topic exchange for order events
uvx rabbitmq-mcp-server exchange create \
  --name order-events \
  --type topic \
  --durable

# 2. Create queues for different services
uvx rabbitmq-mcp-server queue create --name inventory-service-queue --durable
uvx rabbitmq-mcp-server queue create --name shipping-service-queue --durable
uvx rabbitmq-mcp-server queue create --name analytics-service-queue --durable

# 3. Inventory service: only order creation events
uvx rabbitmq-mcp-server binding create \
  --exchange order-events \
  --queue inventory-service-queue \
  --routing-key "orders.*.created"

# 4. Shipping service: only fulfilled orders
uvx rabbitmq-mcp-server binding create \
  --exchange order-events \
  --queue shipping-service-queue \
  --routing-key "orders.*.fulfilled"

# 5. Analytics service: all order events
uvx rabbitmq-mcp-server binding create \
  --exchange order-events \
  --queue analytics-service-queue \
  --routing-key "orders.#"
```

**Test routing**:
```bash
# Publish test message (using rabbitmqadmin or similar)
# Routing key: "orders.eu.created"
# → Goes to: inventory-service-queue, analytics-service-queue
# → Not to: shipping-service-queue
```

---

### Use Case 3: Dead Letter Queue Setup

**Goal**: Configure DLQ for handling failed messages

```bash
# 1. Create dead letter exchange
uvx rabbitmq-mcp-server exchange create \
  --name dlx \
  --type direct \
  --durable

# 2. Create dead letter queue
uvx rabbitmq-mcp-server queue create \
  --name dlq \
  --durable

# 3. Bind DLQ to DLX
uvx rabbitmq-mcp-server binding create \
  --exchange dlx \
  --queue dlq \
  --routing-key "failed"

# 4. Create main queue with DLX configuration
uvx rabbitmq-mcp-server queue create \
  --name orders-queue \
  --durable \
  --arguments '{
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "failed",
    "x-message-ttl": 300000
  }'
```

**How it works**:
- Messages in `orders-queue` expire after 5 minutes (300000ms)
- Expired messages route to `dlx` exchange with routing key `"failed"`
- `dlq` queue receives all dead-lettered messages for investigation

---

### Use Case 4: Cleanup Temporary Resources

**Goal**: Remove all temporary queues and exchanges

```bash
#!/bin/bash

# List all queues starting with "temp-"
uvx rabbitmq-mcp-server queue list --format json | \
  jq -r '.items[] | select(.name | startswith("temp-")) | .name' | \
  while read queue; do
    echo "Deleting queue: $queue"
    uvx rabbitmq-mcp-server queue delete --name "$queue" --force
  done

# List all exchanges starting with "temp-"
uvx rabbitmq-mcp-server exchange list --format json | \
  jq -r '.items[] | select(.name | startswith("temp-")) | .name' | \
  while read exchange; do
    echo "Deleting exchange: $exchange"
    uvx rabbitmq-mcp-server exchange delete --name "$exchange"
  done
```

---

### Use Case 5: Multi-Region Routing

**Goal**: Route messages to region-specific queues

```bash
# 1. Create regional topic exchange
uvx rabbitmq-mcp-server exchange create \
  --name geo-routing \
  --type topic \
  --durable

# 2. Create region-specific queues
uvx rabbitmq-mcp-server queue create --name us-east-queue --durable
uvx rabbitmq-mcp-server queue create --name us-west-queue --durable
uvx rabbitmq-mcp-server queue create --name eu-queue --durable

# 3. Bind queues with region patterns
uvx rabbitmq-mcp-server binding create \
  --exchange geo-routing \
  --queue us-east-queue \
  --routing-key "orders.us.east.*"

uvx rabbitmq-mcp-server binding create \
  --exchange geo-routing \
  --queue us-west-queue \
  --routing-key "orders.us.west.*"

uvx rabbitmq-mcp-server binding create \
  --exchange geo-routing \
  --queue eu-queue \
  --routing-key "orders.eu.*"

# 4. Create catch-all queue for other regions
uvx rabbitmq-mcp-server queue create --name global-queue --durable

uvx rabbitmq-mcp-server binding create \
  --exchange geo-routing \
  --queue global-queue \
  --routing-key "orders.#"
```

**Message routing examples**:
- `orders.us.east.12345` → `us-east-queue`, `global-queue`
- `orders.eu.london.67890` → `eu-queue`, `global-queue`
- `orders.asia.tokyo.11111` → `global-queue` only

---

## Advanced Scenarios

### Priority Queue with Multiple Priorities

```bash
# Create priority queue (0-10 priority levels)
uvx rabbitmq-mcp-server queue create \
  --name priority-orders \
  --durable \
  --arguments '{"x-max-priority": 10}'

# Publishers can set priority per message (0-10)
# Higher priority messages consumed first
```

**Use case**: VIP customer orders get priority 10, regular orders priority 5

---

### Queue with Expiration

```bash
# Queue auto-deletes after 24 hours of inactivity
uvx rabbitmq-mcp-server queue create \
  --name session-queue \
  --arguments '{"x-expires": 86400000}'
```

**Use case**: User session queues that clean up automatically

---

### Limiting Queue Length

```bash
# Queue rejects messages after reaching 1000
uvx rabbitmq-mcp-server queue create \
  --name bounded-queue \
  --arguments '{
    "x-max-length": 1000,
    "x-overflow": "reject-publish"
  }'

# Alternative: drop oldest messages when full
uvx rabbitmq-mcp-server queue create \
  --name circular-buffer \
  --arguments '{
    "x-max-length": 1000,
    "x-overflow": "drop-head"
  }'
```

---

### Delayed Message Queue

```bash
# Requires rabbitmq_delayed_message_exchange plugin
# Create delayed exchange
uvx rabbitmq-mcp-server exchange create \
  --name delayed-exchange \
  --type x-delayed-message \
  --arguments '{"x-delayed-type": "direct"}'

# Create queue for delayed messages
uvx rabbitmq-mcp-server queue create --name delayed-queue --durable

# Bind queue
uvx rabbitmq-mcp-server binding create \
  --exchange delayed-exchange \
  --queue delayed-queue \
  --routing-key "delayed"
```

**Use case**: Schedule tasks for future execution

---

## Integration Examples

### With jq (JSON Processing)

```bash
# Get queue names only
uvx rabbitmq-mcp-server queue list --format json | jq -r '.items[].name'

# Find queues with high message counts
uvx rabbitmq-mcp-server queue list --format json | \
  jq '.items[] | select(.messages > 1000) | {name, messages}'

# Calculate total messages across all queues
uvx rabbitmq-mcp-server queue list --format json | \
  jq '[.items[].messages] | add'

# Get queues with zero consumers
uvx rabbitmq-mcp-server queue list --format json | \
  jq '.items[] | select(.consumers == 0) | .name'
```

---

### With grep (Pattern Matching)

```bash
# Find queues matching pattern
uvx rabbitmq-mcp-server queue list | grep "order"

# Count exchanges by type
uvx rabbitmq-mcp-server exchange list | grep -c "topic"
```

---

### With watch (Monitoring)

```bash
# Monitor queue depths every 2 seconds
watch -n 2 'uvx rabbitmq-mcp-server queue list --format json | \
  jq ".items[] | {name, messages, consumers}"'

# Alert when queue depth exceeds threshold
watch -n 5 'uvx rabbitmq-mcp-server queue list --format json | \
  jq -e ".items[] | select(.messages > 10000)" && \
  echo "ALERT: Queue depth exceeded!"'
```

---

### In Shell Scripts (Bash)

```bash
#!/bin/bash

# Function to create queue with error handling
create_queue_safe() {
  local queue_name=$1
  
  if uvx rabbitmq-mcp-server queue create --name "$queue_name" --durable; then
    echo "✓ Created queue: $queue_name"
  else
    echo "✗ Failed to create queue: $queue_name" >&2
    return 1
  fi
}

# Create multiple queues
queues=("orders" "notifications" "analytics")
for queue in "${queues[@]}"; do
  create_queue_safe "$queue"
done
```

---

### In PowerShell

```powershell
# List all queues and convert to PowerShell objects
$queues = uvx rabbitmq-mcp-server queue list --format json | ConvertFrom-Json

# Filter queues with messages
$queues.items | Where-Object { $_.messages -gt 0 } | Select-Object name, messages

# Create queue with error handling
try {
  uvx rabbitmq-mcp-server queue create --name "orders-queue" --durable
  Write-Host "✓ Queue created successfully"
} catch {
  Write-Error "✗ Failed to create queue: $_"
}

# Delete multiple queues
$tempQueues = $queues.items | Where-Object { $_.name -like "temp-*" }
foreach ($queue in $tempQueues) {
  uvx rabbitmq-mcp-server queue delete --name $queue.name --force
}
```

---

## Debugging Tips

### Enable Verbose Logging

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

uvx rabbitmq-mcp-server queue list
```

### Check Connection

```bash
# Test RabbitMQ Management API directly
curl -u guest:guest http://localhost:15672/api/overview

# Check specific vhost
curl -u guest:guest http://localhost:15672/api/vhosts/%2F
```

### Validate Credentials

```bash
# Test with wrong credentials (should fail)
uvx rabbitmq-mcp-server queue list \
  --user wrong \
  --password invalid
# Expected: "UNAUTHORIZED" error
```

### Debug Binding Issues

```bash
# List all bindings to see routing
uvx rabbitmq-mcp-server binding list --format json | jq '.items[]'

# Check if specific binding exists
uvx rabbitmq-mcp-server binding list --format json | \
  jq '.items[] | select(.routing_key == "orders.*.created")'
```

### Performance Debugging

```bash
# Time operation execution
time uvx rabbitmq-mcp-server queue list

# Should be < 2 seconds for pagination
```

### Memory Debugging

```bash
# Monitor memory usage during operation
/usr/bin/time -v uvx rabbitmq-mcp-server queue list

# Check maximum resident set size (should be < 1GB)
```

---

## Shell Integration

### Bash Aliases

Add to `~/.bashrc` or `~/.bash_profile`:

```bash
# RabbitMQ MCP Server aliases
alias rmq='uvx rabbitmq-mcp-server'
alias rmq-ql='uvx rabbitmq-mcp-server queue list'
alias rmq-qc='uvx rabbitmq-mcp-server queue create'
alias rmq-qd='uvx rabbitmq-mcp-server queue delete'
alias rmq-el='uvx rabbitmq-mcp-server exchange list'
alias rmq-ec='uvx rabbitmq-mcp-server exchange create'
alias rmq-bl='uvx rabbitmq-mcp-server binding list'

# Usage:
# rmq-ql --verbose
# rmq-qc --name my-queue --durable
```

---

### ZSH Completion

Add to `~/.zshrc`:

```zsh
# RabbitMQ MCP Server completion
eval "$(uvx rabbitmq-mcp-server --completion zsh)"
```

---

### Environment Variables

Create `~/.rabbitmq-mcp.env`:

```bash
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=15672
export RABBITMQ_USER=admin
export RABBITMQ_PASSWORD=secret
export RABBITMQ_VHOST=/production
```

Source in shell:

```bash
source ~/.rabbitmq-mcp.env

# Now can omit connection parameters
uvx rabbitmq-mcp-server queue list
```

---

### Pre-configured Scripts

**Monitoring Script** (`monitor-queues.sh`):

```bash
#!/bin/bash
set -euo pipefail

# Monitor queue depths and alert if > threshold
THRESHOLD=1000

while true; do
  clear
  echo "=== Queue Monitoring ($(date)) ==="
  echo ""
  
  uvx rabbitmq-mcp-server queue list --format json | \
    jq -r '.items[] | "\(.name)\t\(.messages)\t\(.consumers)"' | \
    while IFS=$'\t' read -r name messages consumers; do
      if [ "$messages" -gt "$THRESHOLD" ]; then
        echo "⚠️  $name: $messages messages ($consumers consumers)"
      else
        echo "✓  $name: $messages messages ($consumers consumers)"
      fi
    done
  
  sleep 10
done
```

**Cleanup Script** (`cleanup-temp-resources.sh`):

```bash
#!/bin/bash
set -euo pipefail

echo "Cleaning up temporary RabbitMQ resources..."

# Delete temp queues
uvx rabbitmq-mcp-server queue list --format json | \
  jq -r '.items[] | select(.name | startswith("temp-")) | .name' | \
  while read queue; do
    echo "Deleting queue: $queue"
    uvx rabbitmq-mcp-server queue delete --name "$queue" --force
  done

echo "Cleanup complete!"
```

---

## Additional Resources

- **API Reference**: `docs/API.md` - Complete operation reference
- **Architecture**: `docs/ARCHITECTURE.md` - System design and decisions
- **Contributing**: `docs/CONTRIBUTING.md` - How to contribute
- **OpenAPI Specs**: `specs/003-essential-topology-operations/contracts/`

---

*Last Updated: October 2025*
