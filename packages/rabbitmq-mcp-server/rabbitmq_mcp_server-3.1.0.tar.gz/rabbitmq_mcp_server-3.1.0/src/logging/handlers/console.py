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

import sys
from collections.abc import Iterable
from typing import IO, Any

import orjson


class ConsoleLogHandler:
    def __init__(self, stream: IO[str] | None = None) -> None:
        self._stream = stream or sys.stderr

    def write_batch(self, batch: Iterable[dict[str, Any]]) -> None:
        for item in batch:
            try:
                serialized = orjson.dumps(item).decode("utf-8")
                self._stream.write(serialized)
                self._stream.write("\n")
            except Exception:
                # Console handler deve ser à prova de falhas.
                continue
        try:
            self._stream.flush()
        except Exception:
            pass
