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

"""Shared helpers for CLI command options and execution."""

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import click

from cli.formatters.json import format_json
from cli.formatters.table import format_table
from tools import call_id as call_id_tool

ConnectionDict = dict[str, Any]
PaginationDict = dict[str, Any]


def connection_options(func: Callable[..., Any]) -> Callable[..., Any]:
    options = [
        click.option(
            "--password",
            envvar="RABBITMQ_PASSWORD",
            required=True,
            hide_input=True,
            help="RabbitMQ password",
        ),
        click.option(
            "--user",
            envvar="RABBITMQ_USER",
            required=True,
            help="RabbitMQ username",
        ),
        click.option(
            "--port",
            envvar="RABBITMQ_PORT",
            default=15672,
            show_default=True,
            type=int,
            help="RabbitMQ management port",
        ),
        click.option(
            "--host",
            envvar="RABBITMQ_HOST",
            required=True,
            help="RabbitMQ host",
        ),
        click.option(
            "--use-tls/--no-use-tls",
            envvar="RABBITMQ_USE_TLS",
            default=False,
            show_default=True,
            help="Use HTTPS when contacting the management API",
        ),
        click.option(
            "--connection-vhost",
            envvar="RABBITMQ_CONNECTION_VHOST",
            default="/",
            show_default=True,
            help="Virtual host used for authentication context",
        ),
    ]

    for option in reversed(options):
        func = option(func)
    return func


def pagination_options(func: Callable[..., Any]) -> Callable[..., Any]:
    options = [
        click.option(
            "--page-size",
            default=50,
            show_default=True,
            type=int,
            help="Items per page (1-200)",
        ),
        click.option(
            "--page",
            default=1,
            show_default=True,
            type=int,
            help="Page number (1-based)",
        ),
    ]

    for option in reversed(options):
        func = option(func)
    return func


def output_options(func: Callable[..., Any]) -> Callable[..., Any]:
    options = [
        click.option(
            "--format",
            "output_format",
            type=click.Choice(["table", "json"], case_sensitive=False),
            default="table",
            show_default=True,
            help="Output format",
        ),
        click.option(
            "--verbose/--no-verbose",
            default=False,
            show_default=True,
            help="Include additional statistics in table output",
        ),
    ]

    for option in reversed(options):
        func = option(func)
    return func


def build_connection_payload(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    connection_vhost: str,
    use_tls: bool,
    vhost: str | None,
) -> ConnectionDict:
    payload: ConnectionDict = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "connection_vhost": connection_vhost or "/",
        "use_tls": use_tls,
    }
    if vhost is not None:
        payload["vhost"] = vhost
    return payload


def build_pagination_payload(*, page: int, page_size: int) -> PaginationDict:
    return {"page": page, "pageSize": page_size}


def execute_operation(
    endpoint: str,
    params: ConnectionDict,
    pagination: PaginationDict | None = None,
) -> dict[str, Any]:
    response = call_id_tool.call_id(endpoint, params=params, pagination=pagination)
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    raise TypeError(f"Unexpected response type: {type(response)!r}")


def format_table_output(
    items: Iterable[dict[str, Any]],
    columns: Sequence[tuple[str, str]],
    footer: str,
) -> str:
    headers = [header for header, _ in columns]
    rows: list[dict[str, Any]] = []
    for item in items:
        row: dict[str, Any] = {}
        for header, key in columns:
            row[header] = _extract_value(item, key)
        rows.append(row)
    table = format_table(rows, headers)
    return f"{table}\n{footer}".strip()


def format_json_output(payload: dict[str, Any]) -> str:
    return format_json(payload)


def _extract_value(item: dict[str, Any], dotted_key: str) -> Any:
    value: Any = item
    for part in dotted_key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
    return value


__all__ = [
    "connection_options",
    "pagination_options",
    "output_options",
    "build_connection_payload",
    "build_pagination_payload",
    "execute_operation",
    "format_table_output",
    "format_json_output",
]
