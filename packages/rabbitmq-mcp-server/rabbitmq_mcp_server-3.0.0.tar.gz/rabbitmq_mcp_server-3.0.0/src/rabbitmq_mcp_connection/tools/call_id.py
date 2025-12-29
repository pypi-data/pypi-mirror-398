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

"""Despachante para o MCP call-id tool."""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from rabbitmq_mcp_connection.connection.config import load_config
from rabbitmq_mcp_connection.connection.exceptions import (
    AuthenticationError,
    ConnectionError,
    ConnectionTimeoutError,
    VHostNotFoundError,
)
from rabbitmq_mcp_connection.connection.health import HealthChecker
from rabbitmq_mcp_connection.connection.manager import ConnectionManager
from rabbitmq_mcp_connection.connection.pool import ConnectionPool
from rabbitmq_mcp_connection.logging.config import get_logger
from rabbitmq_mcp_connection.schemas.connection import (
    ConnectionConfig,
    ConnectResult,
    DisconnectResult,
    HealthStatus,
    PoolStats,
)
from rabbitmq_mcp_connection.schemas.mcp import MCPError, MCPToolResult
from rabbitmq_mcp_connection.tools.contracts import load_connection_operations

LOGGER = get_logger(__name__)


class ToolState:
    def __init__(self) -> None:
        self._config: ConnectionConfig | None = None
        self._manager: ConnectionManager | None = None
        self._health_checker: HealthChecker | None = None
        self._pool: ConnectionPool | None = None

    async def get_manager(self, overrides: dict[str, Any] | None = None) -> ConnectionManager:
        config = self._resolve_config(overrides or {})
        if self._manager is None:
            self._manager = ConnectionManager(config)
            self._config = config
            self._health_checker = HealthChecker(self._manager)
            return self._manager

        if self._config != config:
            await self._manager.disconnect()
            self._manager = ConnectionManager(config)
            self._config = config
            self._health_checker = HealthChecker(self._manager)
        return self._manager

    def get_health_checker(self, manager: ConnectionManager) -> HealthChecker:
        if self._health_checker is None or self._manager is not manager:
            self._health_checker = HealthChecker(manager)
        return self._health_checker

    def get_pool(self, config: ConnectionConfig) -> ConnectionPool:
        if self._pool is None or self._config != config:
            self._pool = ConnectionPool(config)
        return self._pool

    def peek_manager(self) -> ConnectionManager | None:
        return self._manager

    def _resolve_config(self, overrides: dict[str, Any]) -> ConnectionConfig:
        try:
            config = load_config(**overrides)
        except ValidationError as exc:
            raise ValueError(exc.errors()) from exc
        return config


_STATE = ToolState()
_OPERATIONS = load_connection_operations()


def _error(code: str, message: str, details: dict[str, Any] | None = None) -> MCPToolResult:
    return MCPToolResult(success=False, error=MCPError(code=code, message=message, details=details))


async def handle_call_id(operation_id: str, payload: dict[str, Any] | None = None) -> MCPToolResult:
    if operation_id not in _OPERATIONS:
        return _error("UNKNOWN_OPERATION", f"Operação não suportada: {operation_id}")

    payload = payload or {}

    handlers: dict[str, Callable[[dict[str, Any]], Awaitable[MCPToolResult]]] = {
        "connection.connect": _handle_connect,
        "connection.disconnect": _handle_disconnect,
        "connection.health_check": _handle_health_check,
        "connection.get_status": _handle_get_status,
        "pool.get_stats": _handle_pool_stats,
    }

    handler = handlers.get(operation_id)
    if handler is None:
        return _error("NOT_IMPLEMENTED", f"Handler não implementado para {operation_id}")

    try:
        return await handler(payload)
    except ValueError as exc:
        return _error("INVALID_PAYLOAD", "Dados inválidos", details={"errors": str(exc)})
    except ConnectionTimeoutError as exc:
        return _error("CONNECTION_TIMEOUT", str(exc))
    except AuthenticationError as exc:
        return _error("AUTHENTICATION_FAILED", str(exc))
    except VHostNotFoundError as exc:
        return _error("VHOST_NOT_FOUND", str(exc))
    except ConnectionError as exc:
        return _error("CONNECTION_ERROR", str(exc))
    except Exception as exc:  # pragma: no cover - proteção geral
        LOGGER.exception("call_id.unhandled_exception", operation=operation_id)
        return _error("INTERNAL_ERROR", "Unexpected error", details={"error": str(exc)})


async def _handle_connect(payload: dict[str, Any]) -> MCPToolResult:
    manager = await _STATE.get_manager(payload)
    start = time.perf_counter()
    await manager.connect()
    latency_ms = (time.perf_counter() - start) * 1000

    result = ConnectResult(
        connected=manager.state.is_connected,
        connection_url=manager.config.get_connection_url(),
        latency_ms=latency_ms,
        server_properties=getattr(manager.connection, "server_properties", None),
    )
    return MCPToolResult(success=True, result=result.model_dump())


async def _handle_disconnect(payload: dict[str, Any]) -> MCPToolResult:
    manager = _STATE.peek_manager()
    if manager is None or not manager.state.is_connected:
        return _error("NOT_CONNECTED", "Nenhuma conexão ativa para desconectar")

    force = bool(payload.get("force", False))
    if force:
        if manager.connection and not manager.connection.is_closed:
            await manager.connection.close()
    start = time.perf_counter()
    await manager.disconnect()
    duration_ms = (time.perf_counter() - start) * 1000
    result = DisconnectResult(disconnected=True, graceful=not force, duration_ms=duration_ms)
    return MCPToolResult(success=True, result=result.model_dump())


async def _handle_health_check(payload: dict[str, Any]) -> MCPToolResult:
    manager = await _STATE.get_manager({})
    checker = _STATE.get_health_checker(manager)
    status: HealthStatus = await checker.check_health()
    return MCPToolResult(success=True, result=status.model_dump())


async def _handle_get_status(payload: dict[str, Any]) -> MCPToolResult:
    manager = await _STATE.get_manager({})
    status = await manager.get_status()
    return MCPToolResult(success=True, result=status.model_dump())


async def _handle_pool_stats(payload: dict[str, Any]) -> MCPToolResult:
    manager = await _STATE.get_manager({})
    pool = _STATE.get_pool(manager.config)
    stats: PoolStats = await pool.get_stats()
    return MCPToolResult(success=True, result=stats.model_dump())


def reset_tool_state() -> None:
    """Reinicia o estado global (útil em testes)."""

    global _STATE
    _STATE = ToolState()


__all__ = ["handle_call_id", "reset_tool_state"]
