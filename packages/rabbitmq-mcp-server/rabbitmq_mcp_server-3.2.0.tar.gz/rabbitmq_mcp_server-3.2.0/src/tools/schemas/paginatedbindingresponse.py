"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from typing import Any

from pydantic import BaseModel, Field


class PaginatedBindingResponse(BaseModel):
    items: list[Any] = Field(...)
    pagination: str = Field(...)
