# Epic 6: Testing & Quality Framework

**Goal**: Implement comprehensive testing strategy with unit, integration, contract, and performance tests achieving 80%+ code coverage and validating all critical functionality.

**Value**: Ensures production-ready quality, catches regressions early, validates MCP protocol compliance, and provides confidence for continuous deployment. Delivers **enterprise-grade quality assurance** from MVP.

**Product Differentiator**: 80%+ test coverage from day 1 - contract tests ensure MCP protocol compliance, integration tests validate with real RabbitMQ. Quality is not optional, it's built-in.

**Covered FRs**: FR-018

---

## Story 6.1: Test Infrastructure Setup

As a developer,
I want pytest-based test infrastructure with proper organization and fixtures,
So that I can write and run tests efficiently with shared test utilities.

**Acceptance Criteria:**

**Given** the project repository
**When** test infrastructure is configured
**Then** tests/ directory contains: unit/, integration/, contract/, performance/, fixtures/, conftest.py

**And** pytest configuration in pytest.ini or pyproject.toml includes: test discovery patterns, coverage settings, markers (unit, integration, slow), output formatting

**And** conftest.py provides shared fixtures: rabbitmq_connection, mcp_server, test_vhost, sample_queues, sample_exchanges

**And** test execution: `pytest` runs all tests, `pytest -m unit` runs unit tests only, `pytest -m integration` runs integration tests

**And** coverage report generated: `pytest --cov=src --cov-report=html --cov-report=term`

**And** test suite runs in CI/CD pipeline automatically on every commit

**And** parallel test execution supported: `pytest -n auto` (uses pytest-xdist)

**Prerequisites:** Story 1.1 (project setup)

**Technical Notes:**
- Use pytest for test framework (async support with pytest-asyncio)
- Test markers: @pytest.mark.unit, @pytest.mark.integration, @pytest.mark.contract, @pytest.mark.slow
- Fixtures scope: function (default), class, module, session
- Coverage tool: pytest-cov (wrapper around coverage.py)
- Coverage target: 80% overall, 95% for critical paths (connection, operations, safety validations)
- Test discovery: test_*.py or *_test.py files
- Fixtures in conftest.py available to all tests
- Environment for tests: use .env.test or environment variables

---

## Story 6.2: Unit Tests for MCP Tools

As a developer,
I want unit tests for all MCP tools (search-ids, get-id, call-id) with mocked dependencies,
So that I can verify tool logic independently without RabbitMQ instance.

**Acceptance Criteria:**

**Given** MCP tools implementation
**When** unit tests execute
**Then** search-ids tests cover: valid queries return relevant operations, invalid queries return empty list, similarity threshold filtering works, caching behavior correct, edge cases (empty query, special chars)

**And** get-id tests cover: valid operation IDs return complete details, invalid IDs return error, schema validation correct, response format matches MCP specification

**And** call-id tests cover: parameter validation before execution, HTTP request construction correct, error handling for connection failures, timeout behavior, response parsing

**And** all tests use mocked dependencies: mock httpx client, mock AMQP connection, mock operation registry, mock embeddings

**And** tests run in <10 seconds total

**And** unit tests achieve 90%+ coverage for MCP tool code

**Prerequisites:** Story 1.6-1.9 (MCP tools implementation), Story 6.1 (test infrastructure)

**Technical Notes:**
- Use unittest.mock or pytest-mock for mocking
- Mock httpx: @pytest.fixture def mock_httpx_client() -> AsyncMock
- Mock embeddings: use small test embeddings file with 10 operations
- Test data: create sample operations.json with known operation IDs
- Parameterized tests: @pytest.mark.parametrize for testing multiple inputs
- Assert response structure matches MCP protocol: {"jsonrpc": "2.0", "id": ..., "result": {...}}
- Test error conditions: connection timeout, invalid JSON response, HTTP 500 errors
- Verify logging calls: assert log messages contain expected correlation IDs

---

## Story 6.3: Unit Tests for RabbitMQ Operations

As a developer,
I want unit tests for all RabbitMQ operations (queues, exchanges, bindings, messages) with mocked API calls,
So that I can verify operation logic, validation, and error handling independently.

**Acceptance Criteria:**

**Given** RabbitMQ operation implementations
**When** unit tests execute
**Then** queue operations tests cover: list parsing, create validation, delete safety checks, purge behavior

**And** exchange operations tests cover: list parsing, create validation, delete protection, type validation

**And** binding operations tests cover: create validation, delete matching, routing key validation

**And** message operations tests cover: publish payload serialization, consume deserialization, ack/nack/reject logic

**And** all tests mock HTTP client responses with realistic RabbitMQ API payloads

**And** tests verify: parameter validation, URL construction, request body formatting, response parsing, error handling

**And** unit tests achieve 85%+ coverage for operation code

**Prerequisites:** Story 3.1-3.11 (topology operations), Story 4.1-4.8 (message operations), Story 6.1 (test infrastructure)

**Technical Notes:**
- Mock httpx responses: mock_response = AsyncMock(status_code=200, json=AsyncMock(return_value={...}))
- Use real RabbitMQ API response samples (captured from actual calls)
- Test validation edge cases: empty strings, null values, max length, special characters
- Test safety validations: queue with messages prevents deletion, exchange with bindings prevents deletion
- Test URL encoding: vhost "/" becomes %2F in URLs
- Verify HTTP methods: GET for lists, PUT for creates, DELETE for deletes
- Test error responses: 404 Not Found, 401 Unauthorized, 500 Internal Server Error

---

## Story 6.4: Integration Tests with Real RabbitMQ

As a developer,
I want integration tests that use real RabbitMQ instance via Docker testcontainers,
So that I can verify end-to-end functionality with actual RabbitMQ behavior.

**Acceptance Criteria:**

**Given** Docker available on test machine
**When** integration tests execute
**Then** RabbitMQ container starts automatically using testcontainers library

**And** container uses official RabbitMQ image with management plugin: rabbitmq:3.13-management

**And** test vhost created: /test-vhost, cleaned up after test suite

**And** integration tests verify complete workflows: create queue → publish message → consume message → acknowledge

**And** tests verify: connection establishment, reconnection after failure, health checks, topology operations, message flow

**And** container logs captured if tests fail (for debugging)

**And** container stopped and removed after test suite completes (cleanup)

**And** integration tests complete in <2 minutes

**Prerequisites:** Story 2.2-2.7 (connection management), Story 3.1-3.11 (topology), Story 4.1-4.8 (messaging), Story 6.1 (test infrastructure)

**Technical Notes:**
- Use testcontainers-python library: from testcontainers.rabbitmq import RabbitMQContainer
- Container configuration: with RabbitMQContainer("rabbitmq:3.13-management") as rabbitmq: ...
- Extract connection details: rabbitmq.get_connection_url(), rabbitmq.get_management_url()
- Fixture scope: module (reuse container across test module for speed)
- Test isolation: each test uses unique queue/exchange names or cleanup after
- Skipped if Docker not available: @pytest.mark.skipif(not docker_available, reason="Docker required")
- CI/CD: Docker available in GitHub Actions (use service containers)
- Test reconnection: stop container, verify reconnection logic, restart container

---

## Story 6.5: Contract Tests for MCP Protocol Compliance

As a developer,
I want contract tests that verify MCP protocol specification compliance,
So that I can ensure the server works correctly with all MCP clients (Claude, ChatGPT, custom clients).

**Acceptance Criteria:**

**Given** MCP server implementation
**When** contract tests execute
**Then** tests verify: JSON-RPC 2.0 request/response format, MCP protocol methods (initialize, tools/list, tools/call), tool definitions schema compliance, error codes follow specification

**And** initialize method returns: server name, version, protocol version, capabilities

**And** tools/list returns exactly 3 tools with correct schemas

**And** tools/call executes tools with parameter validation

**And** invalid requests return appropriate error codes: -32700 (parse error), -32600 (invalid request), -32601 (method not found), -32602 (invalid params), -32603 (internal error)

**And** stdio transport works: reads from stdin, writes to stdout, logs to stderr

**And** contract tests achieve 100% coverage of MCP protocol interactions

**And** tests run with mocked RabbitMQ (focus on protocol, not RabbitMQ operations)

**Prerequisites:** Story 1.6 (MCP server foundation), Story 6.1 (test infrastructure)

**Technical Notes:**
- Test JSON-RPC format: {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
- Validate against MCP specification: https://modelcontextprotocol.io/specification
- Test tool schema format: name, description, input_schema (JSON Schema)
- Test parameter validation: required fields, type checking, constraints
- Test error response format: {"jsonrpc": "2.0", "id": 1, "error": {"code": -32600, "message": "..."}}
- Use JSON Schema validator: jsonschema library to validate tool definitions
- Test stdio: mock stdin/stdout for testing (io.StringIO)
- Document MCP protocol version supported: "2024-11-05"

---

## Story 6.6: Performance Tests & Benchmarks

As a developer,
I want performance tests that measure latency and throughput under load,
So that I can verify performance requirements are met and detect regressions.

**Acceptance Criteria:**

**Given** MCP server with real RabbitMQ connection
**When** performance tests execute
**Then** semantic search latency measured: p50, p95, p99 percentiles for 1000 queries

**And** search latency p95 ≤100ms requirement verified

**And** operation execution latency measured: queue list, create, delete, publish, consume

**And** operation latency p95 ≤200ms requirement verified

**And** throughput measured: messages published per second (target: 1000+/min), messages consumed per second

**And** concurrent operations tested: 10, 50, 100 concurrent queue lists

**And** connection pool performance tested: 5 concurrent HTTP calls reuse connections

**And** logging overhead measured: <5ms per operation

**And** performance metrics logged: {operation, p50, p95, p99, throughput, error_rate}

**Prerequisites:** Story 6.4 (integration tests with RabbitMQ), Story 6.1 (test infrastructure)

**Technical Notes:**
- Use pytest-benchmark for performance testing
- Measure latency: time.perf_counter() before/after operation
- Calculate percentiles: numpy.percentile([latencies], [50, 95, 99])
- Throughput: operations per second = count / elapsed_time
- Concurrent testing: asyncio.gather() for parallel operations
- Warmup: run operations 10 times before measuring (cache warmup)
- Reference hardware: Document test environment specs (CPU, RAM, RabbitMQ version)
- Compare against requirements: assert p95_latency < 100ms
- CI/CD: Run performance tests on representative hardware

---

## Story 6.7: Test Coverage Reporting & Quality Gates

As a developer,
I want automated coverage reports with quality gates that fail builds if coverage drops,
So that code quality remains high and regressions are caught early.

**Acceptance Criteria:**

**Given** test suite execution with coverage measurement
**When** tests complete
**Then** coverage report generated in multiple formats: terminal summary, HTML report, XML (for CI)

**And** coverage metrics include: overall coverage, per-module coverage, per-function coverage, uncovered lines

**And** coverage targets enforced: overall ≥80%, critical modules ≥95% (connection, operations, safety validations)

**And** HTML report shows: green (covered), red (uncovered), yellow (partially covered) lines

**And** CI/CD pipeline fails if coverage below target

**And** coverage badge displayed in README: ![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)

**And** coverage trends tracked over time (via CI/CD artifacts)

**Prerequisites:** Story 6.1-6.6 (all tests), Story 6.1 (test infrastructure)

**Technical Notes:**
- Coverage tool: pytest-cov (wrapper around coverage.py)
- Generate reports: pytest --cov=src --cov-report=term --cov-report=html --cov-report=xml
- HTML report location: htmlcov/index.html
- XML report for CI: coverage.xml (Codecov, Coveralls integration)
- Coverage configuration in .coveragerc or pyproject.toml:
  - [tool.coverage.run] source = ["src"], omit = ["*/tests/*", "*/migrations/*"]
  - [tool.coverage.report] fail_under = 80, show_missing = true
- Quality gate: pytest --cov=src --cov-fail-under=80
- GitHub Actions: upload coverage to Codecov for tracking
- Badge: https://codecov.io/gh/{owner}/{repo}/branch/main/graph/badge.svg

---

## Story 6.8: Test Data Fixtures & Factories

As a developer,
I want reusable test data fixtures and factories for queues, exchanges, bindings, and messages,
So that I can quickly create test scenarios without duplicating setup code.

**Acceptance Criteria:**

**Given** test infrastructure
**When** tests use fixtures
**Then** fixtures provide: sample_queue (name, vhost, properties), sample_exchange (name, type, properties), sample_binding (source, destination, routing_key), sample_message (payload, properties)

**And** factories support customization: create_queue(name="custom", durable=False)

**And** fixtures handle cleanup: queues/exchanges deleted after test, connections closed

**And** fixtures use realistic data: names follow naming conventions, properties use common values

**And** fixtures support multiple scenarios: empty queue, queue with messages, durable vs transient, different exchange types

**And** factory pattern allows generating many objects: create_queues(count=10)

**And** fixtures documented in tests/fixtures/README.md

**Prerequisites:** Story 6.1 (test infrastructure)

**Technical Notes:**
- Create tests/fixtures/ directory with factory modules
- Use pytest fixtures: @pytest.fixture with scope (function, module, session)
- Factory functions: def create_queue(name=None, vhost="/", durable=True, **kwargs) -> dict
- Cleanup with yield: fixture creates resource, yields, then cleanup code runs
- Use faker library for realistic test data: from faker import Faker; fake.uuid4()
- Common test data: TEST_VHOST = "/test", TEST_QUEUE_PREFIX = "test-queue-", TEST_EXCHANGE_PREFIX = "test-exchange-"
- Fixtures auto-use: @pytest.fixture(autouse=True) for cleanup fixtures
- Document fixture usage in docstrings and README

---
