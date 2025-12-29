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

"""
Contract tests for JSON schema validation of log entries and configuration.

These tests validate that:
1. LogEntry model matches expected JSON schema
2. LogConfig model matches expected JSON schema
3. All required fields are present
4. Field types are correct
5. Constraints are enforced (enums, ranges, patterns)
"""

import json
import re
from datetime import UTC, datetime

import pytest

from src.models.log_config import LogConfig, LogLevel, RabbitMQConfig
from src.models.log_entry import LogCategory, LogEntry, OperationResult


class TestLogEntrySchema:
    """Contract tests for LogEntry JSON schema."""

    def test_log_entry_has_all_required_fields(self) -> None:
        """Validate that LogEntry includes all required fields per spec."""
        entry = LogEntry(
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message="Test message",
        )

        data = entry.model_dump()

        # Required fields per spec
        required_fields = {
            "schema_version",
            "timestamp",
            "level",
            "category",
            "message",
        }

        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from LogEntry"

    def test_log_entry_schema_version_is_semantic_versioning(self) -> None:
        """Validate schema_version follows semantic versioning (MAJOR.MINOR.PATCH)."""
        entry = LogEntry(
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message="Test",
        )

        schema_version = entry.schema_version

        # Regex for semantic versioning: X.Y.Z where X, Y, Z are integers
        semver_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(
            semver_pattern, schema_version
        ), f"schema_version '{schema_version}' doesn't match semantic versioning pattern"

    def test_log_entry_schema_version_defaults_to_1_0_0(self) -> None:
        """Validate default schema_version is '1.0.0' per spec."""
        entry = LogEntry(
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message="Test",
        )

        assert (
            entry.schema_version == "1.0.0"
        ), f"Default schema_version should be '1.0.0', got '{entry.schema_version}'"

    def test_log_entry_timestamp_is_iso8601_utc(self) -> None:
        """Validate timestamp is ISO 8601 format with UTC timezone."""
        entry = LogEntry(
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message="Test",
        )

        timestamp_str = entry.model_dump()["timestamp"]

        # Should end with 'Z' for UTC
        assert timestamp_str.endswith(
            "Z"
        ), f"Timestamp should be UTC with 'Z' suffix, got: {timestamp_str}"

        # Should be parseable as ISO 8601
        try:
            datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError as e:
            pytest.fail(f"Timestamp not valid ISO 8601: {timestamp_str}, error: {e}")

    def test_log_entry_level_enum_validation(self) -> None:
        """Validate level field accepts only valid LogLevel enum values."""
        valid_levels = [LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO, LogLevel.DEBUG]

        for level in valid_levels:
            entry = LogEntry(
                timestamp=datetime.now(UTC),
                level=level,
                category=LogCategory.OPERATION,
                message="Test",
            )
            assert entry.level == level

        # Invalid level should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            LogEntry(
                timestamp=datetime.now(UTC),
                level="INVALID",  # type: ignore
                category=LogCategory.OPERATION,
                message="Test",
            )

    def test_log_entry_category_enum_validation(self) -> None:
        """Validate category field accepts only valid LogCategory enum values."""
        valid_categories = [
            LogCategory.SECURITY,
            LogCategory.CONNECTION,
            LogCategory.OPERATION,
            LogCategory.PERFORMANCE,
            LogCategory.ERROR,
        ]

        for category in valid_categories:
            entry = LogEntry(
                timestamp=datetime.now(UTC),
                level=LogLevel.INFO,
                category=category,
                message="Test",
            )
            assert entry.category == category

    def test_log_entry_message_truncation_at_100kb(self) -> None:
        """Validate messages >100KB are truncated with '[truncated]' marker."""
        # Create message slightly over 100KB
        large_message = "x" * (100 * 1024 + 100)

        entry = LogEntry(
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message=large_message,
        )

        # Message should be truncated
        assert len(entry.message) <= (100 * 1024), "Message should be truncated to 100KB"
        assert entry.message.endswith(
            "...[truncated]"
        ), "Truncated message should end with '...[truncated]'"

    def test_log_entry_optional_fields_are_optional(self) -> None:
        """Validate optional fields can be omitted."""
        # Minimal entry with only required fields
        entry = LogEntry(
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message="Test",
        )

        # Optional fields should be None or have defaults
        assert entry.correlation_id is None or isinstance(entry.correlation_id, str)
        assert entry.tool_name is None or isinstance(entry.tool_name, str)
        assert entry.duration_ms is None or isinstance(entry.duration_ms, int | float)

    def test_log_entry_serializes_to_valid_json(self) -> None:
        """Validate LogEntry can be serialized to valid JSON."""
        entry = LogEntry(
            timestamp=datetime.now(UTC),
            level=LogLevel.ERROR,
            category=LogCategory.SECURITY,
            message="Security event",
            correlation_id="test-123",
            tool_name="test_tool",
            duration_ms=42.5,
            operation_result=OperationResult.FAILURE,
            error_type="TestError",
            error_message="Test error message",
        )

        # Serialize to JSON
        json_str = entry.model_dump_json()

        # Should be valid JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            pytest.fail(f"LogEntry doesn't serialize to valid JSON: {e}")

        # Verify key fields present
        assert data["level"] == "ERROR"
        assert data["category"] == "SECURITY"
        assert data["message"] == "Security event"
        assert data["correlation_id"] == "test-123"


class TestLogConfigSchema:
    """Contract tests for LogConfig JSON schema."""

    def test_log_config_has_all_required_fields(self) -> None:
        """Validate LogConfig has all required configuration fields."""
        config = LogConfig()  # type: ignore[call-arg]

        data = config.model_dump()

        # Required fields per spec
        required_fields = {
            "log_level",
            "output_file",
            "rotation_when",
            "rotation_interval",
            "rotation_max_bytes",
            "retention_days",
            "compression_enabled",
            "async_queue_size",
            "async_flush_interval",
            "batch_size",
            "file_permissions",
            "fallback_to_console",
        }

        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from LogConfig"

    def test_log_config_defaults_are_correct(self) -> None:
        """Validate LogConfig defaults match specification."""
        config = LogConfig()  # type: ignore[call-arg]

        # Validate defaults per spec
        assert config.log_level == LogLevel.INFO
        assert config.rotation_max_bytes == 100 * 1024 * 1024  # 100MB
        assert config.retention_days == 30
        assert config.compression_enabled is True
        assert config.async_queue_size == 10_000
        assert config.batch_size == 100
        assert config.fallback_to_console is True

    def test_log_config_validates_minimum_values(self) -> None:
        """Validate LogConfig enforces minimum value constraints."""
        # retention_days must be >= 1
        with pytest.raises(Exception):  # Pydantic ValidationError
            LogConfig(retention_days=0)  # type: ignore[call-arg]

        # async_queue_size must be >= 100
        with pytest.raises(Exception):
            LogConfig(async_queue_size=50)  # type: ignore[call-arg]

        # batch_size must be >= 1
        with pytest.raises(Exception):
            LogConfig(batch_size=0)  # type: ignore[call-arg]

    def test_log_config_rabbitmq_config_optional(self) -> None:
        """Validate RabbitMQ configuration is optional."""
        config = LogConfig()  # type: ignore[call-arg]

        # RabbitMQ should have default config with enabled=False
        assert hasattr(config, "rabbitmq")
        assert isinstance(config.rabbitmq, RabbitMQConfig)
        assert config.rabbitmq.enabled is False

    def test_log_config_rabbitmq_validation(self) -> None:
        """Validate RabbitMQ configuration field validation."""
        rabbitmq_config = RabbitMQConfig(
            enabled=True,
            host="localhost",
            port=5672,
            vhost="/",
            username="guest",
            password="guest",
            exchange="logs",
            exchange_type="topic",
        )

        config = LogConfig(rabbitmq=rabbitmq_config)  # type: ignore[call-arg]

        assert config.rabbitmq.enabled is True
        assert config.rabbitmq.host == "localhost"
        assert config.rabbitmq.port == 5672
        assert config.rabbitmq.exchange == "logs"
        assert config.rabbitmq.exchange_type == "topic"

    def test_log_config_serializes_to_valid_json(self) -> None:
        """Validate LogConfig can be serialized to valid JSON."""
        config = LogConfig(  # type: ignore[call-arg]
            log_level=LogLevel.DEBUG,
            output_file="logs/test.log",
            retention_days=14,
        )

        # Serialize to JSON
        json_str = config.model_dump_json()

        # Should be valid JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            pytest.fail(f"LogConfig doesn't serialize to valid JSON: {e}")

        # Verify key fields
        assert data["log_level"] == "DEBUG"
        assert data["output_file"] == "logs/test.log"
        assert data["retention_days"] == 14

    def test_log_config_can_be_loaded_from_dict(self) -> None:
        """Validate LogConfig can be constructed from dictionary (YAML parsing)."""
        config_dict = {
            "log_level": "INFO",
            "output_file": "logs/app.log",
            "rotation_max_bytes": 50 * 1024 * 1024,
            "retention_days": 7,
            "compression_enabled": False,
        }

        # Should construct from dict
        config = LogConfig(**config_dict)

        assert config.log_level == LogLevel.INFO
        assert config.output_file == "logs/app.log"
        assert config.rotation_max_bytes == 50 * 1024 * 1024
        assert config.retention_days == 7
        assert config.compression_enabled is False


class TestSchemaBackwardCompatibility:
    """Contract tests for schema version backward compatibility."""

    def test_schema_version_supports_minor_version_bumps(self) -> None:
        """Validate that minor version bumps maintain backward compatibility."""
        # Simulate v1.1.0 log with new optional field
        entry_v1_1_0 = LogEntry(
            schema_version="1.1.0",
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message="Test",
        )

        # v1.0.0 parser should still read it (only required fields)
        data = entry_v1_1_0.model_dump()
        assert data["schema_version"] == "1.1.0"

        # Can construct from data (backward compatible)
        reconstructed = LogEntry(**data)
        assert reconstructed.message == "Test"

    def test_schema_version_supports_patch_version_bumps(self) -> None:
        """Validate patch version bumps are backward compatible."""
        entry_v1_0_1 = LogEntry(
            schema_version="1.0.1",
            timestamp=datetime.now(UTC),
            level=LogLevel.INFO,
            category=LogCategory.OPERATION,
            message="Test",
        )

        # Should be fully backward compatible
        data = entry_v1_0_1.model_dump()
        reconstructed = LogEntry(**data)
        assert reconstructed.schema_version == "1.0.1"
