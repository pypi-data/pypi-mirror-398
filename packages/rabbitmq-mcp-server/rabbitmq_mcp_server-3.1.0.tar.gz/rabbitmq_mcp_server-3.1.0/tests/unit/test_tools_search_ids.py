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

import pytest
from pytest import MonkeyPatch

from rabbitmq_mcp_connection.tools import search_ids
from rabbitmq_mcp_connection.tools.search_ids import (
    KeywordFallbackBackend,
    handle_search_ids,
)


@pytest.fixture(autouse=True)
def _force_keyword_backend(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(search_ids, "_BACKEND", KeywordFallbackBackend())


def test_handle_search_ids_requires_query() -> None:
    result = handle_search_ids("")
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "INVALID_QUERY"


def test_handle_search_ids_returns_results() -> None:
    result = handle_search_ids("connection")
    assert result.success is True
    assert result.result is not None
    items = result.result["items"]
    assert len(items) > 0
    assert all("operation_id" in item for item in items)
    assert result.metadata == {"backend": "KeywordFallbackBackend"}
