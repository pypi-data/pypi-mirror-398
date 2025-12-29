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

import contextvars
import secrets
import time
import uuid

__all__ = [
    "generate_correlation_id",
    "set_correlation_id",
    "get_correlation_id",
    "reset_correlation_id",
]


_correlation_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def generate_correlation_id() -> str:
    try:
        return str(uuid.uuid4())
    except Exception:
        timestamp = int(time.time() * 1_000_000)
        random_part = secrets.token_hex(3)
        return f"fallback-{timestamp}-{random_part}"


def set_correlation_id(value: str | None = None) -> str:
    correlation_id = value or generate_correlation_id()
    _correlation_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str | None:
    return _correlation_var.get()


def reset_correlation_id() -> None:
    _correlation_var.set(None)
