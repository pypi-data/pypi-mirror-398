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

from tools import get_id


def test_get_id_returns_operation_schema() -> None:
    schema = get_id.get_id("queues.list")

    assert schema.operation_id == "queues.list"
    assert schema.summary
    assert schema.description
    assert isinstance(schema.parameters, list)
    assert "200" in schema.responses


def test_get_id_raises_for_unknown_operation() -> None:
    with pytest.raises(ValueError) as exc:
        get_id.get_id("unknown.operation")

    assert "unknown.operation" in str(exc.value)
