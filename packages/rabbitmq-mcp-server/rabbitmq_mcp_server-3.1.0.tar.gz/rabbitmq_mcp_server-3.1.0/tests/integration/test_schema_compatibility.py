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

import pytest

from src.models.log_entry import LogCategory, LogEntry, LogLevel


def _base_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "timestamp": "2025-10-15T12:00:00Z",
        "level": LogLevel.INFO.value,
        "category": LogCategory.OPERATION.value,
        "correlation_id": "cid-123",
        "message": "operation completed",
    }


def test_old_parser_reads_logs_with_minor_version_bump() -> None:
    payload = _base_payload()
    payload["schema_version"] = "1.1.0"
    payload["context"] = {"new_optional_field": "extra info"}

    entry = LogEntry.model_validate(payload)

    assert entry.schema_version == "1.1.0"
    assert entry.context == {"new_optional_field": "extra info"}


def test_old_parser_reads_logs_with_patch_version_bump() -> None:
    payload = _base_payload()
    payload["schema_version"] = "1.0.1"

    entry = LogEntry.model_validate(payload)

    assert entry.schema_version == "1.0.1"


def test_parser_warns_on_major_version_mismatch() -> None:
    payload = _base_payload()
    payload["schema_version"] = "2.0.0"

    with pytest.raises(ValueError, match="unsupported schema_version major component"):
        LogEntry.model_validate(payload)


@pytest.mark.parametrize("invalid_version", ["1.0", "1", "v1.0.0", "1.0.0.0"])
def test_schema_version_increment_follows_semver_rules(invalid_version: str) -> None:
    payload = _base_payload()
    payload["schema_version"] = invalid_version

    with pytest.raises(ValueError):
        LogEntry.model_validate(payload)
