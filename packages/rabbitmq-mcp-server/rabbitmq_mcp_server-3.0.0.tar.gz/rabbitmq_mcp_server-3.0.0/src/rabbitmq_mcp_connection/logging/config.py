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

"""Configuração centralizada de logging estruturado com structlog."""

import logging
import sys
from collections.abc import Iterable
from typing import Any

import structlog

from .sanitizer import sanitize_value

DEFAULT_LOG_LEVEL = logging.INFO  # type: ignore[attr-defined]
SENSITIVE_KEYS = {"password", "credentials", "secret", "token"}


def _sanitize_processor(_: logging.Logger, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:  # type: ignore[name-defined]
    """Sanitiza campos sensíveis e URLs AMQP em qualquer payload."""

    for key in list(event_dict.keys()):
        value = event_dict[key]
        if key in SENSITIVE_KEYS:
            event_dict[key] = "***"
            continue
        event_dict[key] = sanitize_value(value)

    message = event_dict.get("event")
    if isinstance(message, str):
        event_dict["event"] = sanitize_value(message)

    if "exception" in event_dict and isinstance(event_dict["exception"], str):
        event_dict["exception"] = sanitize_value(event_dict["exception"])

    if "traceback" in event_dict and isinstance(event_dict["traceback"], str):
        event_dict["traceback"] = sanitize_value(event_dict["traceback"])

    return event_dict


def configure_logging(
    level: int = DEFAULT_LOG_LEVEL,
    processors: Iterable[structlog.types.Processor] | None = None,
) -> None:
    """Inicializa logging estruturado com sanitização e saída JSON."""

    logging.basicConfig(  # type: ignore[attr-defined]
        level=level,
        stream=sys.stdout,
        format="%(message)s",
    )

    structlog.configure(
        processors=list(  # type: ignore[arg-type]
            processors
            or (
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                _sanitize_processor,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            )
        ),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Retorna um logger estruturado pronto para uso."""

    return structlog.get_logger(name)
