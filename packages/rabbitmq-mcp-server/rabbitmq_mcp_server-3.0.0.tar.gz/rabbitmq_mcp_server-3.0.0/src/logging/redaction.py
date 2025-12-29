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

import re
from typing import Any

__all__ = ["apply_redaction", "apply_redaction_to_event"]


REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"password\s*=\s*['\"]?([^'\"\s]+)"), "[REDACTED]"),
    (re.compile(r"api[_-]?key\s*=\s*['\"]?([^'\"\s]+)"), "[REDACTED]"),
    (re.compile(r"token\s*=\s*['\"]?([^'\"\s]+)"), "[REDACTED]"),
    (re.compile(r"Bearer\s+([A-Za-z0-9\-._~+/]+=*)", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"amqp://([^:]+):([^@]+)@"), r"amqp://\1:[REDACTED]@"),
)


SENSITIVE_KEYS = {"password", "api_key", "token", "authorization"}
SENSITIVE_KEY_SUBSTRINGS = ("password", "token", "secret", "api_key")


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    if lowered in SENSITIVE_KEYS:
        return True
    return any(sub in lowered for sub in SENSITIVE_KEY_SUBSTRINGS)


def _redacted_value_for_key(key: str) -> str:
    lowered = key.lower()
    if lowered == "authorization":
        return "Bearer [REDACTED]"
    return "[REDACTED]"


def _redact_string(value: str) -> str:
    redacted = value
    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _redact_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, str) and _is_sensitive_key(key):
            redacted[key] = _redacted_value_for_key(key)
            continue
        redacted[key] = apply_redaction(value)
    return redacted


def _redact_sequence(sequence: Any) -> Any:
    if isinstance(sequence, list):
        return [apply_redaction(item) for item in sequence]
    if isinstance(sequence, tuple):
        return tuple(apply_redaction(item) for item in sequence)
    return sequence


def apply_redaction(data: Any) -> Any:
    if isinstance(data, str):
        return _redact_string(data)
    if isinstance(data, dict):
        return _redact_mapping(data)
    if isinstance(data, list | tuple):
        return _redact_sequence(data)
    return data


def apply_redaction_to_event(event_dict: dict[str, Any]) -> dict[str, Any]:
    # structlog may pass a proxy mapping; convert to a plain dict for consistent processing
    if not isinstance(event_dict, dict):
        event_dict = dict(event_dict)
    return _redact_mapping(event_dict)
