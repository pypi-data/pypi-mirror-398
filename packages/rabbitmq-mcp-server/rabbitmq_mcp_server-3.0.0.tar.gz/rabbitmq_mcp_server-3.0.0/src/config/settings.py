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

import os
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    host: str
    port: int = 15672
    user: str
    password: str
    vhost: str = "/"
    use_tls: bool = False
    crud_timeout: int = 5
    list_timeout: int = 30
    search_timeout: float = 0.1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @classmethod
    def from_yaml(cls, path: str = "config/config.yaml") -> RabbitMQSettings:  # noqa: F821
        if not os.path.exists(path):
            # Allow BaseSettings to resolve values from environment variables when YAML is absent.
            return cls(**{})

        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        # Support nested rabbitmq configuration blocks while preserving direct mapping usage.
        data = raw.get("rabbitmq", raw)

        normalized: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                normalized[key] = os.path.expandvars(value)
            else:
                normalized[key] = value

        return cls(**normalized)

    def validate_timeouts(self) -> None:
        assert 1 <= self.crud_timeout <= 60, "crud_timeout must be between 1 and 60 seconds"
        assert 1 <= self.list_timeout <= 60, "list_timeout must be between 1 and 60 seconds"
        assert 0.1 <= self.search_timeout <= 60, "search_timeout must be between 0.1 and 60 seconds"
        assert self.host and self.port, "host and port are required"
