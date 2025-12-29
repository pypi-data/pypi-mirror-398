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

"""Exchange list operation with client-side pagination."""

import logging as _stdlib_logging  # Import stdlib logging before anything else
from typing import Any

from pydantic import BaseModel, Field

from config.settings import Settings
from tools.operations.executor import RabbitMQExecutor
from utils.errors import ConflictError, NotFoundError
from utils.validation import validate_exchange_type, validate_name, validate_vhost_exists

try:
    from config.logging import get_logger
except Exception:  # pragma: no cover - fallback if logging setup fails

    def get_logger(name: str) -> Any:
        return _stdlib_logging.getLogger(name)  # type: ignore[attr-defined]


class Exchange(BaseModel):
    name: str
    vhost: str
    type: str
    durable: bool
    auto_delete: bool
    internal: bool
    arguments: dict[str, Any] = Field(default_factory=dict)
    bindings_count: int | None = None
    message_stats: dict[str, Any] | None = None

    model_config = {"extra": "ignore"}


class ExchangeOptions(BaseModel):
    durable: bool = False
    auto_delete: bool = False
    internal: bool = False
    arguments: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class PaginationMetadata(BaseModel):
    totalItems: int
    totalPages: int
    page: int
    pageSize: int
    hasNextPage: bool
    hasPreviousPage: bool


class PaginatedExchangeResponse(BaseModel):
    items: list[Exchange]
    pagination: PaginationMetadata


def list_exchanges(
    vhost: str | None = None,
    page: int = 1,
    pageSize: int = 50,
    *,
    settings: Settings | None = None,
) -> PaginatedExchangeResponse:
    logger = get_logger("exchange.list")
    if page < 1:
        raise ValueError("page must be >= 1")
    if not (1 <= pageSize <= 200):
        raise ValueError("pageSize must be between 1 and 200")

    settings = settings or Settings.from_yaml()
    timeout = getattr(settings, "list_timeout", getattr(settings, "crud_timeout", 30))
    executor = RabbitMQExecutor(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        vhost=settings.vhost,
        use_tls=settings.use_tls,
        timeout=timeout,
    )

    target_vhost = vhost if vhost is not None else executor.vhost
    validate_vhost_exists(target_vhost, executor)

    logger.debug("Fetching exchanges for vhost %s", target_vhost)
    all_exchanges = executor.get_exchanges(vhost)
    total_items = len(all_exchanges)
    total_pages = max(1, (total_items + pageSize - 1) // pageSize) if total_items else 1
    start = (page - 1) * pageSize
    end = start + pageSize
    paged_exchanges = all_exchanges[start:end]

    items = [Exchange(**exchange) for exchange in paged_exchanges]
    pagination = PaginationMetadata(
        totalItems=total_items,
        totalPages=total_pages,
        page=page,
        pageSize=pageSize,
        hasNextPage=page < total_pages,
        hasPreviousPage=page > 1,
    )

    logger.debug(
        "Returning %s exchanges (page %s/%s)",
        len(items),
        page,
        total_pages,
    )
    return PaginatedExchangeResponse(items=items, pagination=pagination)


def create_exchange(
    vhost: str | None,
    name: str,
    exchange_type: str,
    options: ExchangeOptions,
    *,
    settings: Settings | None = None,
) -> Exchange:
    """Create an exchange with validation and audit logging."""

    logger = get_logger("exchange.create")
    settings = settings or Settings.from_yaml()
    timeout = getattr(settings, "crud_timeout", getattr(settings, "list_timeout", 5))
    executor = RabbitMQExecutor(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        vhost=settings.vhost,
        use_tls=settings.use_tls,
        timeout=timeout,
    )

    target_vhost = vhost if vhost is not None else executor.vhost
    validate_vhost_exists(target_vhost, executor)
    validate_name(name)
    validate_exchange_type(exchange_type)

    payload = {
        "type": exchange_type,
        **options.model_dump(exclude_none=True),
    }

    try:
        executor.create_exchange(target_vhost, name, payload)
    except ConflictError as exc:
        context = {"vhost": target_vhost, "exchange": name}
        context.update(getattr(exc, "context", {}))
        raise ConflictError(
            code="EXCHANGE_ALREADY_EXISTS",
            message=f"Exchange '{name}' already exists in vhost '{target_vhost}'",
            action="Choose a different exchange name or delete the existing exchange",
            context=context,
        ) from exc

    try:
        exchange_data = executor.get_exchange(target_vhost, name) or {}
    except NotFoundError:
        exchange_data = {}

    enriched: dict[str, Any] = {
        "name": name,
        "vhost": target_vhost,
        **payload,
        **exchange_data,
    }

    audit_fields = {
        "operation": "exchange.create",
        "vhost": target_vhost,
        "exchange_name": name,
        "type": exchange_type,
        "user": settings.user,
        "result": "success",
    }
    if hasattr(logger, "bind"):
        logger.info("exchange.create.success", **audit_fields)
    else:  # pragma: no cover - fallback for plain logging
        logger.info(
            "exchange.create.success operation=%s vhost=%s exchange=%s type=%s user=%s result=%s",
            audit_fields["operation"],
            audit_fields["vhost"],
            audit_fields["exchange_name"],
            audit_fields["type"],
            audit_fields["user"],
            audit_fields["result"],
        )

    return Exchange(**enriched)


def validate_exchange_delete(
    vhost: str,
    name: str,
    *,
    settings: Settings | None = None,
    executor: RabbitMQExecutor | None = None,
) -> dict[str, Any]:
    """Ensure exchanges are safe to delete according to spec requirements."""

    logger = get_logger("exchange.delete.validate")

    if name == "" or name.startswith("amq."):
        raise ConflictError(
            code="SYSTEM_EXCHANGE",
            message=f"Exchange '{name or '<default>'}' is managed by RabbitMQ and cannot be deleted.",
            action="Choose a user-defined exchange for deletion",
            context={"vhost": vhost, "exchange": name or ""},
        )

    validate_name(name)

    settings = settings or Settings.from_yaml()
    timeout = getattr(settings, "crud_timeout", getattr(settings, "list_timeout", 5))
    client = executor or RabbitMQExecutor(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        vhost=settings.vhost,
        use_tls=settings.use_tls,
        timeout=timeout,
    )

    validate_vhost_exists(vhost, client)

    try:
        exchange_data = client.get_exchange(vhost, name) or {}
    except NotFoundError as exc:
        raise NotFoundError(
            code="EXCHANGE_NOT_FOUND",
            message=f"Exchange '{name}' was not found in vhost '{vhost}'",
            action="Verify the exchange name and virtual host before retrying",
            context={"vhost": vhost, "exchange": name},
        ) from exc

    bindings = client.get_bindings_for_exchange(vhost, name) or []
    binding_count = len(bindings)
    if binding_count > 0:
        preview = [
            {
                "destination": binding.get("destination"),
                "destination_type": binding.get("destination_type"),
                "routing_key": binding.get("routing_key", ""),
            }
            for binding in bindings[:5]
        ]
        raise ConflictError(
            code="EXCHANGE_HAS_BINDINGS",
            message=(
                f"Exchange '{name}' has {binding_count} binding(s) and must be detached before deletion."
            ),
            action="Remove bindings first using 'binding delete' before retrying",
            context={
                "vhost": vhost,
                "exchange": name,
                "binding_count": binding_count,
                "sample_bindings": preview,
            },
        )

    if hasattr(logger, "bind"):
        logger.debug("exchange.delete.validation.pass", vhost=vhost, exchange=name)
    else:  # pragma: no cover - fallback for plain logging
        logger.debug(
            "exchange.delete.validation.pass vhost=%s exchange=%s",
            vhost,
            name,
        )

    return {
        "exchange": exchange_data,
        "binding_count": binding_count,
    }


def delete_exchange(
    vhost: str | None,
    name: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Delete an exchange after validating safety conditions."""

    logger = get_logger("exchange.delete")
    settings = settings or Settings.from_yaml()
    timeout = getattr(settings, "crud_timeout", getattr(settings, "list_timeout", 5))
    executor = RabbitMQExecutor(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        vhost=settings.vhost,
        use_tls=settings.use_tls,
        timeout=timeout,
    )

    target_vhost = vhost if vhost is not None else executor.vhost
    validation_context = validate_exchange_delete(
        target_vhost,
        name,
        settings=settings,
        executor=executor,
    )

    executor.delete_exchange(target_vhost, name)

    audit_fields = {
        "operation": "exchange.delete",
        "vhost": target_vhost,
        "exchange_name": name,
        "user": settings.user,
        "result": "success",
    }
    if hasattr(logger, "bind"):
        logger.info("exchange.delete.success", **audit_fields)
    else:  # pragma: no cover - fallback for plain logging
        logger.info(
            "exchange.delete.success operation=%s vhost=%s exchange=%s user=%s result=%s",
            audit_fields["operation"],
            audit_fields["vhost"],
            audit_fields["exchange_name"],
            audit_fields["user"],
            audit_fields["result"],
        )

    return {
        "status": "deleted",
        "operation": "exchange.delete",
        "exchange": name,
        "vhost": target_vhost,
        "binding_count": validation_context.get("binding_count", 0),
    }


__all__ = [
    "Exchange",
    "ExchangeOptions",
    "PaginatedExchangeResponse",
    "create_exchange",
    "delete_exchange",
    "list_exchanges",
    "validate_exchange_delete",
]
