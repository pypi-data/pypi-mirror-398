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

from typing import Any

from .correlation import get_correlation_id
from .redaction import apply_redaction_to_event

__all__ = ["add_correlation_id", "redact_sensitive_data"]


ProcessorReturn = tuple[Any, str, dict[str, Any]]

_LEVEL_LABELS = {
    "warning": "WARN",
    "warn": "WARN",
    "error": "ERROR",
    "exception": "ERROR",
    "info": "INFO",
    "debug": "DEBUG",
}

_DEFAULT_SCHEMA_VERSION = "1.0.0"


def add_correlation_id(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    label = _LEVEL_LABELS.get(method_name, method_name.upper())
    event_dict.setdefault("level", label)
    event_dict.setdefault("schema_version", _DEFAULT_SCHEMA_VERSION)

    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict.setdefault("correlation_id", correlation_id)
    return event_dict


def redact_sensitive_data(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    return apply_redaction_to_event(event_dict)
