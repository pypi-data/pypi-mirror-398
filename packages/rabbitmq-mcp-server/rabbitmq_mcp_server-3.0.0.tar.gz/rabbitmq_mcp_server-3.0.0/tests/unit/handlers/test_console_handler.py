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

import io
import json
from contextlib import redirect_stderr

import pytest

from src.logging.handlers.console import ConsoleLogHandler


@pytest.fixture
def handler_and_buffer():
    buffer = io.StringIO()
    handler = ConsoleLogHandler(stream=buffer)
    return handler, buffer


def _read_output(buffer: io.StringIO):
    buffer.seek(0)
    return [json.loads(line) for line in buffer.read().splitlines() if line]


def test_console_handler_writes_to_stderr(handler_and_buffer):
    handler, buffer = handler_and_buffer

    handler.write_batch([{"event": "test"}])

    output = buffer.getvalue().strip()
    assert output


def test_console_handler_writes_json_format(handler_and_buffer):
    handler, buffer = handler_and_buffer

    handler.write_batch([{"event": "first"}, {"event": "second", "value": 2}])

    records = _read_output(buffer)
    assert records == [
        {"event": "first"},
        {"event": "second", "value": 2},
    ]


def test_console_handler_never_raises_exception():
    handler = ConsoleLogHandler()

    buffer = io.StringIO()
    with redirect_stderr(buffer):
        handler.write_batch([{"event": "test"}])

    with redirect_stderr(io.StringIO()):
        handler.write_batch([{"event": "test"}])
