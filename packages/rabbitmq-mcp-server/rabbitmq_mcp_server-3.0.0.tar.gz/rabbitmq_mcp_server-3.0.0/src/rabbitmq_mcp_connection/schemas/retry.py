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

"""Componentes de retry/backoff usados no gerenciamento de conexão."""

from pydantic import BaseModel, Field


class RetryStats(BaseModel):
    attempts: int = Field(ge=0)
    current_delay: float = Field(gt=0)
    max_delay: float = Field(gt=0)


class RetryPolicy(BaseModel):
    """Política de retry com backoff exponencial."""

    initial_delay: float = Field(default=1.0, gt=0, le=60)
    backoff_factor: float = Field(default=2.0, gt=1.0, le=10.0)
    max_delay: float = Field(default=60.0, gt=0, le=3600)
    current_delay: float = Field(default=1.0, gt=0)
    attempts: int = Field(default=0, ge=0)

    def next_delay(self) -> float:
        delay = min(self.current_delay, self.max_delay)
        self.current_delay = min(self.current_delay * self.backoff_factor, self.max_delay)
        self.attempts += 1
        return delay

    def reset(self) -> None:
        self.current_delay = self.initial_delay
        self.attempts = 0

    def get_stats(self) -> RetryStats:
        return RetryStats(
            attempts=self.attempts,
            current_delay=self.current_delay,
            max_delay=self.max_delay,
        )
