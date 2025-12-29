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

"""Unit tests for RabbitMQ log handler (T043 - User Story 6)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.logging.handlers.rabbitmq import RabbitMQLogHandler


@pytest.fixture
def mock_pika():
    """Mock pika library for testing without actual RabbitMQ connection."""
    with patch("src.logging.handlers.rabbitmq.pika") as mock:
        # Mock connection
        mock_connection = MagicMock()
        mock_channel = MagicMock()

        mock_connection.channel.return_value = mock_channel
        mock.BlockingConnection.return_value = mock_connection

        yield mock


@pytest.fixture
def handler_config():
    """Default configuration for RabbitMQ handler."""
    return {
        "host": "localhost",
        "port": 5672,
        "vhost": "/",
        "username": "guest",
        "password": "guest",
        "exchange": "logs",
        "exchange_type": "topic",
        "durable": True,
        "retry_attempts": 3,
        "retry_base_delay": 1.0,
        "retry_max_delay": 10.0,
    }


def test_rabbitmq_handler_connects_to_broker(mock_pika, handler_config):
    """Test that RabbitMQLogHandler successfully connects to RabbitMQ broker."""
    RabbitMQLogHandler(**handler_config)

    # Verify connection was attempted
    mock_pika.BlockingConnection.assert_called_once()

    # Verify connection parameters
    call_args = mock_pika.BlockingConnection.call_args
    params = call_args[0][0]
    assert params.host == "localhost"
    assert params.port == 5672
    assert params.virtual_host == "/"
    assert params.credentials.username == "guest"
    assert params.credentials.password == "guest"


def test_handler_declares_exchange(mock_pika, handler_config):
    """Test that handler declares the log exchange with correct settings."""
    RabbitMQLogHandler(**handler_config)

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # Verify exchange was declared
    mock_channel.exchange_declare.assert_called_once_with(
        exchange="logs",
        exchange_type="topic",
        durable=True,
    )


def test_handler_publishes_log_to_exchange(mock_pika, handler_config):
    """Test that handler publishes log entries to the exchange."""
    handler = RabbitMQLogHandler(**handler_config)

    log_entry = {
        "timestamp": "2025-10-15T10:30:00Z",
        "level": "INFO",
        "category": "CONNECTION",
        "message": "Connected to RabbitMQ",
        "correlation_id": "test-123",
    }

    handler.write_batch([log_entry])

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # Verify message was published
    assert mock_channel.basic_publish.call_count == 1

    call_args = mock_channel.basic_publish.call_args
    assert call_args[1]["exchange"] == "logs"
    assert call_args[1]["routing_key"] == "INFO.CONNECTION"

    # Verify message body is JSON
    body = call_args[1]["body"]
    parsed = json.loads(body)
    assert parsed["message"] == "Connected to RabbitMQ"


def test_routing_key_pattern_applied(mock_pika, handler_config):
    """Test that routing key follows {level}.{category} pattern."""
    handler = RabbitMQLogHandler(**handler_config)

    test_cases = [
        ("ERROR", "SECURITY", "ERROR.SECURITY"),
        ("INFO", "OPERATION", "INFO.OPERATION"),
        ("DEBUG", "PERFORMANCE", "DEBUG.PERFORMANCE"),
        ("WARN", "CONNECTION", "WARN.CONNECTION"),
    ]

    for level, category, expected_key in test_cases:
        log_entry = {
            "timestamp": "2025-10-15T10:30:00Z",
            "level": level,
            "category": category,
            "message": "Test message",
        }

        handler.write_batch([log_entry])

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # Verify all routing keys are correct
    calls = mock_channel.basic_publish.call_args_list
    for i, (level, category, expected_key) in enumerate(test_cases):
        assert calls[i][1]["routing_key"] == expected_key


def test_messages_are_persistent(mock_pika, handler_config):
    """Test that published messages have delivery_mode=2 (persistent)."""
    handler = RabbitMQLogHandler(**handler_config)

    log_entry = {
        "timestamp": "2025-10-15T10:30:00Z",
        "level": "ERROR",
        "category": "ERROR",
        "message": "Critical error",
    }

    handler.write_batch([log_entry])

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # Verify properties include delivery_mode=2
    call_args = mock_channel.basic_publish.call_args
    properties = call_args[1]["properties"]
    assert properties.delivery_mode == 2


def test_handler_fails_gracefully_if_broker_down(handler_config, capsys):
    """Test that handler handles connection failure gracefully without crashing."""
    with patch("src.logging.handlers.rabbitmq.pika") as mock_pika:
        # Simulate connection failure
        mock_pika.BlockingConnection.side_effect = Exception("Connection refused")

        # Should not raise exception
        handler = RabbitMQLogHandler(**handler_config, fallback_to_console=True)

        log_entry = {
            "timestamp": "2025-10-15T10:30:00Z",
            "level": "ERROR",
            "category": "ERROR",
            "message": "Test error",
        }

        # Should not crash
        handler.write_batch([log_entry])

        # Verify fallback message logged to stderr
        captured = capsys.readouterr()
        assert "Failed to publish log to RabbitMQ" in captured.err


def test_handler_batch_writes_multiple_logs(mock_pika, handler_config):
    """Test that write_batch publishes multiple logs efficiently."""
    handler = RabbitMQLogHandler(**handler_config)

    log_entries = [
        {"level": "INFO", "category": "CONNECTION", "message": "Log 1"},
        {"level": "ERROR", "category": "ERROR", "message": "Log 2"},
        {"level": "DEBUG", "category": "OPERATION", "message": "Log 3"},
    ]

    handler.write_batch(log_entries)

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # Verify all messages were published
    assert mock_channel.basic_publish.call_count == 3


def test_handler_reconnects_after_connection_loss(mock_pika, handler_config):
    """Test that handler automatically reconnects if connection is lost."""
    handler = RabbitMQLogHandler(**handler_config)

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # First publish succeeds
    log_entry1 = {"level": "INFO", "category": "CONNECTION", "message": "Log 1"}
    handler.write_batch([log_entry1])

    # Simulate connection loss
    mock_channel.basic_publish.side_effect = [Exception("Connection lost"), None]

    # Second publish triggers reconnect
    log_entry2 = {"level": "INFO", "category": "CONNECTION", "message": "Log 2"}

    handler.write_batch([log_entry2])

    # Verify reconnection was attempted (new connection created)
    assert mock_pika.BlockingConnection.call_count >= 2


def test_handler_uses_exponential_backoff_on_retry(handler_config):
    """Test that handler uses exponential backoff when retrying connection."""
    with patch("src.logging.handlers.rabbitmq.pika") as mock_pika:
        with patch("src.logging.handlers.rabbitmq.time.sleep") as mock_sleep:
            # Simulate 3 connection failures, then success
            mock_pika.BlockingConnection.side_effect = [
                Exception("Connection refused"),
                Exception("Connection refused"),
                Exception("Connection refused"),
                MagicMock(),  # Success on 4th attempt
            ]

            RabbitMQLogHandler(**handler_config)

            # Verify exponential backoff delays
            calls = mock_sleep.call_args_list
            assert len(calls) >= 3

            # Base delay 1s, backoff 2x, max 10s
            delays = [call[0][0] for call in calls]
            assert delays[0] == pytest.approx(1.0, abs=0.1)  # 1s
            assert delays[1] == pytest.approx(2.0, abs=0.1)  # 2s
            assert delays[2] == pytest.approx(4.0, abs=0.1)  # 4s


def test_handler_gives_up_after_max_retries(handler_config, capsys):
    """Test that handler gives up after maximum retry attempts."""
    with patch("src.logging.handlers.rabbitmq.pika") as mock_pika:
        with patch("src.logging.handlers.rabbitmq.time.sleep"):
            # Simulate persistent connection failure
            mock_pika.BlockingConnection.side_effect = Exception("Connection refused")

            RabbitMQLogHandler(**handler_config, fallback_to_console=True)

            # Verify warning logged
            captured = capsys.readouterr()
            assert "Failed to connect to RabbitMQ" in captured.err
            assert "retries" in captured.err.lower()


def test_handler_respects_max_delay_cap(handler_config):
    """Test that exponential backoff respects max delay cap."""
    with patch("src.logging.handlers.rabbitmq.pika") as mock_pika:
        with patch("src.logging.handlers.rabbitmq.time.sleep") as mock_sleep:
            # Simulate many failures to test max delay
            mock_pika.BlockingConnection.side_effect = [Exception("Connection refused")] * 10

            try:
                RabbitMQLogHandler(**handler_config)
            except Exception:
                pass  # Expected to fail after retries

            # Verify no delay exceeds max_delay (10s)
            calls = mock_sleep.call_args_list
            for call in calls:
                delay = call[0][0]
                assert delay <= 10.0


def test_handler_closes_connection_on_shutdown(mock_pika, handler_config):
    """Test that handler properly closes connection on shutdown."""
    handler = RabbitMQLogHandler(**handler_config)

    mock_connection = mock_pika.BlockingConnection.return_value

    # Shutdown handler
    handler.close()

    # Verify connection was closed
    mock_connection.close.assert_called_once()


def test_handler_includes_all_log_fields_in_message(mock_pika, handler_config):
    """Test that published message includes all log entry fields."""
    handler = RabbitMQLogHandler(**handler_config)

    log_entry = {
        "timestamp": "2025-10-15T10:30:00Z",
        "level": "ERROR",
        "category": "SECURITY",
        "message": "Authentication failed",
        "correlation_id": "req-456",
        "user_id": "admin",
        "error_type": "AuthError",
        "schema_version": "1.0.0",
    }

    handler.write_batch([log_entry])

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # Verify published message contains all fields
    call_args = mock_channel.basic_publish.call_args
    body = call_args[1]["body"]
    parsed = json.loads(body)

    assert parsed["timestamp"] == "2025-10-15T10:30:00Z"
    assert parsed["level"] == "ERROR"
    assert parsed["category"] == "SECURITY"
    assert parsed["message"] == "Authentication failed"
    assert parsed["correlation_id"] == "req-456"
    assert parsed["user_id"] == "admin"
    assert parsed["error_type"] == "AuthError"
    assert parsed["schema_version"] == "1.0.0"


def test_handler_handles_missing_category_gracefully(mock_pika, handler_config):
    """Test that handler handles missing category field gracefully."""
    handler = RabbitMQLogHandler(**handler_config)

    log_entry = {
        "timestamp": "2025-10-15T10:30:00Z",
        "level": "INFO",
        "message": "Log without category",
    }

    # Should not crash
    handler.write_batch([log_entry])

    mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value

    # Verify routing key uses default for missing category
    call_args = mock_channel.basic_publish.call_args
    routing_key = call_args[1]["routing_key"]
    assert routing_key == "INFO.UNKNOWN"  # Default category
