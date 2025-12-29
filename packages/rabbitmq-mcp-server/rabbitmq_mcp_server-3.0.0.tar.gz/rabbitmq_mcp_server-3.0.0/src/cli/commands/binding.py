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

"""Binding-related CLI commands."""

import json

import click

from cli.commands.shared import (
    build_connection_payload,
    build_pagination_payload,
    connection_options,
    execute_operation,
    format_json_output,
    format_table_output,
    output_options,
    pagination_options,
)
from utils.errors import RabbitMQError

BindingColumn = tuple[str, str]

BASE_COLUMNS: list[BindingColumn] = [
    ("Source", "source"),
    ("Destination", "destination"),
    ("Type", "destination_type"),
    ("Routing Key", "routing_key"),
    ("VHost", "vhost"),
]


def _parse_json_arguments(
    _: click.Context, param: click.Parameter, value: str | None
) -> dict[str, object]:
    if value in (None, ""):
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - click renders message
        raise click.BadParameter("Arguments must be valid JSON", param=param) from exc
    if not isinstance(data, dict):
        raise click.BadParameter("Arguments must be a JSON object", param=param)
    return data


@click.group()
def binding() -> None:
    """Binding operations."""


@binding.command("list")
@connection_options
@pagination_options
@output_options
@click.option("--vhost", default=None, help="Filter bindings by virtual host")
def list_bindings(  # pylint: disable=too-many-arguments
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    connection_vhost: str,
    vhost: str | None,
    page: int,
    page_size: int,
    output_format: str,
    verbose: bool,
) -> None:
    """List bindings with client-side pagination."""

    # Verbose flag currently has no additional fields but retained for interface parity.
    _ = verbose

    connection = build_connection_payload(
        host=host,
        port=port,
        user=user,
        password=password,
        connection_vhost=connection_vhost,
        use_tls=use_tls,
        vhost=vhost,
    )
    pagination = build_pagination_payload(page=page, page_size=page_size)

    try:
        payload = execute_operation("bindings.list", connection, pagination)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc)) from exc

    pagination_meta = payload.get("pagination", {})
    footer = (
        f"Page {pagination_meta.get('page', page)} of {pagination_meta.get('totalPages', '?')} "
        f"(Total: {pagination_meta.get('totalItems', '?')})"
    )

    if output_format.lower() == "json":
        click.echo(format_json_output(payload))
        return

    click.echo(format_table_output(payload.get("items", []), BASE_COLUMNS, footer))


@binding.command("create")
@connection_options
@click.option("--vhost", default=None, help="Target virtual host (defaults to connection vhost)")
@click.option("--exchange", required=True, help="Exchange name to bind from")
@click.option("--queue", required=True, help="Queue name to bind to")
@click.option(
    "--routing-key",
    default="",
    show_default=True,
    help="Routing key (use '*' or '#' wildcards for topic exchanges)",
)
@click.option(
    "--arguments",
    callback=_parse_json_arguments,
    default=None,
    help='Additional binding arguments as JSON (e.g. \'{"x-match": "all"}\')',
)
def create_binding(  # pylint: disable=too-many-arguments
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    connection_vhost: str,
    vhost: str | None,
    exchange: str,
    queue: str,
    routing_key: str,
    arguments: dict[str, object],
) -> None:
    """Create a binding between an exchange and a queue."""

    payload = build_connection_payload(
        host=host,
        port=port,
        user=user,
        password=password,
        connection_vhost=connection_vhost,
        use_tls=use_tls,
        vhost=vhost,
    )

    payload.update(
        {
            "exchange": exchange,
            "queue": queue,
            "routing_key": routing_key,
            "arguments": arguments,
        }
    )

    try:
        result = execute_operation("bindings.create", payload, pagination=None)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover - unexpected failure
        raise click.ClickException(str(exc)) from exc

    target_vhost = vhost or payload["connection_vhost"]
    resolved_routing_key = result.get("routing_key", routing_key)
    click.echo(
        f"Binding '{exchange}' -> '{queue}' (routing key '{resolved_routing_key}') created in vhost '{target_vhost}'"
    )


@binding.command("delete")
@connection_options
@click.option("--vhost", default=None, help="Target virtual host (defaults to connection vhost)")
@click.option("--exchange", required=True, help="Exchange name")
@click.option("--queue", required=True, help="Queue name")
@click.option(
    "--properties-key",
    required=True,
    help="Properties key value from the binding list output",
)
def delete_binding(  # pylint: disable=too-many-arguments
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    connection_vhost: str,
    vhost: str | None,
    exchange: str,
    queue: str,
    properties_key: str,
) -> None:
    """Delete a specific binding between an exchange and a queue."""

    payload = build_connection_payload(
        host=host,
        port=port,
        user=user,
        password=password,
        connection_vhost=connection_vhost,
        use_tls=use_tls,
        vhost=vhost,
    )

    payload.update(
        {
            "exchange": exchange,
            "queue": queue,
            "properties_key": properties_key,
        }
    )

    try:
        result = execute_operation("bindings.delete", payload, pagination=None)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise click.ClickException(str(exc)) from exc

    target_vhost = vhost or payload["connection_vhost"]
    resolved_key = result.get("properties_key", properties_key)
    click.echo(
        f"Binding '{exchange}' -> '{queue}' removed from vhost '{target_vhost}' (properties key '{resolved_key}')"
    )


__all__ = ["binding"]
