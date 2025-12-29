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

import math
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.log_entry import (
    LogCategory,
    LogEntry,
    LogLevel,
    OperationResult,
)


def _base_payload(**overrides):
    payload = {
        "timestamp": "2025-01-01T00:00:00.000000Z",
        "level": LogLevel.INFO,
        "category": LogCategory.OPERATION,
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "message",
    }
    payload.update(overrides)
    return payload


def test_log_entry_applies_default_schema_version():
    entry = LogEntry(**_base_payload())
    assert entry.schema_version == "1.0.0"


@pytest.mark.parametrize(
    "value",
    ["1.0", "1", "1.0.0.0", "v1.0.0", "1.0.0-beta"],
)
def test_log_entry_rejects_invalid_schema_version(value):
    with pytest.raises(ValidationError) as exc:
        LogEntry(**_base_payload(schema_version=value))
    assert "schema_version" in str(exc.value)


@pytest.mark.parametrize(
    "timestamp",
    ["2025-01-01T00:00:00.000000", "2025-01-01T00:00:00+00:00"],
)
def test_log_entry_requires_utc_timestamp_with_z_suffix(timestamp):
    with pytest.raises(ValidationError) as exc:
        LogEntry(**_base_payload(timestamp=timestamp))
    assert "timestamp" in str(exc.value)


def test_log_entry_accepts_iso_utc_timestamp():
    now = datetime.now(UTC)
    iso_z = now.isoformat().replace("+00:00", "Z")
    entry = LogEntry(**_base_payload(timestamp=iso_z))
    assert entry.timestamp == iso_z


def test_log_entry_truncates_large_messages():
    oversized = "a" * (100_000 + 500)
    entry = LogEntry(**_base_payload(message=oversized))
    assert entry.message.endswith("...[truncated]")
    assert len(entry.message) <= 100_000 + len("...[truncated]")


def test_log_entry_rejects_invalid_log_level():
    with pytest.raises(ValidationError) as exc:
        LogEntry(**_base_payload(level="TRACE"))
    assert "level" in str(exc.value)


def test_log_entry_accepts_optional_fields():
    entry = LogEntry(**_base_payload(duration_ms=12.5, result=OperationResult.SUCCESS))
    assert math.isclose(entry.duration_ms, 12.5)
    assert entry.result is OperationResult.SUCCESS


def test_log_entry_rejects_negative_duration():
    with pytest.raises(ValidationError) as exc:
        LogEntry(**_base_payload(duration_ms=-1))
    assert "duration_ms" in str(exc.value)


def test_log_entry_allows_context_payload():
    context = {"nested": {"value": 1}, "tags": ["a", "b"]}
    entry = LogEntry(**_base_payload(context=context))
    assert entry.context == context
