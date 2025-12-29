# Epic 9: Pre-built Vector Database (sqlite-vec)

**Goal**: Replace runtime embedding generation with pre-built vector database using sqlite-vec for faster startup, better performance, and offline operation support.

**Value**: Eliminates ~500ms embedding model load time at startup, enables offline semantic search, reduces memory footprint, and provides foundation for future AI features.

**Priority**: High (Performance improvement)

---

## Story 9.1: sqlite-vec Integration

As a developer,
I want semantic search backed by sqlite-vec instead of in-memory embeddings,
So that I get faster startup times and persistent vector storage without external dependencies.

**Acceptance Criteria:**

**Given** the application with sqlite-vec database
**When** server starts
**Then** embeddings are loaded from SQLite database in <100ms (vs ~500ms for model load)

**And** database file located at: ./data/embeddings.db (portable, committed to repo)

**And** database schema includes: operations table (operation_id, description, namespace), embeddings table (operation_id, embedding_vector)

**And** semantic search queries sqlite-vec using vector similarity: SELECT operation_id, distance FROM embeddings ORDER BY vector_distance(embedding, ?) LIMIT 10

**And** search performance: <50ms for typical queries (improvement from <100ms)

**And** database is portable: works offline, no network dependencies, no model downloads

**And** migration script provided: convert existing embeddings.json to sqlite-vec database

**Prerequisites:** Epic 1 complete (semantic search)

**Technical Notes:**
- Use sqlite-vec extension: https://github.com/asg017/sqlite-vec
- Vector storage: BLOB column with float32 array
- Distance functions: cosine similarity (vector_distance_cosine), L2 distance
- Indexing: create vector index for fast similarity search
- Database size: ~2MB for 100 operations with 384-dimension vectors
- Migration: python scripts/migrate_embeddings_to_db.py
- Fallback: if sqlite-vec unavailable, use in-memory embeddings (current approach)

---

## Story 9.2: Incremental Embedding Updates

As a developer,
I want to update embeddings incrementally when operations change,
So that I don't need to regenerate the entire database for small changes.

**Acceptance Criteria:**

**Given** sqlite-vec database with existing embeddings
**When** operation descriptions are modified or new operations added
**Then** only changed operations have embeddings regenerated

**And** update script: python scripts/update_embeddings.py --operations=queues.list,exchanges.create

**And** bulk update supported: regenerate all with --all flag

**And** update completes in <10 seconds for 10 operations

**And** database automatically backed up before updates

**And** update validation: verify embedding dimensions match, check for corruption

**Prerequisites:** Story 9.1 (sqlite-vec integration)

**Technical Notes:**
- Detect changes: compare operation descriptions with database, identify diffs
- Incremental generation: only run embedding model for changed operations
- SQL UPDATE: UPDATE embeddings SET embedding_vector = ? WHERE operation_id = ?
- Transaction: wrap updates in transaction for atomicity
- Backup: cp embeddings.db embeddings.db.backup before updates
- Validation: SELECT COUNT(*) should match operations count

---
