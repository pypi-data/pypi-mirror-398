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

from .parser import OpenAPIParseError, parse_openapi_spec


class OperationMetadata:
    def __init__(self, operation_id: str, path: str, method: str, spec: dict[str, Any]):
        self.operation_id = operation_id
        self.path = path
        self.method = method
        self.spec = spec


class OperationRegistry:
    def __init__(self, openapi_paths: list[str]):
        self._operations: dict[str, OperationMetadata] = {}
        self._loaded = False
        self._openapi_paths = openapi_paths
        self._load_operations()

    def _load_operations(self) -> None:
        for path in self._openapi_paths:
            try:
                spec = parse_openapi_spec(path)
            except OpenAPIParseError as e:
                raise RuntimeError(f"Failed to load OpenAPI spec {path}: {e}")
            for api_path, methods in spec.get("paths", {}).items():
                for method, op in methods.items():
                    op_id = op.get("operationId")
                    if op_id:
                        self._operations[op_id] = OperationMetadata(
                            operation_id=op_id, path=api_path, method=method, spec=op
                        )
        self._loaded = True

    def get_operation(self, operation_id: str) -> OperationMetadata | None:
        return self._operations.get(operation_id)

    def list_operations(self, tag: str | None = None) -> list[OperationMetadata]:
        if tag:
            return [op for op in self._operations.values() if tag in op.spec.get("tags", [])]
        return list(self._operations.values())
