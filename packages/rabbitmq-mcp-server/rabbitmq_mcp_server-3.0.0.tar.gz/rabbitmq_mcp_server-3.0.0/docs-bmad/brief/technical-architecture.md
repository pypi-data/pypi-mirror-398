# Technical Architecture

## OpenAPI-Driven Generation Pipeline

**Architecture Philosophy**: Single source of truth (OpenAPI specification) drives all code generation at build-time, ensuring consistency and eliminating runtime overhead.

**Pipeline Stages**:

```
┌─────────────────────────────────────────────────────────────┐
│  1. OpenAPI Specification (Source of Truth)                 │
│     .specify/memory/rabbitmq-http-api-openapi.yaml         │
│     - 4800+ lines defining all RabbitMQ Management API      │
│     - Operations (paths), Schemas (components), Parameters  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Schema Generation (Build-Time)                          │
│     Script: python scripts/generate_schemas.py              │
│     Output: src/schemas/generated_schemas.py                │
│     - Pydantic models from components.schemas               │
│     - Request/response validation schemas                   │
│     - Type safety for all operations                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Embeddings Generation (Build-Time)                      │
│     Script: python scripts/generate_embeddings.py           │
│     Output: data/embeddings.json                            │
│     - Semantic vectors from operation descriptions          │
│     - Pre-computed for <100ms search performance            │
│     - Model: sentence-transformers/all-mpnet-base-v2        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Operation Registry Generation (Build-Time)              │
│     Script: python scripts/extract_operations.py            │
│     Output: data/operations.json                            │
│     - Maps operation IDs to HTTP methods and paths          │
│     - Parameter definitions and validation rules            │
│     - Documentation and examples                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Runtime Execution (Zero Generation Overhead)            │
│     - Load pre-generated artifacts from disk                │
│     - Instant server startup (<1 second)                    │
│     - Semantic search uses pre-computed embeddings          │
│     - Operation execution uses pre-validated schemas        │
└─────────────────────────────────────────────────────────────┘
```

**Generation Triggers**:
1. **OpenAPI file modified**: Manual or automated detection (file watchers, pre-commit hooks)
2. **Manual invocation**: Developer runs generation scripts when needed
3. **Initial repository setup**: First-time clone runs all generation scripts
4. **CI/CD validation**: Pipeline verifies artifacts are up-to-date (does NOT regenerate)

**Artifact Management**:
- **Committed to version control**: All generated files (schemas, embeddings, operations.json)
- **Portable across platforms**: No external database dependencies
- **Validated in CI**: Pipeline ensures OpenAPI and artifacts stay synchronized
- **No runtime generation**: Server startup is instant with pre-built artifacts

**Key Benefits**:
- **Performance**: <100ms semantic search, <1s server startup
- **Reliability**: Build-time errors caught before deployment
- **Consistency**: Single source of truth eliminates drift
- **Maintainability**: OpenAPI changes automatically propagate through generation
- **Developer Experience**: Type-safe operations with IDE autocomplete

---
