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

"""Binding list operation implementing client-side pagination."""

import logging as _stdlib_logging  # Import stdlib logging before anything else
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from pydantic import BaseModel, Field

from config.settings import Settings
from tools.operations.executor import RabbitMQExecutor
from utils.errors import ConflictError, NotFoundError, ValidationError
from utils.validation import validate_routing_key, validate_vhost_exists

try:  # pragma: no cover - fallback for logging import failures
    from config.logging import get_logger
except Exception:  # pragma: no cover - testing fallback

    def get_logger(name: str) -> Any:
        return _stdlib_logging.getLogger(name)  # type: ignore[attr-defined]


class Binding(BaseModel):
    source: str
    destination: str
    destination_type: str
    vhost: str
    routing_key: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)
    properties_key: str | None = None

    model_config = {"extra": "ignore"}


class PaginationMetadata(BaseModel):
    totalItems: int
    totalPages: int
    page: int
    pageSize: int
    hasNextPage: bool
    hasPreviousPage: bool


class PaginatedBindingResponse(BaseModel):
    items: list[Binding]
    pagination: PaginationMetadata


def list_bindings(
    vhost: str | None = None,
    page: int = 1,
    pageSize: int = 50,
    *,
    settings: Settings | None = None,
) -> PaginatedBindingResponse:
    logger = get_logger("binding.list")
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

    logger.debug("Fetching bindings for vhost %s", target_vhost if vhost is not None else "*")
    all_bindings = executor.get_bindings(vhost)
    total_items = len(all_bindings)
    total_pages = max(1, (total_items + pageSize - 1) // pageSize) if total_items else 1
    start = (page - 1) * pageSize
    end = start + pageSize
    paged_bindings = all_bindings[start:end]

    items = [Binding(**binding) for binding in paged_bindings]
    pagination = PaginationMetadata(
        totalItems=total_items,
        totalPages=total_pages,
        page=page,
        pageSize=pageSize,
        hasNextPage=page < total_pages,
        hasPreviousPage=page > 1,
    )

    logger.debug(
        "Returning %s bindings (page %s/%s)",
        len(items),
        page,
        total_pages,
    )
    return PaginatedBindingResponse(items=items, pagination=pagination)


def create_binding(
    vhost: str | None,
    exchange: str,
    queue: str,
    routing_key: str | None,
    args: dict[str, Any] | None,
    *,
    settings: Settings | None = None,
) -> Binding:
    """Create a binding between an exchange and a queue."""

    logger = get_logger("binding.create")
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

    exchange_data: dict[str, Any] | None = None
    missing_resources: list[str] = []

    def _fetch_exchange() -> dict[str, Any]:
        return executor.get_exchange(target_vhost, exchange)

    def _fetch_queue() -> dict[str, Any]:
        return executor.get_queue(target_vhost, queue)

    with ThreadPoolExecutor(max_workers=2) as pool:
        future_exchange = pool.submit(_fetch_exchange)
        future_queue = pool.submit(_fetch_queue)
        try:
            exchange_data = future_exchange.result()
        except NotFoundError:
            missing_resources.append("exchange")
        except ConflictError:
            raise
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise exc

        try:
            _ = future_queue.result()  # Only check if it succeeds
        except NotFoundError:
            missing_resources.append("queue")
        except ConflictError:
            raise
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise exc

    if len(missing_resources) == 2:
        raise NotFoundError(
            code="RESOURCES_NOT_FOUND",
            message=(
                f"Exchange '{exchange}' and queue '{queue}' do not exist in vhost '{target_vhost}'"
            ),
            action="Create the exchange and queue before creating a binding",
            context={
                "vhost": target_vhost,
                "exchange": exchange,
                "queue": queue,
                "missing": missing_resources,
            },
        )
    if missing_resources:
        missing = missing_resources[0]
        code = "EXCHANGE_NOT_FOUND" if missing == "exchange" else "QUEUE_NOT_FOUND"
        message = (
            f"Exchange '{exchange}' was not found in vhost '{target_vhost}'"
            if missing == "exchange"
            else f"Queue '{queue}' was not found in vhost '{target_vhost}'"
        )
        action = (
            "Create the exchange before binding it to queues"
            if missing == "exchange"
            else "Create the queue before binding exchanges to it"
        )
        raise NotFoundError(
            code=code,
            message=message,
            action=action,
            context={
                "vhost": target_vhost,
                "exchange": exchange,
                "queue": queue,
            },
        )

    exchange_type = (exchange_data or {}).get("type", "")
    validate_routing_key(routing_key or "", exchange_type)

    normalized_routing_key = routing_key or ""
    normalized_arguments = args or {}

    context_seed = {
        "vhost": target_vhost,
        "exchange": exchange,
        "queue": queue,
        "routing_key": normalized_routing_key,
    }

    def _raise_duplicate_conflict(exc: Exception | None = None) -> None:
        context: dict[str, Any] = dict(context_seed)
        if exc is not None:
            context.update(getattr(exc, "context", {}))
        raise ConflictError(
            code="BINDING_ALREADY_EXISTS",
            message="A binding with the same routing key already exists",
            action="Adjust the routing key or arguments to create a distinct binding",
            context=context,
        ) from exc

    try:
        existing_bindings = executor.list_binding_relations(target_vhost, exchange, queue) or []
    except NotFoundError:
        existing_bindings = []

    for existing in existing_bindings:
        existing_arguments = existing.get("arguments") or {}
        if (
            existing.get("routing_key", "") == normalized_routing_key
            and existing_arguments == normalized_arguments
        ):
            _raise_duplicate_conflict()

    payload = {
        "routing_key": normalized_routing_key,
        "arguments": normalized_arguments,
    }

    try:
        executor.create_binding(target_vhost, exchange, queue, payload)
    except ConflictError as exc:
        _raise_duplicate_conflict(exc)

    try:
        binding_list = executor.list_binding_relations(target_vhost, exchange, queue) or []
    except NotFoundError:
        binding_list = []

    selected = None
    for candidate in binding_list:
        if (
            candidate.get("routing_key", "") == (routing_key or "")
            and candidate.get("destination") == queue
        ):
            selected = candidate
            break

    binding_data: dict[str, Any] = selected or {
        "source": exchange,
        "destination": queue,
        "destination_type": "queue",
        "vhost": target_vhost,
        "routing_key": routing_key or "",
        "arguments": args or {},
    }

    audit_fields = {
        "operation": "binding.create",
        "vhost": target_vhost,
        "exchange": exchange,
        "queue": queue,
        "routing_key": routing_key or "",
        "user": settings.user,
        "result": "success",
    }
    if hasattr(logger, "bind"):
        logger.info("binding.create.success", **audit_fields)
    else:  # pragma: no cover - fallback for plain logging
        logger.info(
            "binding.create.success operation=%s vhost=%s exchange=%s queue=%s routing_key=%s user=%s result=%s",
            audit_fields["operation"],
            audit_fields["vhost"],
            audit_fields["exchange"],
            audit_fields["queue"],
            audit_fields["routing_key"],
            audit_fields["user"],
            audit_fields["result"],
        )

    return Binding(**binding_data)


def delete_binding(
    vhost: str | None,
    exchange: str,
    queue: str,
    properties_key: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Delete a specific binding between an exchange and a queue."""

    logger = get_logger("binding.delete")
    if properties_key is None:
        raise ValidationError(
            code="MISSING_PROPERTIES_KEY",
            message="Binding deletion requires the properties key returned by RabbitMQ.",
            action="Pass the value from the binding list output (properties_key field)",
            context={"exchange": exchange, "queue": queue},
        )

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

    try:
        executor.delete_binding(target_vhost, exchange, queue, properties_key)
    except NotFoundError as exc:
        raise NotFoundError(
            code="BINDING_NOT_FOUND",
            message=(
                f"Binding from exchange '{exchange}' to queue '{queue}' with key '{properties_key}' was not found."
            ),
            action="Refresh the bindings list and provide the latest properties key before retrying",
            context={
                "vhost": target_vhost,
                "exchange": exchange,
                "queue": queue,
                "properties_key": properties_key,
            },
        ) from exc

    audit_fields = {
        "operation": "binding.delete",
        "vhost": target_vhost,
        "exchange": exchange,
        "queue": queue,
        "properties_key": properties_key,
        "user": settings.user,
        "result": "success",
    }
    if hasattr(logger, "bind"):
        logger.info("binding.delete.success", **audit_fields)
    else:  # pragma: no cover - fallback for plain logging
        logger.info(
            "binding.delete.success operation=%s vhost=%s exchange=%s queue=%s properties_key=%s user=%s result=%s",
            audit_fields["operation"],
            audit_fields["vhost"],
            audit_fields["exchange"],
            audit_fields["queue"],
            audit_fields["properties_key"],
            audit_fields["user"],
            audit_fields["result"],
        )

    return {
        "status": "deleted",
        "operation": "binding.delete",
        "exchange": exchange,
        "queue": queue,
        "vhost": target_vhost,
        "properties_key": properties_key,
    }


__all__ = [
    "Binding",
    "PaginatedBindingResponse",
    "create_binding",
    "delete_binding",
    "list_bindings",
]
