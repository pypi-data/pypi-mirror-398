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

"""Testes unitários para `ConnectionManager`."""

import pytest
import pytest_asyncio

from rabbitmq_mcp_connection.connection.manager import ConnectionManager
from rabbitmq_mcp_connection.schemas.connection import (
    ConnectionConfig,
    ConnectionState,
)


@pytest.fixture
def config() -> ConnectionConfig:
    return ConnectionConfig(host="localhost", user="guest", password="guest")


@pytest_asyncio.fixture(autouse=True)
async def fake_connect(monkeypatch: pytest.MonkeyPatch):
    from rabbitmq_mcp_connection.connection import manager as manager_module

    async def _connect(**_: object):
        class _Channel:
            def __init__(self) -> None:
                self.is_closed = False

            async def close(self) -> None:  # pragma: no cover - trivial
                self.is_closed = True

        class _Connection:
            def __init__(self) -> None:
                self.is_closed = False
                self.server_properties = {"product": "RabbitMQ", "version": "3.12.0"}
                self._channel = _Channel()

            async def channel(self):
                return self._channel

            async def close(self) -> None:
                self.is_closed = True

        return _Connection()

    monkeypatch.setattr(manager_module.aio_pika, "connect_robust", _connect)

    yield


@pytest.mark.asyncio
async def test_manager_initialization(config: ConnectionConfig) -> None:
    manager = ConnectionManager(config)
    assert manager.state == ConnectionState.DISCONNECTED
    assert manager.connection is None
    assert manager.channel is None


@pytest.mark.asyncio
async def test_connect_updates_state(config: ConnectionConfig) -> None:
    manager = ConnectionManager(config)
    await manager.connect()
    assert manager.state == ConnectionState.CONNECTED
    assert manager.connection is not None
    assert manager.channel is not None


@pytest.mark.asyncio
async def test_disconnect_updates_state(config: ConnectionConfig) -> None:
    manager = ConnectionManager(config)
    await manager.connect()
    await manager.disconnect()
    assert manager.state == ConnectionState.DISCONNECTED
    assert manager.connection is None
    assert manager.channel is None


@pytest.mark.asyncio
async def test_get_status_returns_current_state(config: ConnectionConfig) -> None:
    manager = ConnectionManager(config)
    await manager.connect()
    status = await manager.get_status()
    assert status["state"] == ConnectionState.CONNECTED.value
    assert status["retry_attempts"] == 0
    assert status["connection_url"].startswith("amqp://guest:***@localhost")
