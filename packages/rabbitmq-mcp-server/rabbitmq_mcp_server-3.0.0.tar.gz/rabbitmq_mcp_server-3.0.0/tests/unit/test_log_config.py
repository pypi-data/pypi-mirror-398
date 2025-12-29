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

from typing import Any

import pytest
from pydantic import ValidationError

from models.log_config import LogConfig, RotationWhen


@pytest.fixture()
def base_payload() -> dict[str, Any]:
    return {}


def test_log_config_defaults(base_payload: dict[str, Any]):
    config = LogConfig(**base_payload)
    assert config.log_level == "INFO"
    assert config.output_file == "./logs/rabbitmq-mcp-{date}.log"
    assert config.rotation_when == RotationWhen.MIDNIGHT
    assert config.rotation_interval == 1
    assert config.rotation_max_bytes == 104_857_600
    assert config.retention_days == 30
    assert config.compression_enabled is True
    assert config.async_queue_size == 10_000
    assert config.async_flush_interval == 0.1
    assert config.batch_size == 100
    assert config.file_permissions == "600"
    assert config.fallback_to_console is True


def test_log_config_validates_minimums(base_payload: dict[str, Any]):
    config = LogConfig(
        **base_payload,
        retention_days=1,
        async_queue_size=10_000,
        async_flush_interval=0.05,
        batch_size=10,
    )
    assert config.retention_days == 1
    assert config.async_queue_size == 10_000
    assert config.async_flush_interval == 0.05
    assert config.batch_size == 10


@pytest.mark.parametrize("retention_days", [0, -1])
def test_log_config_rejects_invalid_retention(base_payload: dict[str, Any], retention_days: int):
    with pytest.raises(ValidationError):
        LogConfig(**base_payload, retention_days=retention_days)


@pytest.mark.parametrize("queue_size", [0, 99])
def test_log_config_requires_queue_size_over_minimum(base_payload: dict[str, Any], queue_size: int):
    with pytest.raises(ValidationError):
        LogConfig(**base_payload, async_queue_size=queue_size)


@pytest.mark.parametrize("flush_interval", [0.0, -0.1])
def test_log_config_rejects_flush_interval_under_minimum(
    base_payload: dict[str, Any], flush_interval: float
):
    with pytest.raises(ValidationError):
        LogConfig(**base_payload, async_flush_interval=flush_interval)


@pytest.mark.parametrize("batch_size", [0, -5])
def test_log_config_rejects_invalid_batch_size(base_payload: dict[str, Any], batch_size: int):
    with pytest.raises(ValidationError):
        LogConfig(**base_payload, batch_size=batch_size)


def test_log_config_validates_rotation_max_bytes(base_payload: dict[str, Any]):
    with pytest.raises(ValidationError):
        LogConfig(**base_payload, rotation_max_bytes=0)


def test_log_config_validates_permissions_format(base_payload: dict[str, Any]):
    with pytest.raises(ValidationError):
        LogConfig(**base_payload, file_permissions="7000")


def test_log_config_allows_rabbitmq_settings(base_payload: dict[str, Any]):
    config = LogConfig(
        **base_payload,
        rabbitmq={
            "enabled": True,
            "host": "localhost",
            "port": 5672,
            "vhost": "/",
            "username": "guest",
            "password": "guest",
            "exchange": "logs",
            "routing_key_pattern": "{level}.{category}",
        },
    )
    assert config.rabbitmq.enabled is True
    assert config.rabbitmq.host == "localhost"


def test_log_config_rejects_invalid_rabbitmq_port(base_payload: dict[str, Any]):
    with pytest.raises(ValidationError):
        LogConfig(
            **base_payload,
            rabbitmq={
                "enabled": True,
                "host": "localhost",
                "port": 0,
                "vhost": "/",
                "username": "guest",
                "password": "guest",
                "exchange": "logs",
                "routing_key_pattern": "{level}.{category}",
            },
        )
