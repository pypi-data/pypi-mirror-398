"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from typing import Any

from pydantic import BaseModel, Field


class Queue(BaseModel):
    name: str = Field(...)
    vhost: str = Field(...)
    durable: bool | None = Field(None)
    auto_delete: bool | None = Field(None)
    exclusive: bool | None = Field(None)
    arguments: dict[str, Any] | None = Field(default=None)
    messages: int | None = Field(None)
    messages_ready: int | None = Field(None)
    messages_unacknowledged: int | None = Field(None)
    consumers: int | None = Field(None)
    memory: int | None = Field(None)
    state: str | None = Field(None)
