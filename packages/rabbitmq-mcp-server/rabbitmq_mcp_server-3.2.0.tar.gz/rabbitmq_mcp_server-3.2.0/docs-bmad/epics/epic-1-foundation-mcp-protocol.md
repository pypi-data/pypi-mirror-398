# Epic 1: Foundation & MCP Protocol

**Goal**: Establish the foundational MCP server architecture with OpenAPI-driven code generation pipeline and 3-tool semantic discovery pattern that enables natural language interaction with RabbitMQ operations.

**Value**: Provides the core infrastructure for all subsequent features - without this foundation, no RabbitMQ operations are possible through the MCP protocol. This epic delivers the **unlimited operations, zero overwhelm** product differentiator through semantic discovery architecture.

**Product Differentiator**: Implements the 3-tool semantic discovery pattern that solves MCP's tool explosion problem - exposing 100+ operations through just 3 tools with natural language search.

**Covered FRs**: FR-001, FR-002, FR-003, FR-004, FR-021

---

## Story 1.1: Project Setup & Repository Structure

As a developer,
I want the project repository initialized with modern Python project structure and dependency management,
So that all subsequent development follows consistent patterns and dependencies are properly managed.

**Acceptance Criteria:**

**Given** a fresh repository clone
**When** I run the initial setup commands
**Then** the project structure is created with all necessary directories (src/, tests/, scripts/, data/, config/, docs/, .bmad/)

**And** Python 3.12+ is configured with uv package manager for dependency management

**And** pyproject.toml includes all core dependencies: mcp>=1.0.0, pydantic>=2.0, sentence-transformers, httpx, pika, structlog, pytest, mypy, ruff

**And** pyproject.toml includes project metadata: name, version, description, authors, license, python version constraint (>=3.12,<4.0)

**And** .gitignore excludes: __pycache__/, .pytest_cache/, .mypy_cache/, *.pyc, .env, logs/, .venv/, data/*.json, data/*.yaml

**And** README.md includes: project overview, quick start, installation instructions, basic usage examples

**And** architecture initialization command is executed if using architecture template (see docs-bmad/architecture/project-initialization.md for reference)

**Prerequisites:** None (first story)

**Technical Notes:**
- Use uv for fast dependency resolution and reproducible builds: `uv init` and `uv add <package>`
- Repository structure follows src-layout pattern for clean imports and proper packaging
- Create empty __init__.py files in all Python package directories
- Document directory structure in README.md: src/ (application code), tests/ (test suites), scripts/ (build/generation scripts), data/ (generated artifacts), config/ (configuration files), docs/ (documentation)
- Set Python version constraint: >=3.12,<4.0 (Python 3.12 required for modern type hints)
- Reference architecture/project-initialization.md for any template-specific setup commands

---

## Story 1.2: Development Quality Tools & CI/CD Pipeline

As a developer,
I want pre-commit hooks and CI/CD pipeline configured for code quality enforcement,
So that code quality is maintained automatically and issues are caught early.

**Acceptance Criteria:**

**Given** the project repository is set up (Story 1.1)
**When** I commit code or push to GitHub
**Then** pre-commit hooks run automatically and validate: black formatting, isort import sorting, mypy type checking, ruff linting

**And** pre-commit hooks fail commit if any validation fails (must fix before committing)

**And** pre-commit configuration file (.pre-commit-config.yaml) defines all hooks with versions

**And** GitHub Actions CI/CD pipeline (.github/workflows/ci.yml) runs on pull requests and validates: all tests pass (pytest), linting passes (ruff), type checking passes (mypy --strict), code coverage >80%

**And** CI/CD pipeline fails if any validation fails (prevents merging broken code)

**And** CI/CD pipeline runs on: Python 3.12 and Python 3.13 (multi-version testing)

**Prerequisites:** Story 1.1 (project setup)

**Technical Notes:**
- Install pre-commit: `uv add --dev pre-commit` and `pre-commit install`
- Configure hooks in .pre-commit-config.yaml: black (formatting), isort (imports), mypy (types), ruff (linting)
- Enable strict mypy configuration: disallow_untyped_defs=true, warn_return_any=true, strict_optional=true
- Use ruff for fast linting (replaces flake8, pylint, isort partially): configure via pyproject.toml [tool.ruff]
- GitHub Actions workflow: checkout code, setup Python with uv, install dependencies, run tests with coverage, upload coverage to Codecov
- CI/CD caching: cache uv dependencies and pip packages for faster runs

---

## Story 1.3: OpenAPI Specification Integration

As a developer,
I want the RabbitMQ Management API OpenAPI specification as the single source of truth,
So that all schemas, operations, and documentation derive from one authoritative source.

**Acceptance Criteria:**

**Given** the OpenAPI specification file at `docs-bmad/rabbitmq-http-api-openapi.yaml`
**When** I validate the OpenAPI file
**Then** it passes OpenAPI 3.0 schema validation with zero errors

**And** the specification contains 100+ operation definitions in paths section

**And** the specification contains complete component schemas for request/response bodies

**And** all operations have unique operationId values following format: `{namespace}.{resource}.{action}`

**And** each operation has description, parameters, requestBody (if applicable), and responses defined

**And** validation script `scripts/validate_openapi.py` confirms specification integrity

**Prerequisites:** Story 1.1 (project setup)

**Technical Notes:**
- OpenAPI file is ~4800 lines defining RabbitMQ Management API
- Store in docs-bmad/ folder (not .specify/memory/ to avoid hidden directory issues)
- Use openapi-spec-validator library for validation
- Document any deviations from official RabbitMQ API in comments
- Validation runs as part of CI/CD pipeline (Story 1.2)

---

## Story 1.4: Pydantic Schema Generation

As a developer,
I want Pydantic models automatically generated from OpenAPI component schemas,
So that all request/response validation is type-safe and synchronized with the API specification.

**Acceptance Criteria:**

**Given** the OpenAPI specification with component schemas
**When** I run `python scripts/generate_schemas.py`
**Then** Pydantic models are generated in `src/schemas/generated_schemas.py`

**And** each OpenAPI schema component has a corresponding Pydantic BaseModel class

**And** field types are correctly mapped: string→str, integer→int, boolean→bool, array→List, object→Dict or nested model

**And** required fields are enforced with Pydantic Field() validators

**And** optional fields use Optional[T] type hints

**And** field descriptions from OpenAPI become docstrings in Pydantic models

**And** generated code passes mypy type checking with zero errors

**And** generation script detects OpenAPI changes and prompts regeneration

**Prerequisites:** Story 1.3 (OpenAPI specification)

**Technical Notes:**
- Use datamodel-code-generator library for OpenAPI→Pydantic conversion
- Generated file includes header comment: "Auto-generated from OpenAPI - DO NOT EDIT MANUALLY"
- Custom field validators added for RabbitMQ-specific constraints (e.g., queue name format)
- Generation is idempotent (running twice produces identical output)
- Include timestamp in generated file header for change tracking

---

## Story 1.5: Operation Registry Generation

As a developer,
I want a JSON registry mapping operation IDs to HTTP methods, paths, parameters, and documentation,
So that the MCP server can dynamically execute any RabbitMQ Management API operation.

**Acceptance Criteria:**

**Given** the OpenAPI specification with path definitions
**When** I run `python scripts/extract_operations.py`
**Then** operation registry is created at `data/operations.json`

**And** each operation entry contains: operation_id, namespace, http_method, url_path, description, parameters, request_schema, response_schema, examples, tags, requires_auth

**And** URL paths include parameter placeholders (e.g., `/api/queues/{vhost}/{name}`)

**And** parameters include: name, location (path/query/header), type, required, description, schema

**And** all 100+ operations from OpenAPI are represented in the registry

**And** registry file is <5MB for fast loading

**And** operation lookups by ID complete in <1ms (validated via benchmark)

**Prerequisites:** Story 1.3 (OpenAPI specification)

**Technical Notes:**
- Registry is a JSON file (not database) for portability
- Include operation metadata: deprecated flag, rate_limit_exempt, safety_validation_required
- Manually add AMQP operations (publish, consume, ack, nack, reject) since they're not in Management API OpenAPI
- Script validates no duplicate operation IDs
- CI/CD validates registry synchronization with OpenAPI

---

## Story 1.6: Semantic Embeddings Generation

As a developer,
I want pre-computed vector embeddings for all operation descriptions,
So that semantic search queries return relevant operations in <100ms without runtime computation overhead.

**Acceptance Criteria:**

**Given** the operation registry with operation descriptions
**When** I run `python scripts/generate_embeddings.py`
**Then** embeddings are generated at `data/embeddings.json`

**And** embeddings use sentence-transformers model `all-MiniLM-L6-v2` (384 dimensions)

**And** each operation has a corresponding embedding vector

**And** embeddings file is <50MB for reasonable distribution size

**And** embeddings load into memory in <500ms on reference hardware

**And** cosine similarity calculations between query and all embeddings complete in <50ms

**And** model downloads automatically on first run and caches locally

**Prerequisites:** Story 1.5 (operation registry)

**Technical Notes:**
- Use sentence-transformers library with all-MiniLM-L6-v2 (fast, good quality)
- Store embeddings as JSON array of floats for portability
- Include metadata: model_name, model_version, embedding_dimension, generation_timestamp
- Consider compression (gzip) if file size exceeds 50MB
- Document model choice rationale (speed vs quality tradeoff)
- GPU acceleration optional but not required

---

## Story 1.7: MCP Server Foundation (JSON-RPC 2.0)

As an AI assistant,
I want to connect to the MCP server via stdio transport using JSON-RPC 2.0 protocol,
So that I can discover and execute RabbitMQ operations through the Model Context Protocol.

**Acceptance Criteria:**

**Given** the MCP server is started
**When** I send a JSON-RPC 2.0 request to the stdio interface
**Then** the server responds with valid JSON-RPC 2.0 formatted response

**And** server implements MCP protocol methods: initialize, tools/list, tools/call

**And** initialize method returns server capabilities: name="rabbitmq-mcp-server", version, protocol_version="2024-11-05"

**And** tools/list returns exactly 3 tools: search-ids, get-id, call-id

**And** each tool definition includes: name, description, input_schema (JSON Schema format)

**And** invalid requests return JSON-RPC error codes: -32700 (parse error), -32600 (invalid request), -32601 (method not found), -32602 (invalid params)

**And** server startup completes in <1 second

**Prerequisites:** Story 1.1 (project setup), Story 1.6 (embeddings generation)

**Technical Notes:**
- Use mcp library for MCP protocol implementation
- Stdio transport reads from stdin, writes to stdout (stderr for logs)
- JSON-RPC request format: {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
- Async/await architecture for concurrent request handling
- Graceful shutdown on SIGTERM/SIGINT
- Health check via MCP ping/pong if supported

---

## Story 1.8: `search-ids` Tool Implementation

As an AI assistant,
I want to search for RabbitMQ operations using natural language queries,
So that I can discover relevant operations without knowing exact API endpoint names.

**Acceptance Criteria:**

**Given** the MCP server is connected with pre-loaded embeddings
**When** I call `search-ids` with query "list all queues"
**Then** I receive ranked list of relevant operation IDs with similarity scores

**And** results include operations like: "queues.list", "queues.list_by_vhost" with scores ≥0.7

**And** each result contains: operation_id, description, similarity_score, namespace

**And** results are ordered by similarity score descending (highest first)

**And** queries with no matches (all scores <0.7) return empty list with suggestion: "Try broader terms or check spelling"

**And** search completes in <100ms (p95 latency)

**And** query embedding generation is cached for repeated queries

**And** the tool accepts parameters: query (string, required), threshold (float, optional, default 0.7), max_results (int, optional, default 10)

**Prerequisites:** Story 1.6 (embeddings), Story 1.7 (MCP server foundation)

**Technical Notes:**
- Compute query embedding using same model as operation embeddings
- Cosine similarity calculation: dot(query_vec, op_vec) / (norm(query_vec) * norm(op_vec))
- Use numpy for vectorized similarity calculations (fast)
- Cache query embeddings with LRU cache (max 100 queries)
- Consider approximate nearest neighbor (ANN) if performance degrades with 500+ operations
- Log search queries and top results for analytics (enables innovation validation experiments)

---

## Story 1.9: `get-id` Tool Implementation

As an AI assistant,
I want to retrieve complete documentation and parameter schemas for a specific operation,
So that I understand how to use the operation before calling it.

**Acceptance Criteria:**

**Given** the MCP server with loaded operation registry
**When** I call `get-id` with operation_id "queues.list"
**Then** I receive complete operation details including: operation_id, description, http_method, url_path, parameters (with types and descriptions), request_schema, response_schema, examples

**And** parameter details include: name, type, required, location (path/query/header), description, default value, constraints (min/max, pattern, enum)

**And** response schema describes expected return structure

**And** examples (if available) show sample requests and responses

**And** retrieval completes in <50ms

**And** invalid operation IDs return error: "Operation '{id}' not found. Use search-ids to discover operations."

**And** response includes usage hints: "This operation requires authentication" or "This operation modifies resources"

**Prerequisites:** Story 1.5 (operation registry), Story 1.7 (MCP server foundation)

**Technical Notes:**
- Load operations.json into memory at server startup for fast lookup
- Use dict with operation_id as key for O(1) lookups
- Include metadata: deprecated warnings, rate limit exemptions, safety validation requirements
- Cache responses (immutable data)
- Format output for readability (pretty-printed JSON)
- Include link to RabbitMQ Management API docs if available

---

## Story 1.10: `call-id` Tool Implementation (HTTP Operations)

As an AI assistant,
I want to execute RabbitMQ Management API operations with validated parameters,
So that I can perform actual management tasks on RabbitMQ infrastructure.

**Acceptance Criteria:**

**Given** the MCP server with RabbitMQ connection configured
**When** I call `call-id` with operation_id "queues.list" and vhost="/"
**Then** the operation executes HTTP request to RabbitMQ Management API

**And** parameters are validated against Pydantic schema before HTTP call

**And** validation errors list specific missing/invalid fields: "Parameter 'vhost' is required" or "Parameter 'max_messages' must be integer ≥1"

**And** successful operations return: status="success", result={...operation response...}

**And** HTTP errors return: status="error", error_code, error_message

**And** operations complete in <200ms under normal conditions (p95)

**And** operations exceeding 30-second timeout are aborted with error: "Operation timed out after 30s"

**And** connection failures return immediately without retry: "Failed to connect to RabbitMQ at {host}:{port}"

**Prerequisites:** Story 1.4 (Pydantic schemas), Story 1.5 (operation registry), Story 1.7 (MCP server foundation)

**Technical Notes:**
- Use httpx library for HTTP client (async support)
- HTTP Basic Auth with configured username/password
- TLS/SSL support with certificate verification (configurable via --insecure flag)
- URL construction from template: replace {vhost}, {name}, etc. with actual values
- Request timeout: 30 seconds (configurable)
- No automatic retries (fail-fast pattern)
- Log all operation executions with correlation IDs for audit trail

---

## Story 1.11: Multi-Version API Support

As a developer,
I want to support multiple RabbitMQ Management API versions (3.11.x, 3.12.x, 3.13.x),
So that users can work with different RabbitMQ installations without compatibility issues.

**Acceptance Criteria:**

**Given** environment variable `RABBITMQ_API_VERSION` is set to "3.12"
**When** the server starts
**Then** it loads the corresponding OpenAPI specification from `data/openapi-3.12.yaml`

**And** all generated artifacts (schemas, operations, embeddings) use the 3.12 version

**And** unsupported versions return error: "API version '3.10' not supported. Supported: 3.11, 3.12, 3.13"

**And** default version (if env var not set) is 3.13 (latest)

**And** version is displayed in server info: "RabbitMQ MCP Server v1.0.0 (API: 3.12.x)"

**And** version switching requires server restart (not runtime reload)

**Prerequisites:** Story 1.3 (OpenAPI specification), Story 1.7 (MCP server foundation)

**Technical Notes:**
- Store OpenAPI specs in data/ folder: openapi-3.11.yaml, openapi-3.12.yaml, openapi-3.13.yaml
- Generation scripts accept --api-version parameter
- Default to 3.13 for latest features
- Document version differences in CHANGELOG.md
- CI/CD tests all supported versions
- Consider deprecation warnings for old versions

---
