# Epic 11: Configuration Import/Export

**Goal**: Enable declarative infrastructure management by allowing users to export current RabbitMQ topology as configuration files and import to recreate environments.

**Value**: Supports Infrastructure-as-Code practices, simplifies environment replication (dev → staging → prod), and enables version control of RabbitMQ topology.

**Priority**: Medium (DevOps workflow improvement)

---

## Story 11.1: Export Topology to YAML/JSON

As a DevOps engineer,
I want to export complete RabbitMQ topology (queues, exchanges, bindings) to YAML or JSON file,
So that I can version control configurations and replicate environments.

**Acceptance Criteria:**

**Given** existing RabbitMQ topology in vhost
**When** I run export command: rabbitmq-mcp-server config export --vhost=/ --output=topology.yaml
**Then** YAML file created with complete topology definition

**And** export includes: vhost configuration, queues (with all properties and arguments), exchanges (with types and properties), bindings (with routing keys), policies (if any), parameters

**And** export format supports both YAML and JSON: --format=yaml (default) or --format=json

**And** export filters supported: --queues-only, --exchanges-only, --exclude-system (skip amq.* exchanges)

**And** sensitive data excluded: no passwords or tokens in export (only configuration)

**And** export is idempotent: importing exported config recreates identical topology

**And** export completes in <5 seconds for typical topologies (100 queues, 50 exchanges)

**Prerequisites:** Epic 3 complete (topology operations)

**Technical Notes:**
- Export logic: query RabbitMQ API for all resources, serialize to YAML/JSON
- YAML structure:
  ```yaml
  vhost: /
  queues:
    - name: orders
      durable: true
      arguments:
        x-message-ttl: 60000
  exchanges:
    - name: events
      type: topic
      durable: true
  bindings:
    - source: events
      destination: orders
      routing_key: "order.*"
  ```
- Use ruamel.yaml or PyYAML for YAML serialization
- Exclude: default exchange (""), system exchanges (amq.*), internal metadata
- Validation: schema validation for exported config

---

## Story 11.2: Import Topology from YAML/JSON

As a DevOps engineer,
I want to import topology from YAML/JSON file to create or update RabbitMQ configuration,
So that I can provision new environments or apply configuration changes declaratively.

**Acceptance Criteria:**

**Given** topology configuration file (YAML or JSON)
**When** I run import command: rabbitmq-mcp-server config import --file=topology.yaml --vhost=/
**Then** topology is created/updated on RabbitMQ server

**And** import is idempotent: running multiple times produces same result (no errors for existing resources with matching config)

**And** import validates configuration before applying: schema validation, dependency checks (exchanges exist before bindings)

**And** import supports modes: --create-only (fail if exists), --update-only (fail if doesn't exist), --upsert (create or update, default)

**And** import is transactional: all changes applied or none (rollback on any failure)

**And** dry-run mode: --dry-run shows what would change without applying

**And** import reports: created (count), updated (count), unchanged (count), failed (list with errors)

**And** import completes in <30 seconds for 100 resources

**Prerequisites:** Story 11.1 (export topology), Epic 3 complete (topology operations)

**Technical Notes:**
- Import logic: parse YAML/JSON, validate schema, apply changes via MCP tools
- Order of operations: create exchanges first, then queues, then bindings (resolve dependencies)
- Idempotency: check if resource exists with GET, compare properties, create if missing, update if different
- Transaction: collect all operations, execute in order, rollback on failure (delete created resources)
- Dry-run: execute validation and dependency checks, report changes, skip actual API calls
- Error handling: collect all errors, report at end (don't stop on first error)

---
