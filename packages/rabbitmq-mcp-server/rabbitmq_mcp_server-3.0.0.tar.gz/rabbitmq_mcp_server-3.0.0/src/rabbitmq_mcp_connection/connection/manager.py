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

"""Gerenciador principal de conexões AMQP usando aio-pika."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from rabbitmq_mcp_connection.connection.aio_pika_compat import (
    AbstractChannel,
    RobustConnection,
    aio_pika,
)
from rabbitmq_mcp_connection.connection.exceptions import (
    AuthenticationError,
    ConnectionError,
    ConnectionTimeoutError,
    VHostNotFoundError,
)
from rabbitmq_mcp_connection.connection.monitor import ConnectionMonitor
from rabbitmq_mcp_connection.logging.config import get_logger
from rabbitmq_mcp_connection.schemas.connection import (
    ConnectionConfig,
    ConnectionState,
    ConnectionStatusResult,
)
from rabbitmq_mcp_connection.schemas.retry import RetryPolicy

logger = get_logger(__name__)


@dataclass(slots=True)
class ConnectionMetadata:
    """Metadados sobre a conexão atual."""

    connected_since: datetime | None = None
    server_properties: dict[str, Any] | None = None


class ConnectionManager:
    """Gerencia conexão AMQP e reconexões automáticas."""

    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config
        self.connection: RobustConnection | None = None
        self.channel: AbstractChannel | None = None
        self.state = ConnectionState.DISCONNECTED
        self.retry_policy = RetryPolicy()
        self._lock = asyncio.Lock()
        self._metadata = ConnectionMetadata()
        self._reconnect_task: asyncio.Task[None] | None = None
        self.monitor: ConnectionMonitor | None = None
        self._reconnect_callback_registered = False

    async def connect(self) -> None:
        """Estabelece uma conexão AMQP seguindo FR-001..FR-012."""

        async with self._lock:
            if self.state == ConnectionState.CONNECTED:
                return

            self.state = ConnectionState.CONNECTING
            logger.info(
                "connection.connecting",
                host=self.config.host,
                port=self.config.port,
                vhost=self.config.vhost,
            )

            try:
                self.connection = cast(
                    RobustConnection,
                    await asyncio.wait_for(
                        aio_pika.connect_robust(
                            host=self.config.host,
                            port=self.config.port,
                            login=self.config.user,
                            password=self.config.password,
                            virtualhost=self.config.vhost,
                            heartbeat=self.config.heartbeat,
                            timeout=self.config.timeout,
                        ),
                        timeout=self.config.timeout,
                    ),
                )
                self._reconnect_callback_registered = False
            except TimeoutError as exc:  # pragma: no cover - requires real broker
                self.state = ConnectionState.FAILED
                raise ConnectionTimeoutError("Tempo limite excedido ao conectar") from exc
            except aio_pika.exceptions.ProbableAuthenticationError as exc:
                self.state = ConnectionState.FAILED
                raise AuthenticationError("Credenciais inválidas para RabbitMQ") from exc
            except Exception as exc:  # pragma: no cover - erros externos
                self.state = ConnectionState.FAILED
                message = str(exc)
                if "not_allowed" in message.lower() or "vhost" in message.lower():
                    raise VHostNotFoundError(f"VHost não encontrado: {self.config.vhost}") from exc
                raise ConnectionError("Falha ao estabelecer conexão") from exc

            assert self.connection is not None
            self.channel = await self.connection.channel()  # canal default
            self.state = ConnectionState.CONNECTED
            self.retry_policy.reset()
            self._metadata.connected_since = datetime.now(UTC)
            self._metadata.server_properties = getattr(self.connection, "server_properties", None)

            if self.monitor is not None:
                await self.monitor.stop()
            if self.connection is not None:
                self.monitor = ConnectionMonitor(
                    self.connection,
                    on_connection_lost=self._handle_connection_lost,
                )
                await self.monitor.start()
                self._register_reconnect_callback()

            logger.info(
                "connection.established",
                host=self.config.host,
                port=self.config.port,
                vhost=self.config.vhost,
                connection_url=self.config.get_connection_url(),
            )

    async def disconnect(self) -> None:
        """Desconecta graciosamente fechando recursos conforme FR-007."""

        async with self._lock:
            if self.state == ConnectionState.DISCONNECTED:
                return

            logger.info("connection.disconnecting")

            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()
                self._reconnect_task = None

            if self.monitor is not None:
                await self.monitor.stop()
                self.monitor = None

            self._unregister_reconnect_callback()

            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            if self.connection and not self.connection.is_closed:
                await self.connection.close()

            self.channel = None
            self.connection = None
            self.state = ConnectionState.DISCONNECTED
            self._metadata = ConnectionMetadata()
            self._reconnect_callback_registered = False

            logger.info("connection.disconnected")

    async def get_status(self) -> ConnectionStatusResult:
        """Retorna informações sobre a conexão atual (FR-009)."""

        return ConnectionStatusResult(
            state=self.state,
            connection_url=self.config.get_connection_url(),
            connected_since=self._metadata.connected_since,
            retry_attempts=self.retry_policy.attempts,
            next_retry_in_seconds=(
                self.retry_policy.current_delay
                if self.state == ConnectionState.RECONNECTING
                else None
            ),
        )

    async def ensure_connected(self) -> None:
        """Garante que a conexão está ativa, reconectando se necessário."""

        if self.state == ConnectionState.CONNECTED:
            return
        await self.connect()

    async def reconnect(self) -> None:
        """Inicia processo de reconexão com backoff exponencial (FR-011)."""

        async with self._lock:
            if self.state == ConnectionState.RECONNECTING:
                return
            self.state = ConnectionState.RECONNECTING
            self.retry_policy.reset()

        logger.warning("connection.reconnecting", host=self.config.host)

        while True:
            try:
                await self.connect()
                logger.info("connection.reconnected")
                return
            except ConnectionError as exc:
                delay = self.retry_policy.next_delay()
                logger.error(
                    "connection.retry_failed",
                    error=str(exc),
                    attempt=self.retry_policy.attempts,
                    next_retry=delay,
                )
                await asyncio.sleep(delay)

    def schedule_reconnect(self) -> None:
        """Agenda reconexão em segundo plano."""

        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self.reconnect())

    async def _handle_connection_lost(self) -> None:
        logger.warning("connection.lost", host=self.config.host)
        monitor_to_stop: ConnectionMonitor | None = None
        async with self._lock:
            if self.state == ConnectionState.RECONNECTING:
                return
            monitor_to_stop = self.monitor
            self.state = ConnectionState.RECONNECTING
            self.channel = None
            self.monitor = None
            self._metadata.connected_since = None

        if monitor_to_stop is not None:
            await monitor_to_stop.stop()
        self._register_reconnect_callback()

    @asynccontextmanager
    async def channel_context(self) -> AsyncIterator[AbstractChannel]:
        """Context manager para uso seguro do canal."""

        await self.ensure_connected()
        assert self.channel is not None
        yield self.channel

    def __repr__(self) -> str:  # pragma: no cover - repr simples
        return f"ConnectionManager(state={self.state.value}, config={self.config!r})"

    def _register_reconnect_callback(self) -> None:
        if self.connection is None or self._reconnect_callback_registered:
            return
        callbacks = getattr(self.connection, "reconnect_callbacks", None)
        if callbacks is None or not hasattr(callbacks, "add"):
            logger.debug("connection.reconnect_callback_missing")
            return
        callbacks.add(self._on_connection_reconnected)
        self._reconnect_callback_registered = True

    def _unregister_reconnect_callback(self) -> None:
        if self.connection is None or not self._reconnect_callback_registered:
            return
        callbacks = getattr(self.connection, "reconnect_callbacks", None)
        if callbacks is not None and hasattr(callbacks, "discard"):
            callbacks.discard(self._on_connection_reconnected)
        self._reconnect_callback_registered = False

    async def _on_connection_reconnected(self, *_: Any, **__: Any) -> None:
        logger.info("connection.reconnected")
        new_monitor: ConnectionMonitor | None = None
        async with self._lock:
            if self.connection is None:
                return

            try:
                self.channel = await self.connection.channel()
            except Exception as exc:  # pragma: no cover - depende do broker real
                logger.error("connection.reconnect_channel_failed", error=str(exc))
                self.channel = None
                return

            self.state = ConnectionState.CONNECTED
            self.retry_policy.reset()
            self._metadata.connected_since = datetime.now(UTC)
            self._metadata.server_properties = getattr(self.connection, "server_properties", None)

            new_monitor = ConnectionMonitor(
                self.connection,
                on_connection_lost=self._handle_connection_lost,
            )
            self.monitor = new_monitor

        if new_monitor is not None:
            await new_monitor.start()
