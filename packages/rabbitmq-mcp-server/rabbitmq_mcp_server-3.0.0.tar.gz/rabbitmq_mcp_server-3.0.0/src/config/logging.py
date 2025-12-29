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

import logging
import os
import uuid
from logging.handlers import TimedRotatingFileHandler  # type: ignore[attr-defined]
from typing import Any

import structlog

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "./logs/rabbitmq-mcp.log")

# Sensitive data patterns to redact
SENSITIVE_PATTERNS = [r"password", r"token", r"credential", r"Authorization"]


class RedactProcessor:
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        for key in event_dict:
            if any(p in key.lower() for p in SENSITIVE_PATTERNS):
                event_dict[key] = "REDACTED"
        return event_dict


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)


# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.UUIDAdder("correlation_id", uuid.uuid4),  # type: ignore[attr-defined]
        RedactProcessor(),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# File-based logging with rotation
file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", utc=True)  # type: ignore[attr-defined]
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logging.Formatter("%(message)s"))  # type: ignore[attr-defined]
logging.getLogger().addHandler(file_handler)  # type: ignore[attr-defined]
logging.getLogger().setLevel(LOG_LEVEL)  # type: ignore[attr-defined]

# Stdout logging for containers/cloud
if os.getenv("LOG_STDOUT", "0") == "1":
    stream_handler = logging.StreamHandler()  # type: ignore[attr-defined]
    stream_handler.setLevel(LOG_LEVEL)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))  # type: ignore[attr-defined]
    logging.getLogger().addHandler(stream_handler)  # type: ignore[attr-defined]
