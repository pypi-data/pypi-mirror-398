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

"""Componente de verificação de saúde da conexão RabbitMQ."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from rabbitmq_mcp_connection.connection.manager import ConnectionManager
from rabbitmq_mcp_connection.logging.config import get_logger
from rabbitmq_mcp_connection.schemas.connection import ConnectionState, HealthStatus

LOGGER = get_logger(__name__)


class HealthChecker:
    """Executa health checks rápidos sobre uma ``ConnectionManager``."""

    def __init__(
        self,
        manager: ConnectionManager,
        *,
        timeout: float = 1.0,
        broker_probe: Callable[[], Awaitable[bool]] | None = None,
    ) -> None:
        self._manager = manager
        self._timeout = timeout
        self._broker_probe = broker_probe

    async def check_health(self) -> HealthStatus:
        start = time.perf_counter()
        is_connected = self._manager.state == ConnectionState.CONNECTED
        broker_available = False
        error_message: str | None = None

        try:
            broker_available = await asyncio.wait_for(self._probe_broker(), timeout=self._timeout)
        except TimeoutError:
            error_message = "Broker health check timed out"
        except Exception as exc:  # pragma: no cover - falhas externas reais
            error_message = str(exc)
            LOGGER.warning("health.check_failed", exception=str(exc))

        end = time.perf_counter()

        return HealthStatus(
            is_connected=is_connected,
            broker_available=broker_available,
            latency_ms=(end - start) * 1000,
            last_check=datetime.now(UTC),
            error_message=error_message,
        )

    async def _probe_broker(self) -> bool:
        if self._broker_probe is not None:
            return await self._broker_probe()

        connection = self._manager.connection
        channel = self._manager.channel
        if connection is None or getattr(connection, "is_closed", False):
            return False
        if channel is None or getattr(channel, "is_closed", False):
            return False

        # Se ambos permanecem abertos consideramos broker disponível.
        return True
