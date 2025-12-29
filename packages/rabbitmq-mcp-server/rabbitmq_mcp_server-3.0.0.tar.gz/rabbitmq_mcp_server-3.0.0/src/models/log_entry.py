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

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

__all__ = ["LogLevel", "LogCategory", "OperationResult", "LogEntry"]

MAX_MESSAGE_LENGTH = 100_000
TRUNCATION_SUFFIX = "...[truncated]"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
TOOL_NAME_PATTERN = r"^[a-z0-9_\-]+$"


class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogCategory(str, Enum):
    CONNECTION = "CONNECTION"
    OPERATION = "OPERATION"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"


class OperationResult(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    FAILURE = "error"
    TIMEOUT = "timeout"


class LogEntry(BaseModel):
    """Structured log entry validated against the documented schema."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: str = Field(
        default="1.0.0",
        pattern=SEMVER_PATTERN,
        description="Semantic version for the log entry schema",
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp in UTC with trailing Z",
    )
    level: LogLevel
    category: LogCategory
    correlation_id: str | None = Field(None, min_length=1)
    message: str = Field(..., min_length=1)

    tool_name: str | None = Field(None, pattern=TOOL_NAME_PATTERN)
    operation_id: str | None = None
    duration_ms: float | None = Field(None, ge=0)
    operation_result: OperationResult | None = Field(  # accepts legacy "result"
        default=None,
        validation_alias=AliasChoices("operation_result", "result"),
    )
    error_type: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None
    context: dict[str, Any] | None = None

    @property
    def result(self) -> OperationResult | None:
        """Expose legacy result alias for backwards compatibility."""

        return self.operation_result

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_timestamp(cls, value: Any) -> str:
        if isinstance(value, datetime):
            aware = value if value.tzinfo else value.replace(tzinfo=UTC)
            utc_value = aware.astimezone(UTC)
            serialized = utc_value.isoformat().replace("+00:00", "Z")
            return serialized
        if isinstance(value, str):
            return value
        raise TypeError("timestamp must be str or datetime")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        if not value.endswith("Z"):
            raise ValueError("timestamp must be in UTC and end with 'Z'")
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be ISO 8601 compliant") from exc
        return value

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        major_str, *_ = value.split(".")
        try:
            major = int(major_str)
        except ValueError as exc:
            raise ValueError("schema_version major component must be numeric") from exc
        if major != 1:
            raise ValueError("unsupported schema_version major component for parser v1.0.0")
        return value

    @field_validator("message")
    @classmethod
    def truncate_message(cls, value: str) -> str:
        if len(value) <= MAX_MESSAGE_LENGTH:
            return value
        return value[:MAX_MESSAGE_LENGTH] + TRUNCATION_SUFFIX

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        level = info.data.get("level")
        if level is not None and level is not LogLevel.ERROR:
            raise ValueError("error_type requires level ERROR")
        return value

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        level = info.data.get("level")
        if level is not None and level is not LogLevel.ERROR:
            raise ValueError("error_message requires level ERROR")
        return value
