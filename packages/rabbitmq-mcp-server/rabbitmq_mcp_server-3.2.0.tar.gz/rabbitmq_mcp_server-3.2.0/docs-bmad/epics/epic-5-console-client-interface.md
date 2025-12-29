# Epic 5: Console Client Interface

**Goal**: Implement standalone CLI that wraps MCP server functionality in a human-friendly command-line interface, enabling direct RabbitMQ management without AI assistant integration.

**Value**: Provides alternative access method for developers who prefer CLI tools, enables scripting and automation, and validates MCP server functionality independently of AI assistants. Extends **zero context switching** to CLI workflows - beautiful terminal output keeps focus on task.

**Product Differentiator**: Dual-mode access (MCP + CLI) means users choose their workflow - AI conversation for exploration, CLI for automation and scripting.

**Covered FRs**: FR-022

---

## Story 5.1: CLI Command Structure & Argument Parsing

As a developer,
I want a consistent command structure `rabbitmq-mcp-server <resource> <operation> [options]`,
So that I can intuitively manage RabbitMQ resources using familiar CLI patterns.

**Acceptance Criteria:**

**Given** the CLI is installed
**When** I run `rabbitmq-mcp-server queue list --vhost=/`
**Then** command is parsed into: resource="queue", operation="list", options={vhost: "/"}

**And** resource types supported: queue, exchange, binding, message, connection

**And** common options include: --host, --port, --user, --password, --vhost, --format (table/json), --insecure (disable TLS verification), --help

**And** options follow precedence: CLI args > env vars > config file > defaults

**And** invalid resource returns error: "Unknown resource 'queu'. Did you mean 'queue'?"

**And** missing operation returns error: "No operation specified. Usage: rabbitmq-mcp-server queue <operation>"

**And** --help displays: usage, available operations, option descriptions, examples

**And** --version displays: "rabbitmq-mcp-server version {version}"

**Prerequisites:** Story 1.1 (project setup), Story 2.1 (configuration management)

**Technical Notes:**
- Use argparse or click library for CLI argument parsing
- Entry point in pyproject.toml: [project.scripts] rabbitmq-mcp-server = "rabbitmq_mcp.cli:main"
- Resource aliases: queue/queues, exchange/exchanges, binding/bindings
- Positional arguments: resource and operation (required)
- Optional arguments: --host, --port, etc. (use - or -- prefix)
- Environment variables: RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_VHOST
- Config file: ./config/config.toml or --config path
- Did-you-mean suggestions for typos using fuzzy matching (editdistance)

---

## Story 5.2: Queue Management Commands

As a DevOps engineer,
I want CLI commands for all queue operations (list, create, delete, purge, get-details),
So that I can manage queues directly from terminal without AI assistant or web UI.

**Acceptance Criteria:**

**Given** RabbitMQ is accessible
**When** I run `rabbitmq-mcp-server queue list --vhost=/`
**Then** queues are listed in table format with columns: Name, Vhost, Durable, Messages, Consumers, Memory

**And** `queue create --name=orders --vhost=/ --durable` creates queue with specified properties

**And** `queue delete --name=orders --vhost=/` deletes queue (with safety check)

**And** `queue delete --name=orders --vhost=/ --force` bypasses safety check

**And** `queue purge --name=orders --vhost=/` removes all messages from queue

**And** `queue get --name=orders --vhost=/` displays detailed queue information

**And** all commands support --format=json for machine-readable output

**And** exit codes: 0 for success, non-zero for errors

**Prerequisites:** Story 5.1 (CLI structure), Story 3.1-3.4 (queue operations)

**Technical Notes:**
- Commands map to MCP tools: queue list → search-ids("list queues") → call-id(...)
- Table output uses rich library for formatted tables with colors
- Column ordering: Identity (Name, Vhost) → Configuration (Durable, Auto-delete) → Metrics (Messages, Consumers, Memory)
- Memory formatted in human-readable units: 1024 bytes → 1 KB, 1048576 → 1 MB
- JSON output: raw response from MCP server (pretty-printed)
- Error messages displayed to stderr, results to stdout
- Support filtering: queue list --filter="consumers=0" (no consumers)
- Support sorting: queue list --sort=messages (descending by default)

---

## Story 5.3: Exchange Management Commands

As a DevOps engineer,
I want CLI commands for exchange operations (list, create, delete, get-details),
So that I can configure message routing directly from terminal.

**Acceptance Criteria:**

**Given** RabbitMQ is accessible
**When** I run `rabbitmq-mcp-server exchange list --vhost=/`
**Then** exchanges are listed with columns: Name, Type, Vhost, Durable, Auto-delete, Internal

**And** `exchange create --name=events --type=topic --vhost=/ --durable` creates topic exchange

**And** `exchange delete --name=events --vhost=/` deletes exchange (with safety check)

**And** `exchange delete --name=events --vhost=/ --force` bypasses safety check

**And** `exchange get --name=events --vhost=/` displays detailed exchange information

**And** type validation: --type must be one of [direct, topic, fanout, headers]

**And** system exchanges (amq.*) are marked with indicator in list view

**And** all commands support --format=json

**Prerequisites:** Story 5.1 (CLI structure), Story 3.5-3.7 (exchange operations)

**Technical Notes:**
- Commands map to MCP tools via search/call pattern
- Exchange type colors in table: direct=blue, topic=green, fanout=yellow, headers=magenta
- System exchanges shown but delete command rejects them
- Default exchange ("") displayed as "(default)" in list
- Support filtering: exchange list --filter="type=topic"
- Include message rates if available: publish_in, publish_out (messages/sec)
- Document exchange type use cases in help text

---

## Story 5.4: Binding Management Commands

As a DevOps engineer,
I want CLI commands for binding operations (list, create, delete),
So that I can configure message routing rules from terminal.

**Acceptance Criteria:**

**Given** RabbitMQ is accessible
**When** I run `rabbitmq-mcp-server binding list --vhost=/`
**Then** bindings are listed with columns: Source, Destination, Destination-Type, Routing-Key, Vhost

**And** `binding create --source=events --destination=orders-queue --routing-key="order.*" --vhost=/` creates binding

**And** `binding create --source=events --destination=logs-exchange --destination-type=exchange --routing-key="log.#" --vhost=/` creates exchange-to-exchange binding

**And** `binding delete --source=events --destination=orders-queue --routing-key="order.*" --vhost=/` deletes specific binding

**And** destination-type defaults to "queue", can be "exchange"

**And** routing key supports topic patterns: * (one word), # (zero or more words)

**And** all commands support --format=json

**Prerequisites:** Story 5.1 (CLI structure), Story 3.8-3.10 (binding operations)

**Technical Notes:**
- Commands map to MCP tools: bindings.list, bindings.create, bindings.delete
- Table truncates long routing keys (>50 chars) with ellipsis for readability
- Support filtering: binding list --filter="source=events"
- Support filtering by destination: binding list --destination=orders-queue
- Routing key empty for fanout exchanges (display as "(none)")
- Headers exchange bindings show arguments instead of routing key
- Deletion requires exact match (source, destination, routing_key must all match)

---

## Story 5.5: Message Publishing Command

As a developer,
I want CLI command to publish messages to exchanges,
So that I can test message flows or send one-off messages without writing application code.

**Acceptance Criteria:**

**Given** RabbitMQ is accessible with existing exchange "events"
**When** I run `rabbitmq-mcp-server message publish --exchange=events --routing-key="order.created" --payload='{"order_id": 123}'`
**Then** message is published to the exchange

**And** payload accepts: JSON string (parsed), plain text, file path (--payload-file=./message.json)

**And** properties configurable: --persistent (delivery_mode=2), --priority=5, --content-type="application/json", --correlation-id="abc123", --headers='{"x-source":"cli"}'

**And** successful publish displays: "Message published successfully. Message ID: {id}"

**And** publish validation checks exchange existence before sending

**And** --dry-run flag validates without actually publishing

**And** exit code 0 for success, non-zero for errors

**Prerequisites:** Story 5.1 (CLI structure), Story 4.1 (publish message)

**Technical Notes:**
- Commands map to MCP tool: amqp.publish
- Payload from stdin: echo '{"data": "value"}' | rabbitmq-mcp-server message publish --exchange=events --routing-key=test --payload=-
- JSON payload auto-detected and validated
- File payload: read from --payload-file path, support JSON, XML, plain text
- Default properties: content_type=application/json (if JSON), delivery_mode=2 (persistent)
- Headers accept JSON dict string: --headers='{"key": "value"}'
- Large payloads (>100KB) show warning about size
- Support batch publish: --payload-file with JSON array publishes multiple messages

---

## Story 5.6: Message Consumption Command

As a developer,
I want CLI command to consume messages from queues,
So that I can inspect message content, debug routing issues, or monitor message flow.

**Acceptance Criteria:**

**Given** RabbitMQ is accessible with queue "orders-queue" containing messages
**When** I run `rabbitmq-mcp-server message consume --queue=orders-queue --count=10`
**Then** up to 10 messages are consumed and displayed

**And** each message displays: delivery_tag, exchange, routing_key, payload, properties, redelivered

**And** --count parameter limits messages consumed (default: 1, max: 1000)

**And** --timeout parameter sets max wait time in seconds (default: 10s)

**And** --no-ack flag auto-acknowledges messages (default: manual ack required)

**And** --ack-after flag acknowledges after displaying each message

**And** --format=json outputs messages as JSON array

**And** consuming from empty queue waits up to timeout, then displays: "No messages received within {timeout}s"

**Prerequisites:** Story 5.1 (CLI structure), Story 4.2 (consume messages), Story 4.3 (acknowledge)

**Technical Notes:**
- Commands map to MCP tools: amqp.consume, amqp.ack
- Default behavior: consume without ack (messages returned to queue if not acknowledged)
- --ack-after acknowledges each message immediately after display
- Display format: message number, delivery tag, routing key, payload preview (truncated if large)
- JSON payloads pretty-printed for readability
- Binary payloads displayed as base64 or hex dump
- Support continuous consumption: --follow (Ctrl+C to stop)
- Track and display consumption statistics: messages/sec, average size

---

## Story 5.7: Connection Health Check Command

As a DevOps engineer,
I want CLI command to check RabbitMQ connection health,
So that I can quickly diagnose connectivity issues without inspecting logs.

**Acceptance Criteria:**

**Given** RabbitMQ connection configuration
**When** I run `rabbitmq-mcp-server connection health`
**Then** health check executes for both AMQP and HTTP connections

**And** successful health check displays: "✓ AMQP connection: Connected to {host}:{port} vhost={vhost}" and "✓ HTTP API connection: Connected to {host}:{port}"

**And** failed health check displays: "✗ AMQP connection: Failed - {error}" and/or "✗ HTTP API connection: Failed - {error}"

**And** exit code 0 if all connections healthy, non-zero if any failed

**And** health check completes in <2 seconds

**And** --verbose flag shows detailed connection info: RabbitMQ version, node name, uptime, erlang version

**And** --format=json outputs health status as structured JSON

**Prerequisites:** Story 5.1 (CLI structure), Story 2.4 (health checks)

**Technical Notes:**
- Commands map to MCP tool: connection.health
- AMQP health: verify connection is open, channel is active
- HTTP health: GET /api/healthchecks/node, verify 200 OK response
- Display RabbitMQ version from HTTP API: GET /api/overview
- Colors: green ✓ for success, red ✗ for failure
- Verbose mode shows: cluster name, node name, management plugin version, memory usage, disk usage
- JSON output: {amqp: {status, host, port, vhost}, http: {status, host, port}, rabbitmq: {version, uptime}}
- Use for monitoring scripts: exit code indicates health status

---

## Story 5.8: Rich Terminal Output Formatting

As a CLI user,
I want beautiful, readable terminal output with colors, tables, and progress indicators,
So that I can quickly scan and understand command results without parsing raw data.

**Acceptance Criteria:**

**Given** any CLI command that outputs data
**When** command executes successfully
**Then** table format uses rich library with proper column alignment, headers, borders

**And** colors enhance readability: headers bold, success green, errors red, warnings yellow

**And** wide columns (names, routing keys) are truncated with ellipsis if terminal width exceeded

**And** numeric columns (messages, memory) are right-aligned

**And** boolean columns (durable, auto_delete) display as Yes/No or ✓/✗

**And** tables adapt to terminal width (responsive layout)

**And** --no-color flag disables colors for piping to files

**And** --format=json bypasses table formatting (raw JSON output)

**Prerequisites:** Story 5.1 (CLI structure), Story 5.2-5.7 (all commands)

**Technical Notes:**
- Use rich library for terminal formatting: rich.console.Console, rich.table.Table
- Detect terminal capabilities: rich automatically handles color support detection
- Column alignment: left for text, right for numbers, center for booleans
- Row limits: display first 100 rows by default, add --limit parameter for more
- Pagination for large result sets: press Enter to show next page
- Progress spinners for long operations: "Connecting to RabbitMQ..."
- Success/error messages with icons: ✓ Success, ✗ Error, ⚠ Warning, ℹ Info
- Syntax highlighting for JSON output (when --format=json)

---

## Story 5.9: Help System & Examples

As a developer,
I want comprehensive help text with examples for every command,
So that I can learn CLI usage without consulting external documentation.

**Acceptance Criteria:**

**Given** any CLI command
**When** I run `rabbitmq-mcp-server <resource> <operation> --help`
**Then** help text displays: description, usage syntax, option descriptions, examples

**And** examples show common use cases with realistic values

**And** `rabbitmq-mcp-server --help` lists all available resources and global options

**And** `rabbitmq-mcp-server queue --help` lists all queue operations

**And** help text includes: operation description, required options (marked *), optional options with defaults, exit codes, related commands

**And** examples include: simple usage, advanced usage with multiple options, piping to other commands

**And** help formatting uses colors and sections for readability

**Prerequisites:** Story 5.1 (CLI structure)

**Technical Notes:**
- Help system auto-generated from command definitions
- Examples section per command: 2-4 realistic examples
- Example format: `$ command` followed by expected output or description
- Global help shows resource hierarchy: queue (list, create, delete, purge, get)
- Related commands section: "See also: queue delete --force, exchange list"
- Tips section: "Tip: Use --format=json for scripting"
- Man page style: SYNOPSIS, DESCRIPTION, OPTIONS, EXAMPLES, SEE ALSO
- Support help search: rabbitmq-mcp-server help search "delete queue"

---
