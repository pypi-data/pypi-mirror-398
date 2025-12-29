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

"""
MCP Tool: Get Operation Schema by ID
Implements get_id(endpoint_id: str) -> OperationSchema
"""

import os
from typing import Any

from pydantic import BaseModel

from tools.openapi.operation_registry import OperationRegistry


class OperationSchema(BaseModel):
    operation_id: str
    summary: str
    description: str
    parameters: Any
    responses: Any
    examples: Any | None = None


class ErrorSchema(BaseModel):
    error: str
    message: str


OPENAPI_PATHS = [
    os.path.join(
        os.path.dirname(__file__),
        "../../specs/003-essential-topology-operations/contracts/queue-operations.yaml",
    ),
    os.path.join(
        os.path.dirname(__file__),
        "../../specs/003-essential-topology-operations/contracts/exchange-operations.yaml",
    ),
    os.path.join(
        os.path.dirname(__file__),
        "../../specs/003-essential-topology-operations/contracts/binding-operations.yaml",
    ),
]


def get_id(endpoint_id: str) -> OperationSchema:
    registry = OperationRegistry(OPENAPI_PATHS)
    op = registry.get_operation(endpoint_id)
    if not op:
        raise ValueError(f"Operation ID '{endpoint_id}' not found.")
    spec = op.spec
    parameters = spec.get("parameters", [])
    responses = spec.get("responses", {})
    summary = spec.get("summary", "")
    description = spec.get("description", "")
    examples = None
    # Try to extract examples from responses or requestBody if present
    if "requestBody" in spec:
        examples = (
            spec["requestBody"].get("content", {}).get("application/json", {}).get("examples", None)
        )
    return OperationSchema(
        operation_id=endpoint_id,
        summary=summary,
        description=description,
        parameters=parameters,
        responses=responses,
        examples=examples,
    )
