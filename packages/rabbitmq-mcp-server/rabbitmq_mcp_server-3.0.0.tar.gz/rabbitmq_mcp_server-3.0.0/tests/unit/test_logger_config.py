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

import io
import json

import pytest
import structlog

from src.logging.correlation import reset_correlation_id, set_correlation_id
from src.logging.logger import configure_structlog, reset_structlog_configuration


@pytest.fixture(autouse=True)
def _reset_structlog():
    reset_structlog_configuration()
    reset_correlation_id()
    yield
    reset_structlog_configuration()
    reset_correlation_id()


def test_configure_structlog_sets_expected_processors():
    configure_structlog(logger_factory=structlog.PrintLoggerFactory(file=io.StringIO()))
    processors = structlog.get_config()["processors"]

    assert len(processors) == 6
    timestamper = processors[0]
    assert isinstance(timestamper, structlog.processors.TimeStamper)
    assert timestamper.key == "timestamp"
    assert processors[1].__name__ == "add_correlation_id"
    assert processors[2].__name__ == "redact_sensitive_data"
    assert isinstance(processors[3], structlog.processors.StackInfoRenderer)
    assert processors[4] is structlog.processors.format_exc_info
    assert isinstance(processors[5], structlog.processors.JSONRenderer)


def test_configure_structlog_outputs_valid_json():
    stream = io.StringIO()
    configure_structlog(logger_factory=structlog.PrintLoggerFactory(file=stream))
    set_correlation_id("corr-123")

    logger = structlog.get_logger("test")
    logger.info("hello", foo="bar")

    payload = json.loads(stream.getvalue())
    assert payload["event"] == "hello"
    assert payload["foo"] == "bar"
    assert payload["correlation_id"] == "corr-123"
    assert payload["timestamp"].endswith("Z")


def test_configure_structlog_is_singleton():
    primary_stream = io.StringIO()
    backup_stream = io.StringIO()

    configure_structlog(logger_factory=structlog.PrintLoggerFactory(file=primary_stream))
    configure_structlog(logger_factory=structlog.PrintLoggerFactory(file=backup_stream))

    logger = structlog.get_logger("singleton")
    logger.info("message")

    assert "message" in primary_stream.getvalue()
    assert backup_stream.getvalue() == ""
