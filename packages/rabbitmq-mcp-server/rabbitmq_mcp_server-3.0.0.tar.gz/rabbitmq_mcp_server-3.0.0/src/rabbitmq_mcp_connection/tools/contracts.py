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

"""Utilitários para carregar contratos MCP."""

import json
from functools import lru_cache
from pathlib import Path

from rabbitmq_mcp_connection.schemas.mcp import OperationSchema

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"
CONNECTION_OPERATIONS_PATH = CONTRACTS_DIR / "connection-operations.json"


@lru_cache(maxsize=1)
def load_connection_operations() -> dict[str, OperationSchema]:
    if not CONNECTION_OPERATIONS_PATH.exists():
        raise FileNotFoundError(f"Arquivo de contrato não encontrado: {CONNECTION_OPERATIONS_PATH}")

    data = json.loads(CONNECTION_OPERATIONS_PATH.read_text(encoding="utf-8"))
    operations = {}
    for entry in data.get("operations", []):
        schema = OperationSchema(**entry)
        operations[schema.operation_id] = schema
    return operations


__all__ = ["load_connection_operations"]
