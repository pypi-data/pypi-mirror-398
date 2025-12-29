"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from pydantic import BaseModel, Field


class PaginationMetadata(BaseModel):
    page: int = Field(...)
    pageSize: int = Field(...)
    totalItems: int = Field(...)
    totalPages: int = Field(...)
    hasNextPage: bool = Field(...)
    hasPreviousPage: bool = Field(...)
