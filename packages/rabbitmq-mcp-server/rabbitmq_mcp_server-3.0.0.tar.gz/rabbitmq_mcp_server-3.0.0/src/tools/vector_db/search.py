from __future__ import annotations

"""
Copyright (C) 2025 Luciano Guerche

This file is part of rabbitmq-mcp-server.

rabbitmq-mcp-server is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

rabbitmq-mcp-server is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with rabbitmq-mcp-server. If not, see <https://www.gnu.org/licenses/>.
"""

from pathlib import Path
from typing import Any

from utils.numpy_compat import ensure_numpy_compat

from .embeddings import embed_text

ensure_numpy_compat()

try:  # pragma: no cover - dependencies resolved at runtime
    import chromadb
except Exception as exc:  # pragma: no cover - optional dependency failure
    chromadb = None  # type: ignore[assignment]
    _IMPORT_ERROR: Exception | None = exc
else:  # pragma: no cover - chromadb available
    _IMPORT_ERROR = None


VECTOR_DB_DIR = Path(__file__).parent.parent.parent.parent / "data" / "vectors"
_CLIENT = None
_COLLECTION = None


def _get_collection():  # type: ignore[no-untyped-def]
    global _CLIENT, _COLLECTION
    if chromadb is None:
        raise RuntimeError(
            "Semantic search dependencies are not available; install the 'vector' extra"
        ) from _IMPORT_ERROR

    if _CLIENT is None:
        _CLIENT = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    if _COLLECTION is None:
        _COLLECTION = _CLIENT.get_or_create_collection("rabbitmq_ops")
    return _COLLECTION


def semantic_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    collection = _get_collection()
    embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=limit,
    )
    matches: list[dict[str, Any]] = []
    ids_raw = results.get("ids") or [[]]
    distances_raw = results.get("distances") or [[]]
    metadatas_raw = results.get("metadatas") or [[]]
    documents_raw = results.get("documents") or [[]]

    ids = ids_raw[0] if ids_raw else []
    distances = distances_raw[0] if distances_raw else []
    metadatas = metadatas_raw[0] if metadatas_raw else []
    documents = documents_raw[0] if documents_raw else []

    for idx in range(len(ids)):
        matches.append(
            {
                "id": ids[idx],
                "score": distances[idx],
                "metadata": metadatas[idx] if metadatas else {},
                "document": documents[idx] if documents else None,
            }
        )
    return matches
