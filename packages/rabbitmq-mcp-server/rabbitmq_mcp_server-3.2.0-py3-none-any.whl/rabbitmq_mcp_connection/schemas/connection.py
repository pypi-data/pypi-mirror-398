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

"""Schemas centrais relacionados à conexão RabbitMQ."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class ConnectionState(str, Enum):
    """Estados possíveis de uma conexão AMQP."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

    @property
    def is_connected(self) -> bool:
        return self is ConnectionState.CONNECTED


class ConnectionConfig(BaseModel):
    """Parâmetros necessários para estabelecer uma conexão AMQP."""

    model_config = ConfigDict(validate_assignment=True)

    host: str = Field(
        default="localhost",
        min_length=1,
        description="Hostname ou endereço IP do servidor RabbitMQ.",
    )
    port: int = Field(
        default=5672,
        ge=1,
        le=65535,
        description="Porta AMQP exposta pelo servidor RabbitMQ.",
    )
    user: str = Field(
        default="guest",
        min_length=1,
        description="Usuário utilizado para autenticação.",
    )
    password: str = Field(
        default="guest",
        min_length=1,
        repr=False,
        description="Senha utilizada para autenticação (nunca exibida em repr/logs).",
    )
    vhost: str = Field(
        default="/",
        min_length=1,
        description="Virtual host que será utilizado durante a conexão.",
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Tempo máximo (em segundos) para estabelecer a conexão.",
    )
    heartbeat: int = Field(
        default=60,
        ge=0,
        le=3600,
        description="Intervalo do heartbeat AMQP em segundos (0 desativa).",
    )

    @field_validator("vhost")
    @classmethod
    def _validate_vhost(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("Virtual host deve iniciar com '/'.")
        return value

    def get_connection_url(self, sanitize: bool = True) -> str:
        """Gera a URL de conexão em formato amqp://user:password@host:port/vhost.

        Quando *sanitize* for verdadeiro (padrão) a senha será substituída por ***.
        """

        password: str | None
        if sanitize:
            password = "***"
        else:
            password = self.password

        return f"amqp://{self.user}:{password}@{self.host}:{self.port}{self.vhost}"

    def __repr__(self) -> str:  # pragma: no cover - repr customizado simples
        fields: dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "vhost": self.vhost,
            "timeout": self.timeout,
            "heartbeat": self.heartbeat,
        }
        fields_repr = ", ".join(f"{key}={value!r}" for key, value in fields.items())
        return f"ConnectionConfig({fields_repr})"


class ConnectResult(BaseModel):
    connected: bool
    connection_url: str
    latency_ms: float
    server_properties: dict[str, Any] | None = None


class DisconnectResult(BaseModel):
    disconnected: bool
    graceful: bool
    duration_ms: float


class HealthStatus(BaseModel):
    is_connected: bool
    broker_available: bool
    latency_ms: float
    last_check: datetime
    error_message: str | None = None

    @computed_field(return_type=bool)
    def is_healthy(self) -> bool:
        return self.is_connected and self.broker_available


class ConnectionStatusResult(BaseModel):
    state: ConnectionState
    connection_url: str
    connected_since: datetime | None = None
    retry_attempts: int
    next_retry_in_seconds: float | None = None

    def __getitem__(self, item: str) -> Any:
        return self.model_dump()[item]


class PoolStats(BaseModel):
    max_size: int
    total_connections: int
    in_use: int
    available: int
    waiting_for_connection: int
    acquire_timeout_seconds: int
