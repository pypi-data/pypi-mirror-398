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

"""Implementação do MCP tool search-ids."""

from pathlib import Path

from rabbitmq_mcp_connection.schemas.mcp import (
    MCPError,
    MCPToolResult,
    PaginationMetadata,
    PaginationParams,
    SearchItem,
    SearchResult,
)
from rabbitmq_mcp_connection.tools.contracts import load_connection_operations
from utils.numpy_compat import ensure_numpy_compat

ensure_numpy_compat()

try:  # pragma: no cover - dependências opcionais
    import chromadb
    from sentence_transformers import SentenceTransformer
except Exception as exc:  # pragma: no cover - fallback sem embeddings
    chromadb = None  # type: ignore[assignment]
    SentenceTransformer = None
    _IMPORT_ERROR: Exception | None = exc
else:  # pragma: no cover - dependências disponíveis
    _IMPORT_ERROR = None

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "vectors"
COLLECTION_NAME = "connection_operations"


class SearchBackend:
    def search(self, query: str, limit: int) -> list[tuple[str, float, dict]]:
        raise NotImplementedError


class KeywordFallbackBackend(SearchBackend):
    def __init__(self) -> None:
        self.operations = load_connection_operations()

    def search(self, query: str, limit: int) -> list[tuple[str, float, dict]]:
        query_lower = query.lower()
        scored: list[tuple[str, float, dict]] = []
        for operation_id, schema in self.operations.items():
            text = f"{schema.name} {schema.description}".lower()
            score = 1.0 if query_lower and query_lower in text else 0.25
            metadata = {
                "name": schema.name,
                "category": schema.category,
                "description": schema.description,
            }
            scored.append((operation_id, score, metadata))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]


class ChromaSearchBackend(SearchBackend):
    def __init__(self) -> None:
        if chromadb is None or SentenceTransformer is None:
            raise RuntimeError("Dependências de busca semântica não instaladas")

        self._base_path = DATA_DIR
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self._base_path))
        self._collection = self._client.get_or_create_collection(COLLECTION_NAME)
        self._model = SentenceTransformer("all-MiniLM-L6-v2")

    def search(self, query: str, limit: int) -> list[tuple[str, float, dict]]:
        embedding = self._model.encode(query)
        result = self._collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=limit,
        )

        ids_raw = result.get("ids") or [[]]
        distances_raw = result.get("distances") or [[]]
        metadatas_raw = result.get("metadatas") or [[]]

        ids = ids_raw[0] if ids_raw else []
        distances = distances_raw[0] if distances_raw else []
        metadatas = metadatas_raw[0] if metadatas_raw else []

        scored: list[tuple[str, float, dict]] = []
        for op_id, distance, metadata in zip(ids, distances, metadatas):
            score = float(max(0.0, 1.0 - distance))
            scored.append((op_id, score, dict(metadata or {})))
        return scored


def _resolve_backend() -> SearchBackend:
    if chromadb is not None and SentenceTransformer is not None:
        try:
            return ChromaSearchBackend()
        except Exception:  # pragma: no cover - fallback
            pass
    return KeywordFallbackBackend()


_BACKEND = _resolve_backend()


def handle_search_ids(query: str, pagination: PaginationParams | None = None) -> MCPToolResult:
    if not query:
        return MCPToolResult(
            success=False,
            error=MCPError(code="INVALID_QUERY", message="Query must be non-empty"),
        )

    pagination = pagination or PaginationParams()
    backend = _BACKEND
    raw_results = backend.search(query, pagination.page_size * pagination.page)

    start_index = (pagination.page - 1) * pagination.page_size
    page_items = raw_results[start_index : start_index + pagination.page_size]

    items = [
        SearchItem(operation_id=op_id, score=score, metadata=metadata)
        for op_id, score, metadata in page_items
    ]

    result = SearchResult(
        items=items,
        pagination=PaginationMetadata(
            page=pagination.page,
            page_size=pagination.page_size,
            total=len(raw_results),
        ),
    )

    metadata = {"backend": backend.__class__.__name__}
    if isinstance(backend, KeywordFallbackBackend) and _IMPORT_ERROR is not None:
        metadata["dependency_error"] = str(_IMPORT_ERROR)

    return MCPToolResult(
        success=True,
        result=result.model_dump(),
        metadata=metadata,
    )


__all__ = ["handle_search_ids"]
