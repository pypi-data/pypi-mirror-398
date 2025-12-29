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

import json
import logging
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler  # type: ignore[attr-defined]
from pathlib import Path

import structlog
from structlog.stdlib import BoundLogger, LoggerFactory

SENSITIVE_FIELD_PATTERNS: tuple[str, ...] = (
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "credentials",
    "private_key",
    "access_token",
    "refresh_token",
    "bearer",
    "jwt",
    "session_id",
    "cookie",
    "client_secret",
)

_SENSITIVE_KEYS = {pattern.lower() for pattern in SENSITIVE_FIELD_PATTERNS}

_REDACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = []
for _pattern in SENSITIVE_FIELD_PATTERNS:
    _REDACTION_PATTERNS.extend(
        [
            (
                re.compile(rf"({_pattern}\s*[:=]\s*)([^\s,;]+)", re.IGNORECASE),
                r"\1***",
            ),
            (
                re.compile(rf'("{_pattern}"\s*:\s*")([^"]+)"', re.IGNORECASE),
                r'\1***"',
            ),
            (
                re.compile(rf"('{_pattern}'\s*:\s*')([^']+)'", re.IGNORECASE),
                r"\1***'",
            ),
        ]
    )

_DEFAULT_MAX_BYTES = 100 * 1024 * 1024


class JSONFormatter(logging.Formatter):  # type: ignore[name-defined,misc]
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[name-defined]
        timestamp = datetime.fromtimestamp(record.created, UTC).isoformat().replace("+00:00", "Z")
        record_dict = {
            "timestamp": timestamp,
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": _redact_string(record.getMessage()),
        }

        if record.exc_info:
            record_dict["exception"] = self.formatException(record.exc_info)

        event_payload = None
        message_text = record.getMessage()
        if isinstance(message_text, str):
            try:
                parsed = json.loads(message_text)
            except (json.JSONDecodeError, TypeError):
                parsed = None
            if isinstance(parsed, dict):
                event_payload = parsed

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {"args", "msg", "message", "exc_info", "exc_text"}:
                continue
            if isinstance(value, str | int | float | bool) or value is None:
                if isinstance(key, str) and key.lower() in _SENSITIVE_KEYS:
                    record_dict[key] = "***"
                elif isinstance(value, str):
                    record_dict[key] = _redact_string(value)
                else:
                    record_dict[key] = value

        if isinstance(event_payload, dict):
            for key, value in event_payload.items():
                if not isinstance(key, str):
                    continue
                lowered = key.lower()
                if lowered in _SENSITIVE_KEYS:
                    record_dict[key] = "***"
                elif isinstance(value, str):
                    record_dict[key] = _redact_string(value)
                else:
                    record_dict[key] = value
            if "message" in event_payload:
                record_dict["message"] = _redact_string(str(event_payload["message"]))

        return json.dumps(record_dict, ensure_ascii=False)


class DailyRotatingJSONHandler(RotatingFileHandler):  # type: ignore[misc]
    def __init__(
        self,
        *,
        name: str,
        directory: Path,
        app_name: str,
        level: int,
        retention_days: int,
        max_bytes: int,
    ) -> None:
        self.directory = directory
        self.app_name = app_name
        self.category = name
        directory.mkdir(parents=True, exist_ok=True)

        base_filename = self._build_filename()
        super().__init__(
            filename=base_filename,
            maxBytes=max_bytes,
            backupCount=retention_days,
            encoding="utf-8",
        )
        self.setLevel(level)
        self.setFormatter(JSONFormatter())
        self.set_name(name)
        self.max_bytes = max_bytes

    def _build_filename(self) -> str:
        current_date = datetime.now(UTC).strftime("%Y-%m-%d")
        if self.category == "general":
            filename = f"{self.app_name}-{current_date}.log"
        else:
            filename = f"{self.app_name}-{self.category}-{current_date}.log"
        return str(self.directory / filename)

    @property
    def current_log_path(self) -> str:
        return self.baseFilename  # type: ignore[no-any-return]

    @property
    def rotation(self) -> str:
        return "daily"

    @rotation.setter
    def rotation(self, value: str) -> None:  # pragma: no cover - setter only for tests
        # Logging API expects setter, but rotation is fixed
        pass

    @property
    def retention_days(self) -> int:
        return self.backupCount

    @retention_days.setter
    def retention_days(self, value: int) -> None:
        self.backupCount = value


@dataclass
class LoggingContext:
    logger: BoundLogger
    base_logger: logging.Logger  # type: ignore[name-defined]
    handlers: list[DailyRotatingJSONHandler]
    policies: dict[str, dict[str, int | str]]

    def flush(self) -> None:
        for handler in self.handlers:
            handler.flush()


_current_context: LoggingContext | None = None


def _level_from_env(value: str) -> int:
    try:
        return getattr(logging, value.upper())  # type: ignore[no-any-return]
    except AttributeError:
        return logging.INFO  # type: ignore[attr-defined,no-any-return]


def _redact_string(text: str) -> str:
    if not text:
        return text
    redacted = text
    for regex, replacement in _REDACTION_PATTERNS:
        redacted = regex.sub(replacement, redacted)
    return redacted


def _sanitize_event(
    logger: logging.Logger, method_name: str, event_dict: dict[str, object]  # type: ignore[name-defined]
) -> dict[str, object]:
    for key, value in list(event_dict.items()):
        if isinstance(key, str) and key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***"
            continue
        if isinstance(value, str):
            event_dict[key] = _redact_string(value)
    event = event_dict.pop("event", "")
    event_dict["message"] = _redact_string(str(event))
    if "level" in event_dict:
        event_dict["level"] = str(event_dict["level"]).lower()
    if "logger" not in event_dict:
        event_dict["logger"] = logger.name
    event_dict.pop("logger_name", None)
    return event_dict


def _build_policies(*, max_bytes: int) -> dict[str, dict[str, int | str]]:
    return {
        "general": {"retention_days": 30, "max_bytes": max_bytes, "rotation": "daily"},
        "errors": {"retention_days": 90, "max_bytes": max_bytes, "rotation": "daily"},
        "audit": {"retention_days": 365, "max_bytes": max_bytes, "rotation": "daily"},
    }


def _build_handlers(
    *,
    level: int,
    directory: Path,
    app_name: str,
    max_bytes: int,
) -> list[DailyRotatingJSONHandler]:
    return [
        DailyRotatingJSONHandler(
            name="general",
            directory=directory,
            app_name=app_name,
            level=level,
            retention_days=30,
            max_bytes=max_bytes,
        ),
        DailyRotatingJSONHandler(
            name="errors",
            directory=directory,
            app_name=app_name,
            level=logging.ERROR,  # type: ignore[attr-defined]
            retention_days=90,
            max_bytes=max_bytes,
        ),
        DailyRotatingJSONHandler(
            name="audit",
            directory=directory,
            app_name=app_name,
            level=level,
            retention_days=365,
            max_bytes=max_bytes,
        ),
    ]


def configure_logging(
    *, output_dir: str | Path | None = None, app_name: str = "rabbitmq-mcp"
) -> LoggingContext:
    global _current_context
    reset_logging()

    directory = Path(output_dir or "logs")
    level_name = os.getenv("LOG_LEVEL", "INFO")
    level = _level_from_env(level_name)

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _sanitize_event,  # type: ignore[list-item]
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    base_logger = logging.getLogger(app_name)  # type: ignore[attr-defined]
    base_logger.handlers.clear()
    base_logger.setLevel(level)
    base_logger.propagate = False

    handlers = _build_handlers(
        level=level, directory=directory, app_name=app_name, max_bytes=_DEFAULT_MAX_BYTES
    )

    for handler in handlers:
        base_logger.addHandler(handler)

    policies = _build_policies(max_bytes=_DEFAULT_MAX_BYTES)
    logger = structlog.get_logger(app_name)
    _current_context = LoggingContext(
        logger=logger,
        base_logger=base_logger,
        handlers=handlers,
        policies=policies,
    )
    return _current_context


def reset_logging() -> None:
    global _current_context
    if _current_context is None:
        structlog.reset_defaults()
        return

    for handler in list(_current_context.handlers):
        _current_context.base_logger.removeHandler(handler)
        handler.close()
    _current_context.handlers.clear()
    structlog.reset_defaults()
    _current_context = None


def get_active_handlers() -> Iterable[logging.Handler]:  # type: ignore[name-defined]
    if _current_context is None:
        return []
    return tuple(_current_context.handlers)


__all__ = [
    "DailyRotatingJSONHandler",
    "JSONFormatter",
    "LoggingContext",
    "SENSITIVE_FIELD_PATTERNS",
    "configure_logging",
    "get_active_handlers",
    "reset_logging",
]
