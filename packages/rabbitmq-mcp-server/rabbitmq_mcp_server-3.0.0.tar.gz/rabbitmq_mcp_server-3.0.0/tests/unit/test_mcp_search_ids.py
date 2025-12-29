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

import time
from typing import Any

import pytest

from tools import search_ids


@pytest.fixture(autouse=True)
def _stub_semantic_search(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_results: list[dict[str, Any]] = [
        {"operation_id": "queues.list", "score": 0.95, "summary": "List queues"},
        {"operation_id": "exchanges.list", "score": 0.91, "summary": "List exchanges"},
        {"operation_id": "bindings.list", "score": 0.88, "summary": "List bindings"},
    ]

    def fake_semantic_search(query: str, limit: int) -> list[dict[str, Any]]:
        assert limit >= len(fake_results)
        assert query
        return fake_results.copy()

    monkeypatch.setattr(search_ids, "semantic_search", fake_semantic_search)


def test_search_ids_validates_pagination_inputs() -> None:
    with pytest.raises(ValueError):
        search_ids.search_ids("queues", page=0)
    with pytest.raises(ValueError):
        search_ids.search_ids("queues", pageSize=0)
    with pytest.raises(ValueError):
        search_ids.search_ids("queues", pageSize=500)


def test_search_ids_returns_paginated_metadata() -> None:
    result = search_ids.search_ids("queues", page=2, pageSize=1)

    assert result.page == 2
    assert result.pageSize == 1
    assert result.totalItems == 3
    assert result.totalPages == 3
    assert result.hasNextPage is True
    assert result.hasPreviousPage is True
    assert len(result.results) == 1
    assert result.results[0].operation_id == "exchanges.list"


def test_search_ids_completes_within_performance_budget() -> None:
    started = time.perf_counter()
    search_ids.search_ids("bindings", page=1, pageSize=3)
    duration_ms = (time.perf_counter() - started) * 1000

    assert duration_ms < 100, "Semantic search should complete within 100ms"
