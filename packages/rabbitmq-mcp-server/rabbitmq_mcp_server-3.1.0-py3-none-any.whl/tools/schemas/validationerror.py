"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    code: str = Field(...)
    message: str = Field(...)
    field: str | None = Field(None)
    expected: str | None = Field(None)
    actual: str | None = Field(None)
