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

"""MCP call-id tool dispatcher for topology list operations."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from config.settings import Settings
from tools.operations.bindings import (
    Binding,
    PaginatedBindingResponse,
    create_binding,
    delete_binding,
    list_bindings,
)
from tools.operations.exchanges import (
    Exchange,
    ExchangeOptions,
    PaginatedExchangeResponse,
    create_exchange,
    delete_exchange,
    list_exchanges,
)
from tools.operations.queues import (
    PaginatedQueueResponse,
    Queue,
    QueueOptions,
    create_queue,
    delete_queue,
    list_queues,
)
from utils.errors import RabbitMQError, format_error


class PaginationInput(BaseModel):
    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=50, ge=1, le=200)


class ConnectionParams(BaseModel):
    host: str
    user: str
    password: str
    port: int = 15672
    use_tls: bool = False
    connection_vhost: str = Field(default="/", alias="connection_vhost")
    vhost: str | None = None

    model_config = {"populate_by_name": True}


class QueueCreateInput(ConnectionParams):
    name: str
    durable: bool = False
    exclusive: bool = False
    auto_delete: bool = False
    arguments: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True, "extra": "forbid"}


class ExchangeCreateInput(ConnectionParams):
    name: str
    type: str
    durable: bool = False
    auto_delete: bool = False
    internal: bool = False
    arguments: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True, "extra": "forbid"}


class BindingCreateInput(ConnectionParams):
    exchange: str
    queue: str
    routing_key: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True, "extra": "forbid"}


class QueueDeleteInput(ConnectionParams):
    name: str
    force: bool = False

    model_config = {"populate_by_name": True, "extra": "forbid"}


class ExchangeDeleteInput(ConnectionParams):
    name: str

    model_config = {"populate_by_name": True, "extra": "forbid"}


class BindingDeleteInput(ConnectionParams):
    exchange: str
    queue: str
    properties_key: str

    model_config = {"populate_by_name": True, "extra": "forbid"}


ResponseModel = (
    PaginatedQueueResponse
    | PaginatedExchangeResponse
    | PaginatedBindingResponse
    | Queue
    | Exchange
    | Binding
    | dict[str, Any]
)


_LIST_HANDLERS: dict[str, Callable[..., ResponseModel]] = {
    "queues.list": list_queues,
    "exchanges.list": list_exchanges,
    "bindings.list": list_bindings,
}


def _build_settings(params: ConnectionParams) -> Settings:
    return Settings(
        host=params.host,
        port=params.port,
        user=params.user,
        password=params.password,
        vhost=params.connection_vhost,
        use_tls=params.use_tls,
    )


def call_id(
    endpoint_id: str,
    params: dict[str, Any] | None = None,
    pagination: dict[str, Any] | None = None,
) -> ResponseModel:
    handler = _LIST_HANDLERS.get(endpoint_id)
    if handler is not None:
        try:
            connection_params = ConnectionParams.model_validate(params or {})
            pagination_params = PaginationInput.model_validate(pagination or {})
        except ValidationError as exc:
            raise format_error(exc) from exc

        settings = _build_settings(connection_params)

        try:
            return handler(
                vhost=connection_params.vhost,
                page=pagination_params.page,
                pageSize=pagination_params.pageSize,
                settings=settings,
            )
        except RabbitMQError:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise format_error(exc) from exc

    if endpoint_id == "queues.create":
        try:
            payload = QueueCreateInput.model_validate(params or {})
        except ValidationError as exc:
            raise format_error(exc) from exc

        settings = _build_settings(payload)
        options = QueueOptions(
            durable=payload.durable,
            exclusive=payload.exclusive,
            auto_delete=payload.auto_delete,
            arguments=payload.arguments,
        )
        target_vhost = payload.vhost or payload.connection_vhost

        try:
            return create_queue(
                vhost=target_vhost,
                name=payload.name,
                options=options,
                settings=settings,
            )
        except RabbitMQError:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise format_error(exc) from exc

    if endpoint_id == "exchanges.create":
        try:
            payload = ExchangeCreateInput.model_validate(params or {})  # type: ignore[assignment]
        except ValidationError as exc:
            raise format_error(exc) from exc

        settings = _build_settings(payload)
        options = ExchangeOptions(  # type: ignore[assignment]
            durable=payload.durable,  # type: ignore[attr-defined]
            auto_delete=payload.auto_delete,
            internal=payload.internal,  # type: ignore[attr-defined]
            arguments=payload.arguments,
        )
        target_vhost = payload.vhost or payload.connection_vhost

        try:
            return create_exchange(
                vhost=target_vhost,
                name=payload.name,
                exchange_type=payload.type,  # type: ignore[attr-defined]
                options=options,  # type: ignore[arg-type]
                settings=settings,
            )
        except RabbitMQError:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise format_error(exc) from exc

    if endpoint_id == "bindings.create":
        try:
            payload = BindingCreateInput.model_validate(params or {})  # type: ignore[assignment]
        except ValidationError as exc:
            raise format_error(exc) from exc

        settings = _build_settings(payload)
        target_vhost = payload.vhost or payload.connection_vhost

        try:
            return create_binding(
                vhost=target_vhost,
                exchange=payload.exchange,  # type: ignore[attr-defined]
                queue=payload.queue,  # type: ignore[attr-defined]
                routing_key=payload.routing_key,  # type: ignore[attr-defined]
                args=payload.arguments,
                settings=settings,
            )
        except RabbitMQError:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise format_error(exc) from exc

    if endpoint_id == "queues.delete":
        try:
            payload = QueueDeleteInput.model_validate(params or {})  # type: ignore[assignment]
        except ValidationError as exc:
            raise format_error(exc) from exc

        settings = _build_settings(payload)
        target_vhost = payload.vhost or payload.connection_vhost

        try:
            return delete_queue(
                vhost=target_vhost,
                name=payload.name,
                force=payload.force,  # type: ignore[attr-defined]
                settings=settings,
            )
        except RabbitMQError:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise format_error(exc) from exc

    if endpoint_id == "exchanges.delete":
        try:
            payload = ExchangeDeleteInput.model_validate(params or {})  # type: ignore[assignment]
        except ValidationError as exc:
            raise format_error(exc) from exc

        settings = _build_settings(payload)
        target_vhost = payload.vhost or payload.connection_vhost

        try:
            return delete_exchange(
                vhost=target_vhost,
                name=payload.name,
                settings=settings,
            )
        except RabbitMQError:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise format_error(exc) from exc

    if endpoint_id == "bindings.delete":
        try:
            payload = BindingDeleteInput.model_validate(params or {})  # type: ignore[assignment]
        except ValidationError as exc:
            raise format_error(exc) from exc

        settings = _build_settings(payload)
        target_vhost = payload.vhost or payload.connection_vhost

        try:
            return delete_binding(
                vhost=target_vhost,
                exchange=payload.exchange,  # type: ignore[attr-defined]
                queue=payload.queue,  # type: ignore[attr-defined]
                properties_key=payload.properties_key,  # type: ignore[attr-defined]
                settings=settings,
            )
        except RabbitMQError:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise format_error(exc) from exc

    raise ValueError(f"Unsupported endpoint '{endpoint_id}'")


__all__ = ["call_id", "PaginationInput", "ConnectionParams"]
