"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from typing import Any

from pydantic import BaseModel, Field


class Binding(BaseModel):
    source: str = Field(...)
    destination: str = Field(...)
    destination_type: str = Field(...)
    vhost: str = Field(...)
    routing_key: str = Field(...)
    arguments: dict[str, Any] | None = Field(default=None)
    properties_key: str | None = Field(None)
