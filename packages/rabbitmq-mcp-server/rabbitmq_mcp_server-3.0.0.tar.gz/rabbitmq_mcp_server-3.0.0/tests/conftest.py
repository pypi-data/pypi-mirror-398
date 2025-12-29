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

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"

# Ensure both the project root and src/ directory are importable without installation.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture(autouse=True)
def _set_env_defaults(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Garante valores padrão de conexão para os testes."""
    env_defaults = {
        "AMQP_HOST": "localhost",
        "AMQP_PORT": "5672",
        "AMQP_USER": "guest",
        "AMQP_PASSWORD": "guest",
        "AMQP_VHOST": "/",
    }
    for key, value in env_defaults.items():
        monkeypatch.setenv(key, value)
    yield


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT
