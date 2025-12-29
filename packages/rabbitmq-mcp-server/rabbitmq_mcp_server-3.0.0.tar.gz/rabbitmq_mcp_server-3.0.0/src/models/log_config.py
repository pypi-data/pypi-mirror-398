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

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .log_entry import LogLevel

__all__ = ["RotationWhen", "RabbitMQConfig", "LogConfig"]

DEFAULT_OUTPUT_FILE = "./logs/rabbitmq-mcp-{date}.log"
DEFAULT_ROTATION_MAX_BYTES = 100 * 1024 * 1024  # 100 MB
DEFAULT_ASYNC_QUEUE_SIZE = 10_000
MIN_ASYNC_QUEUE_SIZE = 100
MIN_ASYNC_FLUSH_INTERVAL = 0.01
MIN_BATCH_SIZE = 1
FILE_PERMISSION_PATTERN = r"^[0-7]{3}$"


class RotationWhen(str, Enum):
    MIDNIGHT = "midnight"
    HOURLY = "H"
    MINUTELY = "M"


class RabbitMQConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    host: str = "localhost"
    port: int = Field(5672, ge=1, le=65535)
    vhost: str = "/"
    username: str = "guest"
    password: str = "guest"
    exchange: str = "logs"
    exchange_type: str = "topic"
    routing_key_pattern: str = "{level}.{category}"
    durable: bool = True


class LogConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    log_level: LogLevel = LogLevel.INFO
    output_file: str = DEFAULT_OUTPUT_FILE
    rotation_when: RotationWhen = RotationWhen.MIDNIGHT
    rotation_interval: int = Field(1, gt=0)
    rotation_max_bytes: int = Field(DEFAULT_ROTATION_MAX_BYTES, gt=0)
    retention_days: int = Field(30, ge=1)
    compression_enabled: bool = True
    async_queue_size: int = Field(DEFAULT_ASYNC_QUEUE_SIZE, ge=MIN_ASYNC_QUEUE_SIZE)
    async_flush_interval: float = Field(0.1, ge=MIN_ASYNC_FLUSH_INTERVAL)
    batch_size: int = Field(100, ge=MIN_BATCH_SIZE)
    file_permissions: str = Field("600", pattern=FILE_PERMISSION_PATTERN)
    fallback_to_console: bool = True
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)

    @field_validator("async_queue_size")
    @classmethod
    def validate_queue_size(cls, value: int) -> int:
        if value < MIN_ASYNC_QUEUE_SIZE:
            raise ValueError("async_queue_size must be >= 100")
        return value

    @field_validator("async_flush_interval")
    @classmethod
    def validate_flush_interval(cls, value: float) -> float:
        if value < MIN_ASYNC_FLUSH_INTERVAL:
            raise ValueError("async_flush_interval must be >= 0.01")
        return value

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, value: int) -> int:
        if value < MIN_BATCH_SIZE:
            raise ValueError("batch_size must be >= 1")
        return value

    @field_validator("file_permissions")
    @classmethod
    def validate_file_permissions(cls, value: str) -> str:
        if len(value) != 3:
            raise ValueError("file_permissions must be a three digit octal string")
        return value
