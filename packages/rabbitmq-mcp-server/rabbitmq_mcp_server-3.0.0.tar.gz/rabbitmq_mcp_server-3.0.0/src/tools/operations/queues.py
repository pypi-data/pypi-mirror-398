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

"""Queue list operation implementing client-side pagination."""

import logging as _stdlib_logging  # Import stdlib logging before anything else
from typing import Any

from pydantic import BaseModel, Field

from config.settings import Settings
from tools.operations.executor import RabbitMQExecutor
from utils.errors import ConflictError, NotFoundError
from utils.validation import validate_name, validate_vhost_exists

try:
    from config.logging import get_logger
except Exception:  # pragma: no cover - fallback if logging setup fails

    def get_logger(name: str) -> Any:
        return _stdlib_logging.getLogger(name)  # type: ignore[attr-defined]


class Queue(BaseModel):
    name: str
    vhost: str
    durable: bool
    auto_delete: bool
    exclusive: bool
    arguments: dict[str, Any] = Field(default_factory=dict)
    messages: int = 0
    messages_ready: int = 0
    messages_unacknowledged: int = 0
    consumers: int = 0
    memory: int | None = None
    state: str | None = None

    model_config = {"extra": "ignore"}


class QueueOptions(BaseModel):
    durable: bool = False
    exclusive: bool = False
    auto_delete: bool = False
    arguments: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class PaginationMetadata(BaseModel):
    totalItems: int
    totalPages: int
    page: int
    pageSize: int
    hasNextPage: bool
    hasPreviousPage: bool


class PaginatedQueueResponse(BaseModel):
    items: list[Queue]
    pagination: PaginationMetadata


def list_queues(
    vhost: str | None = None,
    page: int = 1,
    pageSize: int = 50,
    *,
    settings: Settings | None = None,
) -> PaginatedQueueResponse:
    logger = get_logger("queue.list")
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

    logger.debug("Fetching queues for vhost %s", target_vhost)
    all_queues = executor.get_queues(vhost)
    total_items = len(all_queues)
    total_pages = max(1, (total_items + pageSize - 1) // pageSize) if total_items else 1
    start = (page - 1) * pageSize
    end = start + pageSize
    paged_queues = all_queues[start:end]

    items = [Queue(**queue) for queue in paged_queues]
    pagination = PaginationMetadata(
        totalItems=total_items,
        totalPages=total_pages,
        page=page,
        pageSize=pageSize,
        hasNextPage=page < total_pages,
        hasPreviousPage=page > 1,
    )

    logger.debug(
        "Returning %s queues (page %s/%s)",
        len(items),
        page,
        total_pages,
    )
    return PaginatedQueueResponse(items=items, pagination=pagination)


def create_queue(
    vhost: str | None,
    name: str,
    options: QueueOptions,
    *,
    settings: Settings | None = None,
) -> Queue:
    """Create a queue after validating inputs and record audit logs."""

    logger = get_logger("queue.create")
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

    payload = options.model_dump(exclude_none=True)

    try:
        executor.create_queue(target_vhost, name, payload)
    except ConflictError as exc:
        context = {"vhost": target_vhost, "queue": name}
        context.update(getattr(exc, "context", {}))
        raise ConflictError(
            code="QUEUE_ALREADY_EXISTS",
            message=f"Queue '{name}' already exists in vhost '{target_vhost}'",
            action="Choose a different queue name or delete the existing queue",
            context=context,
        ) from exc

    try:
        queue_data = executor.get_queue(target_vhost, name) or {}
    except NotFoundError:
        queue_data = {}

    enriched: dict[str, Any] = {
        "name": name,
        "vhost": target_vhost,
        **payload,
        **queue_data,
    }

    audit_fields = {
        "operation": "queue.create",
        "vhost": target_vhost,
        "queue_name": name,
        "user": settings.user,
        "result": "success",
    }
    if hasattr(logger, "bind"):
        logger.info("queue.create.success", **audit_fields)
    else:  # pragma: no cover - fallback for plain logging
        logger.info(
            "queue.create.success operation=%s vhost=%s queue=%s user=%s result=%s",
            audit_fields["operation"],
            audit_fields["vhost"],
            audit_fields["queue_name"],
            audit_fields["user"],
            audit_fields["result"],
        )

    return Queue(**enriched)


def validate_queue_delete(
    vhost: str,
    name: str,
    force: bool,
    *,
    settings: Settings | None = None,
    executor: RabbitMQExecutor | None = None,
) -> dict[str, Any]:
    """Ensure queue deletion obeys safety requirements before proceeding."""

    logger = get_logger("queue.delete.validate")
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
        queue_data = client.get_queue(vhost, name) or {}
    except NotFoundError as exc:
        raise NotFoundError(
            code="QUEUE_NOT_FOUND",
            message=f"Queue '{name}' was not found in vhost '{vhost}'",
            action="Confirm the queue name and virtual host before retrying",
            context={"vhost": vhost, "queue": name},
        ) from exc

    messages = int(queue_data.get("messages", 0) or 0)
    if messages > 0 and not force:
        raise ConflictError(
            code="QUEUE_NOT_EMPTY",
            message=(
                f"Queue '{name}' contains {messages} messages and cannot be deleted without the --force flag."
            ),
            action="Drain or re-route the messages, or rerun with --force to confirm deletion",
            context={"vhost": vhost, "queue": name, "messages": messages},
        )

    if hasattr(logger, "bind"):
        logger.debug("queue.delete.validation.pass", vhost=vhost, queue=name, force=force)
    else:  # pragma: no cover - fallback for plain logging
        logger.debug(
            "queue.delete.validation.pass vhost=%s queue=%s force=%s",
            vhost,
            name,
            force,
        )
    return queue_data


def delete_queue(
    vhost: str | None,
    name: str,
    force: bool = False,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Delete a queue after enforcing safety checks and emit audit logs."""

    logger = get_logger("queue.delete")
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
    queue_snapshot = validate_queue_delete(
        target_vhost,
        name,
        force,
        settings=settings,
        executor=executor,
    )

    executor.delete_queue(target_vhost, name, force=force)

    audit_fields = {
        "operation": "queue.delete",
        "vhost": target_vhost,
        "queue_name": name,
        "user": settings.user,
        "forced": force,
        "messages_before_delete": queue_snapshot.get("messages", 0),
        "result": "success",
    }
    if hasattr(logger, "bind"):
        logger.info("queue.delete.success", **audit_fields)
    else:  # pragma: no cover - fallback for plain logging
        logger.info(
            "queue.delete.success operation=%s vhost=%s queue=%s user=%s forced=%s result=%s",
            audit_fields["operation"],
            audit_fields["vhost"],
            audit_fields["queue_name"],
            audit_fields["user"],
            audit_fields["forced"],
            audit_fields["result"],
        )

    return {
        "status": "deleted",
        "operation": "queue.delete",
        "queue": name,
        "vhost": target_vhost,
        "forced": force,
        "messages_before_delete": queue_snapshot.get("messages", 0),
    }


__all__ = [
    "Queue",
    "QueueOptions",
    "PaginatedQueueResponse",
    "create_queue",
    "delete_queue",
    "list_queues",
    "validate_queue_delete",
]
