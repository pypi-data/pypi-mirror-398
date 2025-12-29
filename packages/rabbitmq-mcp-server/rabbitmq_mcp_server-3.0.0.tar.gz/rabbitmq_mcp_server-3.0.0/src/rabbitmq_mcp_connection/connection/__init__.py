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

"""Componentes núcleo de conexão AMQP.

Este pacote fornece classes de alto nível para gerenciamento de conexões com
RabbitMQ incluindo monitoramento, política de retry, pool de conexões e
integração com ferramentas MCP. Os módulos expostos aqui formam a base das
User Stories definidas na feature *002-basic-rabbitmq-connection*.
"""

from .exceptions import (  # noqa: F401
    AuthenticationError,
    ConnectionError,
    ConnectionTimeoutError,
    PoolError,
    PoolTimeoutError,
    VHostNotFoundError,
)
from .health import HealthChecker  # noqa: F401
from .manager import ConnectionManager  # noqa: F401
from .monitor import ConnectionMonitor  # noqa: F401
from .pool import ConnectionPool, PooledConnection  # noqa: F401

__all__ = [
    "AuthenticationError",
    "ConnectionError",
    "ConnectionTimeoutError",
    "ConnectionManager",
    "ConnectionMonitor",
    "ConnectionPool",
    "HealthChecker",
    "PoolError",
    "PoolTimeoutError",
    "PooledConnection",
    "VHostNotFoundError",
]
