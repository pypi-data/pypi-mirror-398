# Architecture Decision Records (ADRs)

## ADR-001: OpenAPI-Driven Code Generation

**Context:** Need single source of truth for 100+ RabbitMQ Management API operations with type-safe validation.

**Decision:** Use OpenAPI specification as sole source of truth, generate Pydantic schemas and operation registry at build-time.

**Rationale:**
- Eliminates drift between documentation and implementation
- Type safety with zero runtime overhead
- Pre-computed artifacts enable <1s server startup
- One-time generation cost paid at build time, not runtime

**Consequences:**
- Manual regeneration required when OpenAPI changes (acceptable trade-off)
- Build step adds complexity but ensures consistency
- Generated code committed to version control for portability

**Alternatives Considered:**
- Runtime schema generation: Too slow, defeats performance goals
- Manual schema maintenance: Error-prone, guaranteed drift over time

## ADR-002: 3-Tool Semantic Discovery Pattern

**Context:** Exposing 100+ operations as individual MCP tools would overwhelm AI assistants and violate MCP best practices.

**Decision:** Implement semantic discovery with 3 tools: search-ids (discovery), get-id (documentation), call-id (execution).

**Rationale:**
- Natural language search via embeddings (<100ms)
- Unlimited operations without tool explosion
- Consistent interface regardless of RabbitMQ version
- AI assistants can discover operations without memorization

**Consequences:**
- Two-step process (search → call) vs. direct tool invocation
- Requires pre-computed embeddings (build-time dependency)
- Novel pattern; no existing MCP servers use this approach

**Alternatives Considered:**
- 100+ individual tools: Overwhelms AI context window
- Single generic "execute" tool: Loses type safety and validation
- Categories with sub-tools: Still too many tools (20+ categories)

## ADR-003: Dual Transport (Stdio + HTTP)

**Context:** Different deployment scenarios require different transport mechanisms.

**Decision:** Support both stdio (AI assistants) and Streamable HTTP (remote/browser clients) transports.

**Rationale:**
- Stdio: Standard for Claude Desktop and local AI assistants
- HTTP: Enables remote access, browser clients, multi-client scenarios
- FastMCP supports both with minimal code changes
- Runtime selection via CLI flag or config

**Consequences:**
- Additional configuration complexity for HTTP mode
- Security considerations for HTTP (auth, TLS, CORS)
- Testing requires covering both transports

**Alternatives Considered:**
- Stdio only: Limits use cases to local assistants
- HTTP only: Incompatible with Claude Desktop integration
- SSE transport: Deprecated in favor of Streamable HTTP

## ADR-004: JSON-Based Vector Storage (MVP)

**Context:** Need fast semantic search over 100+ operations with <100ms latency.

**Decision:** Use JSON file for embeddings in MVP, migrate to sqlite-vec in Phase 2 if needed.

**Rationale:**
- JSON simple, portable, no external dependencies
- 100-200 operations fit comfortably in memory (<5MB)
- Loading time <500ms acceptable for startup
- sqlite-vec overhead not justified for current scale

**Consequences:**
- Full load into memory at startup (acceptable for <5MB)
- No incremental updates (regenerate entire file)
- Migration path exists to sqlite-vec if scaling needed

**Alternatives Considered:**
- sqlite-vec immediately: Over-engineering for current scale
- PostgreSQL pgvector: Requires external database (too heavy)
- Elasticsearch: Massive overkill for 100 documents

## ADR-005: Stateless Server Design

**Context:** Need to support horizontal scaling for production deployments.

**Decision:** Stateless server design with no shared state between instances.

**Rationale:**
- Enables horizontal scaling with load balancer
- No session storage or distributed locking required
- Simplifies deployment and operations
- Connection pools managed per-instance

**Consequences:**
- HTTP sessions managed client-side (session ID in header)
- Each instance loads embeddings into memory (acceptable overhead)
- Rate limiting per-instance (acceptable for MVP)

**Alternatives Considered:**
- Stateful with Redis: Adds infrastructure complexity
- Session affinity: Complicates load balancing
- Shared cache: Not needed for immutable data

## ADR-006: Automatic Credential Sanitization

**Context:** Logs and error messages must never expose passwords or tokens.

**Decision:** 100% automatic sanitization via structlog processors, not optional or manual.

**Rationale:**
- Security by default, impossible to forget
- Regex patterns catch all common credential formats
- Applied before any log output or error response
- Zero-trust approach: assume credentials anywhere

**Consequences:**
- Slight performance overhead (<1ms per log entry)
- May over-sanitize in edge cases (acceptable)
- Requires comprehensive regex pattern library

**Alternatives Considered:**
- Manual sanitization: Too error-prone, guaranteed leaks
- Pydantic SecretStr only: Doesn't catch all cases
- Opt-in sanitization: Defeats security by default

## ADR-007: Build-Time vs Runtime Generation

**Context:** Code generation can happen at build-time or runtime.

**Decision:** All generation at build-time, commit artifacts to version control.

**Rationale:**
- Eliminates OpenAPI and model download from runtime dependencies
- Guarantees reproducible builds across environments
- Enables offline operation after initial setup
- Faster startup time (no generation delay)

**Consequences:**
- Generated files committed to Git (larger repo size)
- Manual regeneration when OpenAPI changes
- CI validates artifacts are synchronized

**Alternatives Considered:**
- Runtime generation: Slower startup, external dependencies at runtime
- Hybrid approach: Complexity without clear benefit

## ADR-008: Pydantic for All Validation

**Context:** Need type-safe validation for all inputs and outputs.

**Decision:** Use Pydantic exclusively for schema validation across entire codebase.

**Rationale:**
- Single validation framework reduces complexity
- OpenAPI → Pydantic generation well-supported
- Excellent IDE integration (type hints)
- JSON schema generation for MCP tools

**Consequences:**
- Pydantic V2 required (breaking changes from V1)
- All schemas must be Pydantic models
- Learning curve for contributors

**Alternatives Considered:**
- jsonschema library: No type hints, less IDE support
- dataclasses with manual validation: More code, error-prone
- Multiple validation libraries: Unnecessary complexity

## ADR-009: Structured Logging with structlog

**Context:** Logs must be machine-readable for aggregation and analysis.

**Decision:** JSON-structured logs via structlog with automatic context binding.

**Rationale:**
- Machine-readable for log aggregation systems
- Context binding (correlation IDs) automatic
- Processors enable sanitization and enrichment
- Industry standard for modern applications

**Consequences:**
- Different from stdlib logging (but compatible)
- JSON output less human-readable (use jq for viewing)
- Small performance overhead from JSON serialization

**Alternatives Considered:**
- stdlib logging: Less structured, harder to parse
- Custom logging: Reinventing the wheel
- Multiple logging backends: Unnecessary complexity

## ADR-010: pytest + testcontainers

**Context:** Integration tests need real RabbitMQ, not mocks.

**Decision:** Use pytest as test framework with testcontainers for RabbitMQ instances.

**Rationale:**
- Real RabbitMQ ensures integration tests are realistic
- testcontainers manages Docker lifecycle automatically
- Per-test vhost isolation enables parallel testing
- pytest fixtures provide clean setup/teardown

**Consequences:**
- Requires Docker for integration tests
- Slower than mocked tests (acceptable trade-off)
- CI must support Docker (GitHub Actions does)

**Alternatives Considered:**
- Mocked RabbitMQ: Not realistic enough
- Shared RabbitMQ instance: Test isolation problems
- Manual Docker management: Error-prone, cleanup issues

---
