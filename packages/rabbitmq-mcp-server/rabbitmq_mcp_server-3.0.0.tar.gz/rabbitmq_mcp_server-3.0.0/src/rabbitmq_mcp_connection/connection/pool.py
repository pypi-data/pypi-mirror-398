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

"""Pool assíncrono de conexões RabbitMQ."""

import asyncio
from datetime import UTC, datetime

from rabbitmq_mcp_connection.connection.exceptions import PoolTimeoutError
from rabbitmq_mcp_connection.connection.manager import ConnectionManager
from rabbitmq_mcp_connection.logging.config import get_logger
from rabbitmq_mcp_connection.schemas.connection import ConnectionConfig, PoolStats

LOGGER = get_logger(__name__)


class PooledConnection:
    """Wrapper de ``ConnectionManager`` rastreável para uso em pool."""

    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager
        self.connection = manager.connection
        self.channel = manager.channel
        self.in_use = False
        self.created_at = datetime.now(UTC)
        self.last_used = self.created_at

    async def check_health(self) -> bool:
        connection = self.manager.connection
        channel = self.manager.channel
        if connection is None or getattr(connection, "is_closed", False):
            return False
        if channel is None or getattr(channel, "is_closed", False):
            return False
        return True

    async def reset(self) -> None:
        await self.manager.disconnect()
        await self.manager.connect()
        self.connection = self.manager.connection
        self.channel = self.manager.channel
        self.last_used = datetime.now(UTC)

    def mark_in_use(self) -> None:
        self.in_use = True
        self.last_used = datetime.now(UTC)

    def mark_available(self) -> None:
        self.in_use = False
        self.last_used = datetime.now(UTC)

    async def close(self) -> None:
        await self.manager.disconnect()


class ConnectionPool:
    """Pool assíncrono de conexões reutilizáveis."""

    def __init__(
        self,
        config: ConnectionConfig,
        *,
        max_size: int = 5,
        timeout: int = 10,
    ) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        if timeout < 1:
            raise ValueError("timeout must be >= 1 second")

        self.config = config
        self.max_size = max_size
        self.timeout = timeout
        self._available: asyncio.Queue[PooledConnection] = asyncio.Queue(maxsize=max_size)
        self._all_connections: list[PooledConnection] = []
        self._lock = asyncio.Lock()
        self._waiters = 0

    async def initialize(self) -> None:
        async with self._lock:
            missing = self.max_size - len(self._all_connections)
            for _ in range(missing):
                pooled = await self._create_connection()
                self._all_connections.append(pooled)
                await self._available.put(pooled)
        LOGGER.info("pool.initialized", size=self.max_size)

    async def acquire(self) -> PooledConnection:
        self._waiters += 1
        try:
            pooled = await asyncio.wait_for(self._available.get(), timeout=self.timeout)
        except TimeoutError as exc:
            raise PoolTimeoutError(f"No connection available after {self.timeout}s") from exc
        finally:
            self._waiters = max(self._waiters - 1, 0)

        pooled.mark_in_use()
        LOGGER.debug("pool.connection_acquired", in_use=self.in_use_count)
        return pooled

    async def release(self, pooled: PooledConnection) -> None:
        if not isinstance(pooled, PooledConnection):  # pragma: no cover - defesa
            raise TypeError("release expects PooledConnection instance")

        if await pooled.check_health():
            pooled.mark_available()
            await self._available.put(pooled)
            LOGGER.debug("pool.connection_released", available=self.available_count)
            return

        await self._replace_connection(pooled)

    async def close(self) -> None:
        for pooled in self._all_connections:
            try:
                await pooled.close()
            except Exception:  # pragma: no cover - fechamento best-effort
                LOGGER.warning("pool.connection_close_failed")
        self._all_connections.clear()
        while not self._available.empty():
            self._available.get_nowait()
        LOGGER.info("pool.closed")

    async def get_stats(self) -> PoolStats:
        return PoolStats(
            max_size=self.max_size,
            total_connections=len(self._all_connections),
            in_use=self.in_use_count,
            available=self.available_count,
            waiting_for_connection=self._waiters,
            acquire_timeout_seconds=self.timeout,
        )

    @property
    def in_use_count(self) -> int:
        return sum(1 for conn in self._all_connections if conn.in_use)

    @property
    def available_count(self) -> int:
        return self._available.qsize()

    async def _create_connection(self) -> PooledConnection:
        manager = ConnectionManager(self.config)
        await manager.connect()
        return PooledConnection(manager)

    async def _replace_connection(self, pooled: PooledConnection) -> None:
        async with self._lock:
            if pooled in self._all_connections:
                self._all_connections.remove(pooled)
            try:
                await pooled.close()
            except Exception:  # pragma: no cover - fechamento best-effort
                LOGGER.warning("pool.connection_discard_failed")

            new_connection = await self._create_connection()
            self._all_connections.append(new_connection)
            await self._available.put(new_connection)
            LOGGER.info("pool.connection_replaced")


__all__ = ["ConnectionPool", "PooledConnection"]
