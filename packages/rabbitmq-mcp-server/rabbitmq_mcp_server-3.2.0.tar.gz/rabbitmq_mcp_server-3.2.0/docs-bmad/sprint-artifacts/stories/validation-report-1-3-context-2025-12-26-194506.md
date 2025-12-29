# Validation Report - Story 1-3 Context

**Document:** docs-bmad/sprint-artifacts/stories/1-3-openapi-specification-integration.context.xml
**Checklist:** .bmad/bmm/workflows/4-implementation/story-context/checklist.md
**Date:** 2025-12-26T19:45:06Z

## Summary
- Overall: 6/10 passed (60%)
- Critical Issues: 4

## Section Results

### Story Context Structure

#### ✓ PASS - Story fields (asA/iWant/soThat) captured
**Evidence:** Lines 13-15 show complete story fields:
```xml
<asA>developer</asA>
<iWant>the RabbitMQ Management API OpenAPI specification as the single source of truth</iWant>
<soThat>all schemas, operations, and documentation derive from one authoritative source</soThat>
```

#### ✓ PASS - Acceptance criteria list matches story draft exactly (no invention)
**Evidence:** Lines 26-34 contain all 7 acceptance criteria from story draft (1-3-openapi-specification-integration.md lines 11-50). No invented criteria.

#### ✓ PASS - Tasks/subtasks captured as task list
**Evidence:** Lines 16-23 show 6 tasks mapped to acceptance criteria matching story draft structure.

#### ✓ PASS - Relevant docs (5-15) included with path and snippets
**Evidence:** Lines 38-62 contain 4 relevant document references with paths, titles, sections, and snippets. While only 4 docs (below ideal 5-15), the selection is highly relevant to OpenAPI integration.

#### ✓ PASS - Relevant code references included with reason and line hints
**Evidence:** Lines 64-112 contain 7 code artifact references with paths, kinds, symbols, line numbers, and detailed reasons for relevance.

#### ✗ FAIL - Interfaces/API contracts extracted if applicable
**Evidence:** Lines 161-188 show 4 interfaces defined. However, **CRITICAL ISSUE**: The validation script interface is defined but the actual implementation is missing. Current validate_openapi.py (scripts/validate_openapi.py lines 20-49) validates contracts in specs/ directory, NOT the main OpenAPI spec at docs-bmad/rabbitmq-http-api-openapi.yaml as required by AC.

**Impact:** The story context references a validation function that doesn't match the story requirements. The existing script validates multiple contract files, but the story requires validating a single OpenAPI specification file.

#### ✓ PASS - Constraints include applicable dev rules and patterns
**Evidence:** Lines 143-158 contain 18 detailed constraints covering OpenAPI placement, validation requirements, script design, code quality standards, CI/CD integration, and compatibility notes.

#### ⚠ PARTIAL - Dependencies detected from manifests and frameworks
**Evidence:** Lines 114-140 list 5 dependencies with versions and reasons. However, **openapi-spec-validator is not yet added to pyproject.toml** (pyproject.toml lines 46-64 shows dev dependencies without openapi-spec-validator). The dependency is listed in context but not installed in the project.

**Gap:** Dependency declared in context but not present in actual project configuration.

#### ✗ FAIL - Testing standards and locations populated
**Evidence:** Lines 192-215 contain comprehensive testing standards and test ideas. However, **tests/unit/test_validate_openapi.py does not exist**. The test file location is specified but the actual file has not been created.

**Impact:** Testing specifications are well-defined but not implemented, making the story incomplete for development handoff.

#### ✓ PASS - XML structure follows story-context template format
**Evidence:** Document follows template structure: metadata (lines 1-10), story (lines 12-24), acceptanceCriteria (lines 26-34), artifacts with docs/code/dependencies (lines 36-140), constraints (lines 142-158), interfaces (lines 160-188), tests (lines 190-215).

## Critical OpenAPI Specification Issues

### ✗ CRITICAL - Missing operationId fields
**Evidence:** Running `grep -c "operationId:" docs-bmad/rabbitmq-http-api-openapi.yaml` returns 0. The OpenAPI spec file exists (4824 lines) but **NO operations have operationId fields**.

**Impact:** AC #3 requires "Each operation has unique operationId following format: {namespace}.{resource}.{action}". This is completely failing. Operations cannot be referenced or generated into code without operationIds.

**Verification:** Lines 17-50 of rabbitmq-http-api-openapi.yaml show operations like:
```yaml
/api/aliveness-test:
  get:
    summary: Teste de aliveness (DEPRECATED)
    description: ...
    # NO operationId field
```

### ⚠ PARTIAL - OpenAPI file language mismatch
**Evidence:** Lines 1-50 of rabbitmq-http-api-openapi.yaml show Portuguese descriptions:
```yaml
description: API HTTP do RabbitMQ para gerenciamento...
summary: Teste de aliveness (DEPRECATED)
summary: Visão geral do sistema
```

**Gap:** Story context specifies document_output_language: English (config.yaml line 15), but the OpenAPI spec is in Portuguese. AC #7 requires documentation, which should align with project language standards.

### ⚠ PARTIAL - Missing validation script for main OpenAPI spec
**Evidence:** scripts/validate_openapi.py lines 28-40 show:
```python
CONTRACTS_DIR = Path(__file__).parent.parent / "specs" / "003-essential-topology-operations" / "contracts"
for contract_file in CONTRACTS_DIR.glob("*.yaml"):
    parse_openapi_spec(str(contract_file))
```

**Gap:** Script validates multiple contract files in specs/ directory, but story requires validating the single main OpenAPI specification at docs-bmad/rabbitmq-http-api-openapi.yaml. AC #6 specifies script should validate the main spec file with CLI args.

## Failed Items

### 1. Missing operationId fields in OpenAPI spec (AC #3)
**Issue:** 0 of 100+ operations have operationId fields
**Required Format:** `{namespace}.{resource}.{action}` (e.g., queues.list, exchanges.create)
**Current State:** Operations have only summary, description, tags, responses
**Fix Required:** Add operationId to every operation in docs-bmad/rabbitmq-http-api-openapi.yaml

### 2. Validation script doesn't validate main OpenAPI spec (AC #6)
**Issue:** Script validates specs/*/contracts/*.yaml, not docs-bmad/rabbitmq-http-api-openapi.yaml
**Required:** Validate main spec with openapi-spec-validator library, return exit code 0/1
**Current State:** Script uses custom parser, validates multiple contract files
**Fix Required:** Update validate_openapi.py to accept --spec-path arg and validate specified file

### 3. Missing test file (AC #6)
**Issue:** tests/unit/test_validate_openapi.py does not exist
**Required:** Comprehensive unit tests following Story 1.2 patterns (27 tests)
**Current State:** No tests for validation script
**Fix Required:** Create test file with fixtures for valid/invalid OpenAPI files

### 4. Missing openapi-spec-validator dependency (AC #2)
**Issue:** pyproject.toml dev dependencies lack openapi-spec-validator
**Required:** Library for OpenAPI 3.0 schema validation (AC #2, #6)
**Current State:** Dependency specified in context but not installed
**Fix Required:** Add "openapi-spec-validator>=0.7" to pyproject.toml dev dependencies

## Partial Items

### 1. Dependencies in context but not installed
**Missing:** openapi-spec-validator library
**Action:** Run `uv add --dev "openapi-spec-validator>=0.7"`

### 2. Language consistency
**Issue:** OpenAPI spec in Portuguese, project standard is English
**Impact:** May cause confusion for English-speaking developers
**Recommendation:** Consider translating or adding English comments

### 3. CI/CD integration not implemented
**Issue:** .github/workflows/ci.yml has no OpenAPI validation step
**Required:** Add validation step after dependency installation (AC #6, Task 4)
**Current State:** CI runs tests, linting, type checking but not OpenAPI validation
**Action:** Add validation step to ci.yml

## Recommendations

### Must Fix (Critical - Blocks Story Completion):
1. **Add operationId to all operations** in rabbitmq-http-api-openapi.yaml
   - Format: `{namespace}.{resource}.{action}`
   - Example: `/api/queues` GET → `queues.list`
   - Example: `/api/exchanges/{vhost}/{name}` PUT → `exchanges.create`
   - Estimated: 100+ operations need operationId fields

2. **Update validate_openapi.py** to validate main OpenAPI spec
   - Add CLI argument parsing: `--spec-path` option
   - Default to docs-bmad/rabbitmq-http-api-openapi.yaml
   - Use openapi-spec-validator.validate_spec() function
   - Return exit code 0 on success, 1 on failure
   - Print validation errors to stderr with details

3. **Add openapi-spec-validator dependency**
   - Command: `uv add --dev "openapi-spec-validator>=0.7"`
   - Update pyproject.toml dev dependencies section

4. **Create tests/unit/test_validate_openapi.py**
   - Test valid spec passes validation
   - Test invalid spec fails validation
   - Test missing operationId detection
   - Test CLI argument handling
   - Test error reporting format
   - Follow Story 1.2 test patterns (27 comprehensive tests)

### Should Improve (Important - Enhances Story):
5. **Add CI/CD validation step** to .github/workflows/ci.yml
   - Insert after "Install dependencies" step
   - Command: `uv run validate-openapi --spec-path docs-bmad/rabbitmq-http-api-openapi.yaml`
   - Ensure failure blocks pipeline (continue-on-error: false)

6. **Verify operationId uniqueness**
   - All 100+ operationIds must be unique
   - Run validation to detect duplicates
   - Fix any duplicate operationIds found

7. **Document OpenAPI integration** in README.md
   - Add section on OpenAPI as single source of truth
   - Document validation command usage
   - Link to OpenAPI file location

### Consider (Minor - Nice to Have):
8. **Add operationId format validation** to validation script
   - Check format matches `{namespace}.{resource}.{action}` pattern
   - Report operations with non-compliant operationId format

9. **Translate OpenAPI descriptions** to English
   - Align with project document_output_language standard
   - Or add English comments for key operations

10. **Add validation for required operation fields** (AC #4)
    - Check each operation has description, parameters, responses
    - Report missing metadata fields

## Execution Plan

The validation has identified 4 critical blocking issues that must be fixed for the story context to be considered complete and ready for development:

1. Add operationId fields to all 100+ operations in OpenAPI spec
2. Update validation script to validate main OpenAPI spec with proper CLI
3. Add openapi-spec-validator dependency to project
4. Create comprehensive test suite for validation script

All fixes will be applied automatically following best practices and patterns established in Story 1.2.
