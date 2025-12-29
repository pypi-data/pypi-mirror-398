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

"""Schemas Pydantic para validação de dados.

Este pacote agrega todos os schemas utilizados na feature de conexão RabbitMQ.
Os módulos exportados aqui são referenciados nos tasks T005-T023 da feature
`002-basic-rabbitmq-connection`.
"""

from .connection import ConnectionConfig, ConnectionState  # noqa: F401
from .retry import RetryPolicy, RetryStats  # noqa: F401

__all__ = [
    "ConnectionConfig",
    "ConnectionState",
    "RetryPolicy",
    "RetryStats",
]
