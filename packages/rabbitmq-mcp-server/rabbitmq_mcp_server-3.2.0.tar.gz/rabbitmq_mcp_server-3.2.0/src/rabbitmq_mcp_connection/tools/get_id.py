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

"""Implementação do MCP tool get-id."""

from typing import Any

from rabbitmq_mcp_connection.schemas.mcp import MCPError, MCPToolResult
from rabbitmq_mcp_connection.tools.contracts import load_connection_operations


class OperationNotFoundError(KeyError):
    """Erro quando uma operação solicitada não existe."""


def get_operation_schema(operation_id: str) -> dict[str, Any]:
    operations = load_connection_operations()
    if operation_id not in operations:
        raise OperationNotFoundError(operation_id)

    schema = operations[operation_id]
    return schema.model_dump(by_alias=True)


def handle_get_id(operation_id: str) -> MCPToolResult:
    try:
        schema = get_operation_schema(operation_id)
        return MCPToolResult(success=True, result={"schema": schema})
    except OperationNotFoundError as exc:
        return MCPToolResult(
            success=False,
            error=MCPError(
                code="OPERATION_NOT_FOUND",
                message=f"Operation '{exc.args[0]}' not found",
            ),
        )


__all__ = ["handle_get_id", "get_operation_schema", "OperationNotFoundError"]
