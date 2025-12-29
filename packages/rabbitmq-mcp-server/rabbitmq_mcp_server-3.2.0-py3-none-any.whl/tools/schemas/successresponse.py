"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    status: str | None = Field(None)
    message: str | None = Field(None)
