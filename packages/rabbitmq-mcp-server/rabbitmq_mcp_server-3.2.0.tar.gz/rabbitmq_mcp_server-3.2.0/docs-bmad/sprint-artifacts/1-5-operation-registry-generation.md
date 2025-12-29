# Story 1.5: Operation Registry Generation

Status: done

## Story

As a developer,
I want a JSON registry mapping operation IDs to HTTP methods, paths, parameters, and documentation,
so that the MCP server can dynamically execute any RabbitMQ Management API operation.

## Acceptance Criteria

1. **Registry Generation Script Exists**
   - Script exists at `scripts/extract_operations.py`
   - Script is executable via `uv run python scripts/extract_operations.py`
   - Script accepts CLI arguments: `--spec-path` (OpenAPI file), `--output-path` (registry JSON), `--include-amqp` (flag)
   - Default paths: spec=`docs-bmad/rabbitmq-http-api-openapi.yaml`, output=`data/operations.json`

2. **Operation Registry Created**
   - Running script creates `data/operations.json` with complete operation metadata
   - Each operation entry contains: operation_id, namespace, http_method, url_path, description, parameters, request_schema, response_schema, examples, tags, requires_auth
   - URL paths include parameter placeholders (e.g., `/api/queues/{vhost}/{name}`)
   - All 100+ operations from OpenAPI are represented in the registry

3. **Parameter Metadata Complete**
   - Parameters include: name, location (path/query/header/body), type, required, description, schema
   - Location correctly identifies: path parameters in URL, query parameters, header parameters
   - Type mapping: string, integer, number, boolean, array, object
   - Required flag accurately reflects OpenAPI required arrays per path/operation

4. **Registry File Size and Performance**
   - Registry file is <5MB for fast loading and distribution
   - Registry structure enables O(1) lookups by operation_id (dict with operation_id as key)
   - Operation lookups complete in <1ms (validated via benchmark test)
   - File loads into memory in <100ms on reference hardware

5. **AMQP Operations Included**
   - Manually added AMQP operations (not in Management API OpenAPI): publish, consume, ack, nack, reject
   - AMQP operations follow same structure as HTTP operations
   - AMQP operations marked with `protocol: "amqp"` field (HTTP operations have `protocol: "http"`)
   - AMQP operations have complete parameter schemas for message properties and routing

6. **Registry Validation**
   - Script validates no duplicate operation IDs (exit with error if duplicates found)
   - All operation IDs follow format: `{namespace}.{action}` or `{namespace}.{resource}.{action}`
   - Namespaces are consistent: queues, exchanges, bindings, messages, connections, users, permissions, nodes, cluster, amqp
   - CI/CD validates registry synchronization with OpenAPI (fail if operations missing)

7. **Operation Metadata Enrichment**
   - Include operation metadata: deprecated (bool), rate_limit_exempt (bool), safety_validation_required (bool)
   - Deprecated operations marked from OpenAPI deprecated flag
   - Safety validation required for destructive operations: delete, purge, reset
   - Rate limit exempt for health checks and monitoring operations

## Tasks / Subtasks

- [x] **Task 1: Create Operation Extraction Script** (AC: #1, #2)
  - [x] Create `scripts/extract_operations.py` file with CLI argument parsing (argparse)
  - [x] Load OpenAPI YAML file using PyYAML (already in dependencies)
  - [x] Parse paths section to extract all operations with GET/POST/PUT/DELETE/PATCH methods
  - [x] Extract operation metadata: operationId, summary/description, parameters, requestBody, responses, tags, deprecated
  - [x] Build operation_id from operationId field (format: namespace.action)
  - [x] Determine namespace from tags or path structure (first path segment after /api/)
  - [x] Create data/ directory if it doesn't exist
  - [x] Write operations list to JSON file with pretty formatting (indent=2)
  - [x] Log extraction summary: number of operations extracted, output file path

- [x] **Task 2: Extract HTTP Method and URL Path** (AC: #2, #3)
  - [x] For each path in OpenAPI paths section, iterate over HTTP methods (get, post, put, delete, patch)
  - [x] Store http_method in uppercase (GET, POST, PUT, DELETE, PATCH)
  - [x] Store url_path exactly as in OpenAPI (with parameter placeholders: {vhost}, {name}, etc.)
  - [x] Validate URL paths have consistent parameter naming across operations
  - [x] Test with sample operations: GET /api/queues/{vhost}, POST /api/queues/{vhost}/{name}

- [x] **Task 3: Extract Parameter Metadata** (AC: #3)
  - [x] Parse parameters array from OpenAPI operation definition
  - [x] For each parameter extract: name, in (location), schema.type, required, description
  - [x] Map OpenAPI `in` field to location: path, query, header, cookie (ignore cookie for RabbitMQ)
  - [x] Store parameter type from schema.type (string, integer, number, boolean, array, object)
  - [x] Handle array types: extract items.type for element type
  - [x] Handle object types: store full schema structure
  - [x] Extract default values if present in schema.default
  - [x] Extract constraints: minimum, maximum, minLength, maxLength, pattern, enum
  - [x] Test with operations having path parameters, query parameters, and mixed combinations

- [x] **Task 4: Extract Request and Response Schemas** (AC: #2)
  - [x] For operations with requestBody, extract schema reference or inline schema
  - [x] Store request_schema as schema name (e.g., "QueueCreateRequest") or inline schema structure
  - [x] For responses (200, 201 success codes), extract response schema reference
  - [x] Store response_schema as schema name (e.g., "QueueInfoResponse") or inline structure
  - [x] Handle operations with no request body (null request_schema)
  - [x] Handle operations with no response body (null response_schema)
  - [x] Test with operations having both request/response vs operations with only one or neither

- [x] **Task 5: Add AMQP Operations Manually** (AC: #5)
  - [x] Define AMQP operations structure in script as Python dicts
  - [x] Add publish operation: namespace="amqp", operation_id="amqp.publish", parameters for exchange, routing_key, message, properties
  - [x] Add consume operation: namespace="amqp", operation_id="amqp.consume", parameters for queue, consumer_tag, auto_ack, callback
  - [x] Add ack operation: namespace="amqp", operation_id="amqp.ack", parameters for delivery_tag, multiple
  - [x] Add nack operation: namespace="amqp", operation_id="amqp.nack", parameters for delivery_tag, multiple, requeue
  - [x] Add reject operation: namespace="amqp", operation_id="amqp.reject", parameters for delivery_tag, requeue
  - [x] Mark all AMQP operations with protocol="amqp" field (vs protocol="http" for Management API)
  - [x] Add message properties schema: content_type, delivery_mode, priority, correlation_id, reply_to, expiration, etc.
  - [x] Only include AMQP operations if --include-amqp flag is set (default: true)

- [x] **Task 6: Enrich with Operation Metadata** (AC: #7)
  - [x] Add deprecated field: read from OpenAPI deprecated flag, default false
  - [x] Add rate_limit_exempt field: true for specific operations (overview, health, aliveness)
  - [x] Add safety_validation_required field: true for destructive operations
  - [x] Identify destructive operations by method (DELETE) and path patterns (delete, purge, reset in operationId)
  - [x] Add requires_auth field: default true, false only for public health checks
  - [x] Test metadata flags are correctly assigned to sample operations

- [x] **Task 7: Implement Registry Validation** (AC: #6)
  - [x] Check for duplicate operation IDs: collect all IDs, verify set length equals list length
  - [x] If duplicates found, log error with duplicate IDs and exit with code 1
  - [x] Validate operation_id format: must match pattern `^[a-z_]+\.[a-z_]+(\.[a-z_]+)?(_\d+)?$`
  - [x] Validate namespace consistency: namespace value must match first part of operation_id
  - [x] Validate all namespaces are in allowed list: queues, exchanges, bindings, messages, connections, users, permissions, nodes, cluster, amqp
  - [x] Log validation summary: total operations, unique namespaces, any warnings

- [x] **Task 8: Optimize Registry Structure for Lookups** (AC: #4)
  - [x] Store operations as JSON object (dict) with operation_id as key (not array)
  - [x] Structure: `{ "queues.list": {...}, "queues.create": {...}, ... }`
  - [x] Enables O(1) lookup in Python: `registry[operation_id]`
  - [x] Include metadata in root: model_version, generated_at (ISO timestamp), openapi_source, total_operations
  - [x] Pretty-print JSON with indent=2 for human readability
  - [x] Verify file size <5MB (log warning if exceeds, but don't fail)

- [x] **Task 9: Create Unit Tests for Extraction Script** (AC: #2, #3, #4, #6, #7)
  - [x] Create `tests/unit/test_extract_operations.py`
  - [x] Test: Script extracts correct number of operations from sample OpenAPI (use fixture with 10 operations)
  - [x] Test: Operation entries have all required fields (operation_id, namespace, http_method, url_path, description, etc.)
  - [x] Test: Parameter metadata correctly extracted (name, location, type, required, description)
  - [x] Test: URL paths preserve parameter placeholders
  - [x] Test: Duplicate operation IDs cause validation error
  - [x] Test: Invalid operation_id format causes validation error
  - [x] Test: AMQP operations included when --include-amqp=true
  - [x] Test: AMQP operations excluded when --include-amqp=false
  - [x] Test: Registry structure is dict (not list) with operation_id keys
  - [x] Test: Deprecated operations marked correctly from OpenAPI
  - [x] Test: Safety validation required for DELETE operations
  - [x] Run tests: `uv run pytest tests/unit/test_extract_operations.py -v`

- [x] **Task 10: Create Performance Benchmark Tests** (AC: #4)
  - [x] Create `tests/performance/test_operations_registry.py`
  - [x] Benchmark: Registry file load time (should be <100ms)
  - [x] Benchmark: Operation lookup by ID (should be <1ms using pytest-benchmark)
  - [x] Test with full registry (100+ operations) not sample
  - [x] Use pytest-benchmark for statistical measurement (n=100 runs)
  - [x] Assert p95 latency meets targets or fail test
  - [x] Log benchmark results: min, mean, max, p95, p99 for load and lookup

- [x] **Task 11: Integrate into CI/CD Pipeline** (AC: #6)
  - [x] Update `.github/workflows/ci.yml` to add operation registry validation
  - [x] Add step after schema generation validation: "Validate Operation Registry"
  - [x] Run command: `uv run python scripts/extract_operations.py --spec-path docs-bmad/rabbitmq-http-api-openapi.yaml`
  - [x] Validate generated registry with custom validation script: check operation count matches expected
  - [x] Ensure failures block CI pipeline
  - [x] Test CI integration by pushing changes

- [x] **Task 12: Document Registry Structure and Usage** (AC: #1, #2)
  - [x] Update README.md with "Operation Registry" section
  - [x] Document script usage: `uv run python scripts/extract_operations.py`
  - [x] Document CLI arguments: --spec-path, --output-path, --include-amqp
  - [x] Document registry JSON structure with example operation entry
  - [x] Document how to look up operations: load JSON, access by operation_id key
  - [x] Document AMQP vs HTTP operations distinction (protocol field)
  - [x] Note registry file location: `data/operations.json`
  - [x] Document when to regenerate: after OpenAPI changes (similar to schema generation)

## Dev Notes

### Learnings from Previous Story

**From Story 1-4-pydantic-schema-generation (Status: done)**

**Files Created:**
- `scripts/generate_schemas.py` - Schema generation script structure can be reused for operations extraction script
- `src/schemas/generated_schemas.py` - Generated Pydantic models available for request/response schema references in registry
- `tests/unit/test_generate_schemas.py` - Test patterns for generation scripts established

**Completion Notes from Previous Story:**
- Generation script pattern established: argparse CLI, file I/O, validation, change detection
- OpenAPI file at `docs-bmad/rabbitmq-http-api-openapi.yaml` validated and ready to use
- CI/CD pipeline pattern for validation steps: run generation script, validate output
- README.md documentation pattern for generation tools

**Services/Patterns Created to Reuse:**
- PyYAML for OpenAPI parsing (already in dependencies)
- datamodel-code-generator approach (not needed here, but validation patterns useful)
- CLI structure with argparse: --spec-path, --output-path, --force flags
- Change detection with file modification timestamps
- Black formatting after generation
- mypy validation as quality gate
- Comprehensive unit test coverage with pytest

**Architectural Consistency:**
- Build-time generation pattern (ADR-007): operations extracted at build time, not runtime
- OpenAPI as single source of truth (ADR-001): registry derives from OpenAPI specification
- Type safety requirements: registry structure should be validated with Pydantic model if possible
- JSON-based storage for portability (no database required for MVP)

**CI/CD Infrastructure Ready:**
- GitHub Actions workflow structure established for validation steps
- Quality gates enforce zero failures before merge
- Multi-version Python testing (3.12, 3.13) already configured

**Files to Reuse (Do NOT Recreate):**
- `.github/workflows/ci.yml`: Add operation registry validation step after schema generation
- `README.md`: Add Operation Registry section after Schema Generation section
- `docs-bmad/rabbitmq-http-api-openapi.yaml`: Input OpenAPI specification (do not modify)

**Technical Debt/Issues from Previous Story:**
- None affecting this story - all deliverables completed successfully

[Source: docs-bmad/sprint-artifacts/1-4-pydantic-schema-generation.md#Dev-Agent-Record]

### Architecture Patterns and Constraints

**OpenAPI-Driven Code Generation (ADR-001):**
- OpenAPI specification is single source of truth for operation definitions [Source: docs-bmad/architecture/architecture-decision-records-adrs.md - ADR-001]
- Operation registry extracted at build time from OpenAPI paths section [Source: docs-bmad/architecture/architecture-decision-records-adrs.md - ADR-007]
- Registry used by MCP tools: search-ids (semantic search), get-id (operation docs), call-id (execution) [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "3-Tool Semantic Discovery Pattern"]
- Any changes to operations start with OpenAPI update, then regenerate registry [Source: docs-bmad/architecture/architecture-decision-records-adrs.md - ADR-001]

**Data Architecture Constraints:**
- Operation registry stored as JSON file (not database) for portability [Source: docs-bmad/architecture/data-architecture.md - "Data Storage Strategy"]
- Registry structure: dict with operation_id as key for O(1) lookups [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Operation Registry Entry"]
- File size target: <5MB for fast distribution and loading [Source: docs-bmad/epics/epic-1-foundation-mcp-protocol.md - Story 1.5 AC]
- Registry loaded into memory at server startup (immutable at runtime) [Source: docs-bmad/architecture/data-architecture.md - "Runtime Data"]

**Operation Metadata Requirements:**
- operation_id format: `{namespace}.{action}` following OpenAPI operationId [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Operation Registry Entry"]
- Namespace consistency: queues, exchanges, bindings, messages, connections, users, permissions, nodes, cluster, amqp [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Data Models and Contracts"]
- URL paths preserve parameter placeholders: `/api/queues/{vhost}/{name}` [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Operation Registry Entry"]
- Parameters categorized by location: path, query, header, body [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "APIs and Interfaces"]

**Performance Requirements:**
- Operation lookup: <1ms at p95 (O(1) dict access) [Source: docs-bmad/epics/epic-1-foundation-mcp-protocol.md - Story 1.5 AC]
- Registry file load: <100ms on reference hardware [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Performance"]
- Registry generation: <5 seconds for full OpenAPI (100+ operations) [Source: Tech Spec - reasonable expectation]

**AMQP Operations (Manual Addition):**
- AMQP operations not in Management API OpenAPI specification [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "In Scope"]
- Manually add: publish, consume, ack, nack, reject operations [Source: docs-bmad/epics/epic-1-foundation-mcp-protocol.md - Story 1.5 Technical Notes]
- Mark with protocol="amqp" to distinguish from protocol="http" [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Operation Registry Entry"]
- Full parameter schemas for message properties and routing [Source: docs-bmad/architecture/data-architecture.md - "Message Model"]

### Source Tree Components to Touch

**Files to Create:**
```
/
├── scripts/
│   └── extract_operations.py (operation extraction script with CLI)
├── data/
│   └── operations.json (auto-generated operation registry)
└── tests/
    ├── unit/
    │   └── test_extract_operations.py (unit tests for extraction)
    └── performance/
        └── test_operations_registry.py (performance benchmarks)
```

**Files to Modify:**
```
/
├── .github/
│   └── workflows/
│       └── ci.yml (add operation registry validation step)
└── README.md (add Operation Registry section)
```

**Files to Reference (Input):**
```
/
├── docs-bmad/
│   └── rabbitmq-http-api-openapi.yaml (input OpenAPI specification)
└── src/
    └── schemas/
        └── generated_schemas.py (Pydantic models for schema references)
```

### Project Structure Notes

[Source: docs-bmad/architecture/project-structure.md]

**Operation Registry Location:**
- Registry file at `data/operations.json` per project structure [Source: docs-bmad/architecture/project-structure.md]
- data/ directory contains build-time generated artifacts [Source: docs-bmad/architecture/project-structure.md]
- Registry committed to git for version control and distribution [Source: docs-bmad/architecture/data-architecture.md - "Build-Time Artifacts"]

**Extraction Script Location:**
- Script in `scripts/` directory alongside generate_schemas.py and validate_openapi.py [Source: docs-bmad/architecture/project-structure.md]
- Scripts directory contains build-time generation tools (not runtime code) [Source: docs-bmad/architecture/project-structure.md]
- Extraction script runs during development and optionally in CI for validation [Source: docs-bmad/architecture/project-structure.md]

**Build-Time vs Runtime:**
- Operation registry generated at build time (not runtime) for performance [Source: docs-bmad/architecture/architecture-decision-records-adrs.md - ADR-007]
- Registry loaded into memory at server startup for fast O(1) lookups [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Server Startup Sequence"]
- Registry is immutable at runtime (no updates during server execution) [Source: docs-bmad/architecture/data-architecture.md - "Runtime Data"]

### Testing Standards Summary

[Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Test Strategy Summary"]

**Testing Framework:**
- pytest framework with fixtures for test data isolation [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Test Strategy"]
- Test fixtures in tests/fixtures/ directory for sample OpenAPI files
- pytest-benchmark for performance testing with statistical analysis [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Performance Tests"]
- Follow test coverage requirements: >95% for critical path components [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Quality Standards"]

**Unit Tests for Extraction Script:**
- Test script execution with valid OpenAPI produces operations.json file
- Test operation entries have all required fields: operation_id, namespace, http_method, url_path, description, parameters
- Test parameter metadata completeness: name, location, type, required, description
- Test URL paths preserve parameter placeholders: {vhost}, {name}
- Test duplicate operation IDs cause validation error
- Test invalid operation_id format causes validation error
- Test AMQP operations included/excluded based on --include-amqp flag
- Test registry structure is dict with operation_id keys (not array)
- Test deprecated operations marked from OpenAPI deprecated flag
- Test safety validation required for DELETE operations
- Test file size <5MB validation (warn but don't fail)
- Coverage target: >95% for extraction script (critical path for operation discovery)

**Performance Benchmark Tests:**
- Benchmark registry file load time: target <100ms
- Benchmark operation lookup by ID: target <1ms at p95
- Use pytest-benchmark with n=100 runs for statistical confidence
- Test with full registry (100+ operations) not sample
- Report p50, p95, p99 latencies with pass/fail thresholds
- Performance tests run in CI to catch regressions

**Integration Tests Not Required:**
- Operation registry extraction is standalone (no external services)
- Unit tests with fixture OpenAPI schemas sufficient for coverage
- Registry will be tested indirectly in Story 1.9 (get-id tool uses registry for lookups)

**Code Quality Standards:**
- Extraction script must pass all pre-commit hooks (black, isort, mypy, ruff) [Source: docs-bmad/sprint-artifacts/1-2-development-quality-tools-cicd-pipeline.md]
- Generated registry formatted with pretty JSON (indent=2) for human readability
- Follow naming conventions: snake_case for fields, operation_id format enforced [Source: docs-bmad/architecture/implementation-patterns.md - "Naming Conventions"]
- Code style: Black formatting, isort import ordering, ruff linting [Source: docs-bmad/sprint-artifacts/1-2-development-quality-tools-cicd-pipeline.md]
- Type checking: mypy --strict with zero errors [Source: docs-bmad/architecture/technology-stack-details.md - "Type Checking"]

### References

**Architecture Documents:**
- [Source: docs-bmad/architecture/architecture-decision-records-adrs.md - ADR-001] - OpenAPI-Driven Code Generation
- [Source: docs-bmad/architecture/architecture-decision-records-adrs.md - ADR-007] - Build-Time vs Runtime Generation
- [Source: docs-bmad/architecture/data-architecture.md - "Data Storage Strategy"] - JSON file storage for registry
- [Source: docs-bmad/architecture/data-architecture.md - "Operation Registry Model"] - Registry data model structure

**Epic and Story Context:**
- [Source: docs-bmad/epics/epic-1-foundation-mcp-protocol.md - Story 1.5] - Story definition with acceptance criteria
- [Source: docs-bmad/sprint-artifacts/tech-spec-epic-1.md - "Operation Registry Generation"] - Registry design and metadata
- [Source: docs-bmad/sprint-artifacts/1-4-pydantic-schema-generation.md] - Previous story providing patterns and infrastructure

**External Documentation:**
- OpenAPI 3.0 specification: https://swagger.io/specification/
- OpenAPI 3.0 paths object: https://swagger.io/specification/#paths-object
- OpenAPI 3.0 parameter object: https://swagger.io/specification/#parameter-object
- pytest-benchmark documentation: https://pytest-benchmark.readthedocs.io/

## Dev Agent Record

### Context Reference

- docs-bmad/sprint-artifacts/stories/1-5-operation-registry-generation.context.xml

### Agent Model Used

Claude 3.5 Sonnet (December 2025)

### Debug Log References

### Completion Notes

**Completed:** 2025-12-26
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

### Completion Notes List

**2025-12-26 - Story Implementation Complete**

✅ **All 12 tasks completed successfully:**

1. **Operation Extraction Script Created** (`scripts/extract_operations.py`)
   - Full CLI with argparse: --spec-path, --output-path, --include-amqp flags
   - Extracts 132 operations (127 HTTP + 5 AMQP) from OpenAPI specification
   - Complete parameter metadata extraction with constraints
   - Request/response schema references preserved
   - Passes mypy --strict with zero errors
   - Formatted with black, linted with ruff

2. **Operation Registry Generated** (`data/operations.json`)
   - 132 operations in O(1) dict structure with operation_id keys
   - File size: 119KB (well under 5MB target)
   - Complete metadata: operation_id, namespace, http_method, url_path, description, parameters, schemas, tags, requires_auth, protocol, deprecated, rate_limit_exempt, safety_validation_required
   - AMQP operations included with protocol="amqp" field
   - URL paths preserve parameter placeholders: `/api/queues/{vhost}/{name}`

3. **Comprehensive Testing** (42 tests, 100% passed)
   - 32 unit tests in `tests/unit/test_extract_operations.py`
   - 10 performance benchmark tests in `tests/performance/test_operations_registry.py`
   - Test coverage for all extraction functions, validation, and AMQP operations
   - Performance benchmarks exceeded targets:
     - Registry load time: ~0.47ms (target: <100ms) ✅
     - Operation lookup: ~0.055µs (target: <1ms) ✅
     - File size: 119KB (target: <5MB) ✅

4. **CI/CD Integration**
   - Added "Validate Operation Registry" step to `.github/workflows/ci.yml`
   - Validates registry generation and operation count (>=100)
   - Blocks CI pipeline on validation failures
   - Runs on Python 3.12 and 3.13

5. **Documentation**
   - Added comprehensive "Operation Registry" section to README.md
   - Documented script usage with CLI examples
   - Documented registry structure with JSON examples
   - Documented operation lookup patterns and usage
   - Documented AMQP vs HTTP protocol distinction
   - Documented when to regenerate registry

**Key Achievements:**
- ✅ All acceptance criteria satisfied
- ✅ Performance targets exceeded by 200x (load) and 18,000x (lookup)
- ✅ Type-safe implementation with mypy --strict
- ✅ Comprehensive test coverage (42 tests)
- ✅ CI/CD validation integrated
- ✅ Production-ready documentation

**Technical Highlights:**
- O(1) operation lookups enable sub-microsecond access
- Dict structure with operation_id keys optimized for performance
- Validation prevents duplicate operation IDs and enforces format consistency
- AMQP operations manually defined with complete message properties
- Metadata enrichment for deprecated, destructive, and rate-limit-exempt operations
- pytest-benchmark provides statistical confidence in performance claims

**No Issues or Blockers**

### File List

**Files Created:**
- `scripts/extract_operations.py` - Operation extraction script with CLI (600+ lines)
- `data/operations.json` - Generated operation registry (132 operations, 119KB)
- `tests/unit/test_extract_operations.py` - Unit tests for extraction script (32 tests)
- `tests/performance/test_operations_registry.py` - Performance benchmarks (10 tests)
- `tests/fixtures/sample_openapi.yaml` - Sample OpenAPI for unit tests

**Files Modified:**
- `.github/workflows/ci.yml` - Added operation registry validation step
- `README.md` - Added "Operation Registry" documentation section
- `pyproject.toml` - Added pytest-benchmark dev dependency
- `docs-bmad/sprint-artifacts/sprint-status.yaml` - Story status tracking

**Files Referenced (Input):**
- `docs-bmad/rabbitmq-http-api-openapi.yaml` - OpenAPI specification (input)
- `scripts/generate_schemas.py` - Pattern reference for generation scripts

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-26 | Bob (SM Agent) | Initial story draft created in YOLO mode |
| 2025-12-26 | Amelia (Dev Agent) | Completed all 12 tasks: Created extraction script, generated registry (132 operations), implemented comprehensive testing (42 tests), integrated CI/CD validation, documented usage |
