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

"""Exchange-related CLI commands."""

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
from utils.errors import RabbitMQError, ValidationError
from utils.validation import validate_exchange_type, validate_name

ExchangeColumn = tuple[str, str]

BASE_COLUMNS: list[ExchangeColumn] = [
    ("Name", "name"),
    ("VHost", "vhost"),
    ("Type", "type"),
    ("Durable", "durable"),
    ("Auto Delete", "auto_delete"),
    ("Internal", "internal"),
    ("Bindings", "bindings_count"),
]

VERBOSE_COLUMNS: list[ExchangeColumn] = BASE_COLUMNS + [
    ("Publish In", "message_stats.publish_in"),
    ("Publish Out", "message_stats.publish_out"),
]


def _parse_json_arguments(
    _: click.Context, param: click.Parameter, value: str | None
) -> dict[str, object]:
    if value in (None, ""):
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - click handles display
        raise click.BadParameter("Arguments must be valid JSON", param=param) from exc
    if not isinstance(data, dict):
        raise click.BadParameter("Arguments must be a JSON object", param=param)
    return data


@click.group()
def exchange() -> None:
    """Exchange operations."""


@exchange.command("list")
@connection_options
@pagination_options
@output_options
@click.option("--vhost", default=None, help="Filter exchanges by virtual host")
def list_exchanges(  # pylint: disable=too-many-arguments
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
    """List exchanges with client-side pagination."""

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
        payload = execute_operation("exchanges.list", connection, pagination)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover - unexpected failure
        raise click.ClickException(str(exc)) from exc

    pagination_meta = payload.get("pagination", {})
    footer = (
        f"Page {pagination_meta.get('page', page)} of {pagination_meta.get('totalPages', '?')} "
        f"(Total: {pagination_meta.get('totalItems', '?')})"
    )
    columns = VERBOSE_COLUMNS if verbose else BASE_COLUMNS

    if output_format.lower() == "json":
        click.echo(format_json_output(payload))
        return

    click.echo(format_table_output(payload.get("items", []), columns, footer))


@exchange.command("create")
@connection_options
@click.option("--vhost", default=None, help="Target virtual host (defaults to connection vhost)")
@click.option("--name", required=True, help="Exchange name (alphanumeric, dot, dash or underscore)")
@click.option(
    "--type", "exchange_type", required=True, help="Exchange type: direct|topic|fanout|headers"
)
@click.option(
    "--durable/--no-durable", default=False, show_default=True, help="Create exchange as durable"
)
@click.option(
    "--auto-delete/--no-auto-delete",
    default=False,
    show_default=True,
    help="Auto-delete exchange when unused",
)
@click.option(
    "--internal/--no-internal", default=False, show_default=True, help="Create internal exchange"
)
@click.option(
    "--arguments",
    callback=_parse_json_arguments,
    default=None,
    help='Additional exchange arguments as JSON (e.g. \'{"alternate-exchange": "dead.letter"}\')',
)
def create_exchange(  # pylint: disable=too-many-arguments
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    connection_vhost: str,
    vhost: str | None,
    name: str,
    exchange_type: str,
    durable: bool,
    auto_delete: bool,
    internal: bool,
    arguments: dict[str, object],
) -> None:
    """Create a new exchange."""

    try:
        validate_name(name)
        normalized_type = exchange_type.lower()
        validate_exchange_type(normalized_type)
    except ValidationError as exc:
        hint = "--type" if exc.field == "type" else "--name"
        raise click.BadParameter(exc.to_user_message(), param_hint=hint) from exc

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
            "name": name,
            "type": normalized_type,
            "durable": durable,
            "auto_delete": auto_delete,
            "internal": internal,
            "arguments": arguments,
        }
    )

    try:
        result = execute_operation("exchanges.create", payload, pagination=None)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise click.ClickException(str(exc)) from exc

    target_vhost = vhost or payload["connection_vhost"]
    exchange_name = result.get("name", name)
    resolved_type = result.get("type", normalized_type)
    click.echo(
        f"Exchange '{exchange_name}' (type {resolved_type}) created in vhost '{target_vhost}'"
    )


@exchange.command("delete")
@connection_options
@click.option("--vhost", default=None, help="Target virtual host (defaults to connection vhost)")
@click.option("--name", required=True, help="Exchange name to delete")
def delete_exchange(  # pylint: disable=too-many-arguments
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    connection_vhost: str,
    vhost: str | None,
    name: str,
) -> None:
    """Delete an exchange once bindings are removed."""

    payload = build_connection_payload(
        host=host,
        port=port,
        user=user,
        password=password,
        connection_vhost=connection_vhost,
        use_tls=use_tls,
        vhost=vhost,
    )

    payload.update({"name": name})

    try:
        result = execute_operation("exchanges.delete", payload, pagination=None)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise click.ClickException(str(exc)) from exc

    target_vhost = vhost or payload["connection_vhost"]
    binding_count = result.get("binding_count", 0)
    suffix = "" if not binding_count else f" (bindings removed: {binding_count})"
    click.echo(f"Exchange '{name}' deleted from vhost '{target_vhost}'{suffix}")


__all__ = ["exchange"]
