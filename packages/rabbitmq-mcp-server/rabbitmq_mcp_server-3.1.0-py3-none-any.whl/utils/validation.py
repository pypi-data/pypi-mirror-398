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

"""Input validation helpers for RabbitMQ MCP operations."""

import re
import time
from typing import TYPE_CHECKING

from utils.errors import (
    AuthorizationError,
    ConnectionError,
    NotFoundError,
    RabbitMQError,
    ValidationError,
)

if TYPE_CHECKING:
    from tools.operations.executor import RabbitMQExecutor

__all__ = [
    "validate_name",
    "validate_exchange_type",
    "validate_routing_key",
    "validate_vhost_exists",
    "reset_vhost_cache",
]

_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,255}$")
_ALLOWED_EXCHANGE_TYPES = {"direct", "topic", "fanout", "headers"}
_WILDCARD_PATTERN = re.compile(r"[\*#]")
_CACHE_TTL_SECONDS = 60.0
_VHOST_CACHE: dict[str, tuple[bool, float]] = {}


def _cache_key(executor: RabbitMQExecutor, vhost: str) -> str:
    base_url = getattr(executor, "base_url", "")
    return f"vhost_exists:{base_url}:{vhost}"


def _cache_get(key: str) -> bool | None:
    now = time.monotonic()
    cached = _VHOST_CACHE.get(key)
    if not cached:
        return None
    exists, expires_at = cached
    if expires_at <= now:
        _VHOST_CACHE.pop(key, None)
        return None
    return exists


def _cache_set(key: str, value: bool) -> None:
    _VHOST_CACHE[key] = (value, time.monotonic() + _CACHE_TTL_SECONDS)


def _cache_invalidate(key: str | None = None) -> None:
    if key is None:
        _VHOST_CACHE.clear()
    else:
        _VHOST_CACHE.pop(key, None)


def reset_vhost_cache() -> None:
    """Utility for tests to clear cache state."""

    _cache_invalidate()


def validate_name(name: str) -> None:
    if not _NAME_PATTERN.match(name or ""):
        raise ValidationError(
            code="INVALID_NAME",
            message="Resource name must use alphanumeric characters, dot, dash or underscore",
            field="name",
            expected="between 1 and 255 characters matching ^[a-zA-Z0-9._-]{1,255}$",
            actual=name,
            action="Use only allowed characters and keep the length under 255",
        )


def validate_exchange_type(exchange_type: str) -> None:
    if exchange_type not in _ALLOWED_EXCHANGE_TYPES:
        raise ValidationError(
            code="INVALID_EXCHANGE_TYPE",
            message="Exchange type is not supported",
            field="type",
            expected="direct | topic | fanout | headers",
            actual=exchange_type,
            action="Choose one of the supported exchange types",
        )


def validate_routing_key(routing_key: str, exchange_type: str) -> None:
    if exchange_type != "topic" and _WILDCARD_PATTERN.search(routing_key or ""):
        raise ValidationError(
            code="INVALID_ROUTING_KEY",
            message="Wildcards are only allowed for topic exchanges",
            field="routing_key",
            expected="Use '*' or '#' only with topic exchanges",
            actual=routing_key,
            action="Remove wildcard characters or change the exchange type to 'topic'",
        )


def validate_vhost_exists(vhost: str, executor: RabbitMQExecutor) -> None:
    """Ensure the target virtual host exists, caching positive lookups for 60 seconds."""

    target_vhost = vhost or getattr(executor, "vhost", "/")
    cache_key = _cache_key(executor, target_vhost)
    cached = _cache_get(cache_key)
    if cached:
        return

    endpoint = f"/vhosts/{executor._encode_vhost(target_vhost)}"

    try:
        executor._request("GET", endpoint)
        _cache_set(cache_key, True)
    except NotFoundError:
        _cache_invalidate(cache_key)
        raise ValidationError(
            code="VHOST_NOT_FOUND",
            message=f"Virtual host '{target_vhost}' was not found",
            field="vhost",
            expected="valid vhost",
            actual=target_vhost,
            action="Create the virtual host or provide an existing one",
        )
    except AuthorizationError:
        _cache_invalidate(cache_key)
        raise
    except ConnectionError:
        # Do not cache negative results caused by server or network failures.
        raise
    except RabbitMQError:
        # Surface other structured errors without caching.
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise ConnectionError(
            code="CONNECTION_ERROR",
            message="Failed to validate virtual host due to unexpected error",
            action="Retry the operation or inspect network connectivity",
            context={"exception": exc.__class__.__name__},
        ) from exc
