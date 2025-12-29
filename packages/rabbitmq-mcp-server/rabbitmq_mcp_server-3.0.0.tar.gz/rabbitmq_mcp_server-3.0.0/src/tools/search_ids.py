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
MCP Tool: Semantic Search for Operation IDs
Implements search_ids(query: str, page: int, pageSize: int) -> SearchResult
"""

from pydantic import BaseModel

from tools.vector_db.search import semantic_search


class OperationMatch(BaseModel):
    operation_id: str
    score: float
    summary: str


class SearchResult(BaseModel):
    results: list[OperationMatch]
    page: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasNextPage: bool
    hasPreviousPage: bool


def search_ids(query: str, page: int = 1, pageSize: int = 50) -> SearchResult:
    # Validate pagination
    if page < 1:
        raise ValueError("page must be >= 1")
    if not (1 <= pageSize <= 200):
        raise ValueError("pageSize must be between 1 and 200")
    # Run semantic search
    matches = semantic_search(query, limit=1000)  # Get all possible matches
    totalItems = len(matches)
    totalPages = max(1, (totalItems + pageSize - 1) // pageSize)
    start = (page - 1) * pageSize
    end = start + pageSize
    paged_matches = matches[start:end]
    hasNextPage = page < totalPages
    hasPreviousPage = page > 1
    # Convert to OperationMatch if needed
    results = [
        OperationMatch(**m) if not isinstance(m, OperationMatch) else m for m in paged_matches
    ]
    return SearchResult(
        results=results,
        page=page,
        pageSize=pageSize,
        totalItems=totalItems,
        totalPages=totalPages,
        hasNextPage=hasNextPage,
        hasPreviousPage=hasPreviousPage,
    )
