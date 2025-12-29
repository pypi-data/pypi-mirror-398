"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from typing import Any

from pydantic import BaseModel, Field


class OperationError(BaseModel):
    code: str = Field(...)
    message: str = Field(...)
    suggestion: str | None = Field(None)
    details: dict[str, Any] | None = Field(default=None)
