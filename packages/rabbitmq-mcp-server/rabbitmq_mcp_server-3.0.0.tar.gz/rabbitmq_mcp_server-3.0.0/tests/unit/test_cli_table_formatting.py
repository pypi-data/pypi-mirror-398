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

from cli.commands import binding as binding_cmd
from cli.commands import exchange as exchange_cmd
from cli.commands import queue as queue_cmd
from cli.commands.shared import format_table_output


def _header_sequence(output: str) -> list[str]:
    header_line = output.splitlines()[0]
    return [part.strip() for part in header_line.strip().strip("|").split("|")]


def test_queue_table_column_ordering() -> None:
    payload: list[dict[str, object]] = [
        {
            "name": "orders.queue",
            "vhost": "/",
            "messages": 10,
            "consumers": 3,
            "state": "running",
            "messages_ready": 8,
            "messages_unacknowledged": 2,
            "memory": 1024,
        }
    ]

    base_output = format_table_output(payload, queue_cmd.BASE_COLUMNS, footer="footer")
    verbose_output = format_table_output(payload, queue_cmd.VERBOSE_COLUMNS, footer="footer")

    assert _header_sequence(base_output) == [header for header, _ in queue_cmd.BASE_COLUMNS]
    assert _header_sequence(verbose_output) == [header for header, _ in queue_cmd.VERBOSE_COLUMNS]


def test_exchange_table_column_ordering() -> None:
    payload: list[dict[str, object]] = [
        {
            "name": "orders.exchange",
            "vhost": "/",
            "type": "topic",
            "durable": True,
            "auto_delete": False,
            "internal": False,
            "bindings_count": 2,
            "message_stats": {"publish_in": 5, "publish_out": 5},
        }
    ]

    base_output = format_table_output(payload, exchange_cmd.BASE_COLUMNS, footer="footer")
    verbose_output = format_table_output(payload, exchange_cmd.VERBOSE_COLUMNS, footer="footer")

    assert _header_sequence(base_output) == [header for header, _ in exchange_cmd.BASE_COLUMNS]
    assert _header_sequence(verbose_output) == [
        header for header, _ in exchange_cmd.VERBOSE_COLUMNS
    ]


def test_binding_table_column_ordering() -> None:
    payload: list[dict[str, object]] = [
        {
            "source": "orders.exchange",
            "destination": "orders.queue",
            "destination_type": "queue",
            "routing_key": "order.created",
            "vhost": "/",
        }
    ]

    output = format_table_output(payload, binding_cmd.BASE_COLUMNS, footer="footer")

    assert _header_sequence(output) == [header for header, _ in binding_cmd.BASE_COLUMNS]
