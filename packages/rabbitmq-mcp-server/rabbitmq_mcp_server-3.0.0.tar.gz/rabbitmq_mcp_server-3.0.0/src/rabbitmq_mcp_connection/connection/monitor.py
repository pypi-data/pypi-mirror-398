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

"""Monitoramento de eventos de conexão RabbitMQ."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from rabbitmq_mcp_connection.connection.aio_pika_compat import (
    AbstractConnection,
    RobustConnection,
)
from rabbitmq_mcp_connection.logging.config import get_logger

LOGGER = get_logger(__name__)


class ConnectionMonitor:
    """Escuta eventos de fechamento e agenda reconexão automática."""

    def __init__(
        self,
        connection: RobustConnection,
        *,
        on_connection_lost: Callable[[], Coroutine[None, None, None]] | None = None,
    ) -> None:
        self._connection = connection
        self._on_connection_lost = on_connection_lost
        self._started = False
        self._callback_registered = False
        self._callback_collection: Any | None = None

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        add_close_callback = getattr(self._connection, "add_close_callback", None)

        if callable(add_close_callback):
            add_close_callback(self._handle_close)
            self._callback_registered = True
            LOGGER.debug("monitor.started", method="add_close_callback")
            return

        close_callbacks = getattr(self._connection, "close_callbacks", None)
        if close_callbacks is not None and hasattr(close_callbacks, "add"):
            close_callbacks.add(self._handle_close)
            self._callback_collection = close_callbacks
            self._callback_registered = True
            LOGGER.debug("monitor.started", method="close_callbacks")
            return

        LOGGER.warning("monitor.close_callback_missing")

    async def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        if self._callback_registered and self._callback_collection is not None:
            discard = getattr(self._callback_collection, "discard", None)
            if callable(discard):
                discard(self._handle_close)
        self._callback_collection = None
        self._callback_registered = False
        LOGGER.debug("monitor.stopped")

    def _handle_close(self, connection: AbstractConnection, exc: Exception | None) -> None:
        LOGGER.warning("connection.closed_by_server", exception=str(exc) if exc else None)
        if self._on_connection_lost is None:
            return

        asyncio.create_task(self._on_connection_lost())


__all__ = ["ConnectionMonitor"]
