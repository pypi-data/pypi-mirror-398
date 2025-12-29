"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from typing import Any

from pydantic import BaseModel, Field


class QueueCreateRequest(BaseModel):
    durable: bool | None = Field(None)
    auto_delete: bool | None = Field(None)
    exclusive: bool | None = Field(None)
    arguments: dict[str, Any] | None = Field(default=None)
