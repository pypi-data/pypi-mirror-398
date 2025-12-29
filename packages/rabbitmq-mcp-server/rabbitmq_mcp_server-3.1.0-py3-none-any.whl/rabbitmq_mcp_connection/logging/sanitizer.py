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

"""Utilidades para sanitização de dados sensíveis em logs."""

import re
from collections.abc import Mapping
from typing import Any

AMQP_URL_PATTERN = re.compile(r"(amqp://[^:]+:)([^@]+)(@)")


def sanitize_amqp_urls(value: str) -> str:
    """Substitui credenciais em URLs AMQP pela forma sanitizada."""

    return AMQP_URL_PATTERN.sub(r"\1***\3", value)


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_amqp_urls(value)
    if isinstance(value, Mapping):
        return {key: sanitize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value
