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

"""Schemas auxiliares para integração com MCP."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=5, ge=1, le=50)


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total: int


class SearchItem(BaseModel):
    operation_id: str
    score: float
    metadata: dict[str, Any] | None = None


class SearchResult(BaseModel):
    items: list[SearchItem]
    pagination: PaginationMetadata


class MCPError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class MCPToolResult(BaseModel):
    success: bool
    result: dict[str, Any] | None = None
    error: MCPError | None = None
    metadata: dict[str, Any] | None = None


class OperationSchema(BaseModel):
    operation_id: str
    name: str
    description: str
    category: str
    async_mode: bool = Field(alias="async")
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    examples: list[dict[str, Any]] | None = None
    errors: list[dict[str, Any]] | None = None

    model_config = ConfigDict(populate_by_name=True)


__all__ = [
    "PaginationParams",
    "PaginationMetadata",
    "SearchResult",
    "SearchItem",
    "MCPToolResult",
    "MCPError",
    "OperationSchema",
]
