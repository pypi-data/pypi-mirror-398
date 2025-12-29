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

"""Integration tests for User Story 6 - RabbitMQ Log Streaming (T047 checkpoint validation)."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.logging.correlation import set_correlation_id
from src.logging.logger import get_logger, reset_structlog_configuration
from src.models.log_config import LogConfig, LogLevel, RabbitMQConfig
from src.models.log_entry import LogCategory


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    reset_structlog_configuration()


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ connection for testing."""
    with patch("src.logging.handlers.rabbitmq.pika") as mock_pika:
        mock_connection = MagicMock()
        mock_channel = MagicMock()

        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False
        mock_pika.BlockingConnection.return_value = mock_connection

        yield mock_pika, mock_channel


def test_logs_published_to_rabbitmq_exchange(tmp_path: Path, mock_rabbitmq):
    """
    US6 Acceptance 1: Logs published to configured topic exchange with routing key.

    Validates that when RabbitMQ destination is enabled, logs are published
    to the exchange with {level}.{category} routing key within 500ms.
    """
    mock_pika, mock_channel = mock_rabbitmq

    log_file = tmp_path / "test.log"
    config = LogConfig(
        output_file=str(log_file),
        log_level=LogLevel.DEBUG,
        rabbitmq=RabbitMQConfig(
            enabled=True,
            host="localhost",
            exchange="logs",
        ),
    )

    logger = get_logger("test-rabbitmq", config=config)
    set_correlation_id("us6-test-1")

    start_time = time.time()
    logger.info("Test message", category=LogCategory.CONNECTION)
    logger.flush()
    latency_ms = (time.time() - start_time) * 1000

    logger.shutdown()
    time.sleep(0.1)

    # Verify exchange was declared
    mock_channel.exchange_declare.assert_called_once_with(
        exchange="logs",
        exchange_type="topic",
        durable=True,
    )

    # Verify message was published
    assert mock_channel.basic_publish.call_count >= 1

    call_args = mock_channel.basic_publish.call_args
    assert call_args[1]["exchange"] == "logs"
    assert call_args[1]["routing_key"] == "INFO.CONNECTION"

    # Verify latency requirement (< 500ms)
    assert latency_ms < 500


def test_consumer_filters_by_routing_key(tmp_path: Path, mock_rabbitmq):
    """
    US6 Acceptance 2: Consumers can filter logs by routing key pattern.

    Validates that routing key format {level}.{category} enables
    consumers to subscribe to specific log types (e.g., "error.*").
    """
    mock_pika, mock_channel = mock_rabbitmq

    log_file = tmp_path / "test.log"
    config = LogConfig(
        output_file=str(log_file),
        log_level=LogLevel.DEBUG,
        rabbitmq=RabbitMQConfig(
            enabled=True,
            host="localhost",
            exchange="logs",
        ),
    )

    logger = get_logger("test-filter", config=config)
    set_correlation_id("us6-test-2")

    # Generate logs at different levels
    logger.debug("Debug message", category=LogCategory.OPERATION)
    logger.info("Info message", category=LogCategory.CONNECTION)
    logger.error("Error message 1", category=LogCategory.ERROR)
    logger.error("Error message 2", category=LogCategory.SECURITY)

    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Collect all published routing keys
    routing_keys = [call[1]["routing_key"] for call in mock_channel.basic_publish.call_args_list]

    # Verify routing key pattern
    assert "DEBUG.OPERATION" in routing_keys
    assert "INFO.CONNECTION" in routing_keys
    assert "ERROR.ERROR" in routing_keys
    assert "ERROR.SECURITY" in routing_keys

    # Simulate consumer filtering for "error.*"
    error_logs = [key for key in routing_keys if key.startswith("ERROR.")]
    assert len(error_logs) == 2
    assert "ERROR.ERROR" in error_logs
    assert "ERROR.SECURITY" in error_logs


def test_fallback_to_console_when_broker_unavailable(tmp_path: Path, capsys):
    """
    US6 Acceptance 3: System falls back to console when RabbitMQ unavailable.

    Validates that when broker is down, system continues logging to
    console without blocking operations.
    """
    with patch("src.logging.handlers.rabbitmq.pika") as mock_pika:
        # Simulate broker unavailable
        mock_pika.BlockingConnection.side_effect = Exception("Connection refused")

        log_file = tmp_path / "test.log"
        config = LogConfig(
            output_file=str(log_file),
            rabbitmq=RabbitMQConfig(
                enabled=True,
                host="localhost",
            ),
            fallback_to_console=True,
        )

        logger = get_logger("test-fallback", config=config)
        set_correlation_id("us6-test-3")

        # Should not block or crash
        start_time = time.time()
        logger.info("Test message", category=LogCategory.OPERATION)
        logger.flush()
        duration = time.time() - start_time

        logger.shutdown()

        # Verify operation didn't block for long; exponential backoff (1s + 2s + 4s)
        # with immediate fallback should stay under 8 seconds
        assert duration < 8.0

        # Verify fallback message logged to stderr
        captured = capsys.readouterr()
        assert (
            "Failed to connect to RabbitMQ" in captured.err
            or "Failed to publish log to RabbitMQ" in captured.err
        )


def test_multiple_consumers_receive_copies_independently(tmp_path: Path, mock_rabbitmq):
    """
    US6 Acceptance 4: Multiple consumers receive log copies independently.

    Validates that topic exchange enables multiple consumers with
    separate queues to receive log messages without interfering.
    """
    mock_pika, mock_channel = mock_rabbitmq

    log_file = tmp_path / "test.log"
    config = LogConfig(
        output_file=str(log_file),
        rabbitmq=RabbitMQConfig(
            enabled=True,
            host="localhost",
            exchange="logs",
            exchange_type="topic",  # Topic exchange for multi-consumer
        ),
    )

    logger = get_logger("test-multi", config=config)
    set_correlation_id("us6-test-4")

    # Publish logs
    logger.info("Shared log 1", category=LogCategory.CONNECTION)
    logger.error("Shared log 2", category=LogCategory.ERROR)

    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Verify exchange type is topic (enables multiple bindings)
    mock_channel.exchange_declare.assert_called_once()
    call_args = mock_channel.exchange_declare.call_args
    assert call_args[1]["exchange_type"] == "topic"

    # Verify messages were published (can be consumed by multiple queues)
    assert mock_channel.basic_publish.call_count >= 2

    # Each consumer would create their own queue bound to the exchange
    # Example bindings:
    # - Consumer 1: Queue "alerts" bound to "error.*"
    # - Consumer 2: Queue "audit" bound to "*.CONNECTION"
    # - Consumer 3: Queue "all" bound to "#"
    # All receive independent copies without interference


def test_automatic_reconnection_with_exponential_backoff(tmp_path: Path):
    """
    US6 Acceptance 5: Automatic reconnection when broker becomes available.

    Validates that system attempts reconnection using exponential
    backoff (3 attempts, 1s base, 2x backoff, 10s max).
    """
    with patch("src.logging.handlers.rabbitmq.pika") as mock_pika:
        with patch("src.logging.handlers.rabbitmq.time.sleep") as mock_sleep:
            # Simulate broker unavailable initially, then available
            mock_connection = MagicMock()
            mock_channel = MagicMock()
            mock_connection.channel.return_value = mock_channel
            mock_connection.is_closed = False

            # First 2 attempts fail, 3rd succeeds
            mock_pika.BlockingConnection.side_effect = [
                Exception("Connection refused"),
                Exception("Connection refused"),
                mock_connection,  # Success
            ]

            log_file = tmp_path / "test.log"
            config = LogConfig(
                output_file=str(log_file),
                rabbitmq=RabbitMQConfig(
                    enabled=True,
                    host="localhost",
                ),
            )

            logger = get_logger("test-reconnect", config=config)
            set_correlation_id("us6-test-5")

            # Logger should eventually connect after retries
            logger.info("Test after reconnect", category=LogCategory.OPERATION)
            logger.flush()
            logger.shutdown()

            # Verify exponential backoff was used
            sleep_calls = mock_sleep.call_args_list
            assert len(sleep_calls) >= 2

            # Verify backoff pattern: 1s, 2s, 4s...
            delays = [call[0][0] for call in sleep_calls]
            assert delays[0] == pytest.approx(1.0, abs=0.1)  # 1s
            assert delays[1] == pytest.approx(2.0, abs=0.1)  # 2s


def test_messages_are_persistent(tmp_path: Path, mock_rabbitmq):
    """
    Validate that published messages are marked as persistent (delivery_mode=2).

    This ensures messages survive broker restarts for critical logs.
    """
    mock_pika, mock_channel = mock_rabbitmq

    log_file = tmp_path / "test.log"
    config = LogConfig(
        output_file=str(log_file),
        rabbitmq=RabbitMQConfig(
            enabled=True,
            host="localhost",
        ),
    )

    logger = get_logger("test-persistent", config=config)
    set_correlation_id("us6-test-persist")

    logger.error("Critical error", category=LogCategory.ERROR)
    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Verify message properties include delivery_mode=2
    call_args = mock_channel.basic_publish.call_args
    properties = call_args[1]["properties"]
    assert properties.delivery_mode == 2


def test_log_message_includes_all_fields(tmp_path: Path, mock_rabbitmq):
    """
    Validate that published messages include all log entry fields.

    Ensures consumers receive complete log context.
    """
    mock_pika, mock_channel = mock_rabbitmq

    log_file = tmp_path / "test.log"
    config = LogConfig(
        output_file=str(log_file),
        rabbitmq=RabbitMQConfig(
            enabled=True,
            host="localhost",
        ),
    )

    logger = get_logger("test-fields", config=config)
    set_correlation_id("us6-test-fields")

    logger.error(
        "Authentication failed",
        category=LogCategory.SECURITY,
        user_id="admin",
        ip_address="192.168.1.1",
    )
    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Verify published message contains all fields
    call_args = mock_channel.basic_publish.call_args
    body = call_args[1]["body"]
    parsed = json.loads(body)

    assert parsed["event"] == "Authentication failed"
    assert parsed["level"] == "ERROR"
    assert parsed["category"] == "SECURITY"
    assert parsed["correlation_id"] == "us6-test-fields"
    assert parsed["user_id"] == "admin"
    assert parsed["ip_address"] == "192.168.1.1"
    assert "timestamp" in parsed
    assert "schema_version" in parsed


def test_file_and_rabbitmq_destinations_work_simultaneously(tmp_path: Path, mock_rabbitmq):
    """
    Validate that logs are written to both file and RabbitMQ simultaneously.

    Ensures multi-destination logging works correctly.
    """
    mock_pika, mock_channel = mock_rabbitmq

    log_file = tmp_path / "test.log"
    config = LogConfig(
        output_file=str(log_file),
        rabbitmq=RabbitMQConfig(
            enabled=True,
            host="localhost",
        ),
    )

    logger = get_logger("test-multi-dest", config=config)
    set_correlation_id("us6-test-multi")

    logger.info("Multi-destination log", category=LogCategory.OPERATION)
    logger.flush()
    logger.shutdown()
    time.sleep(0.2)

    # Verify log written to file
    with open(log_file) as f:
        lines = f.readlines()

    assert len(lines) >= 1
    file_log = json.loads(lines[0])
    assert file_log["event"] == "Multi-destination log"

    # Verify log published to RabbitMQ
    assert mock_channel.basic_publish.call_count >= 1
    call_args = mock_channel.basic_publish.call_args
    body = call_args[1]["body"]
    rabbitmq_log = json.loads(body)
    assert rabbitmq_log["event"] == "Multi-destination log"
