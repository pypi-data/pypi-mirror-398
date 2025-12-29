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

"""Queue-related CLI commands."""

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
from utils.validation import validate_name

QueueColumn = tuple[str, str]

BASE_COLUMNS: list[QueueColumn] = [
    ("Name", "name"),
    ("VHost", "vhost"),
    ("Messages", "messages"),
    ("Consumers", "consumers"),
    ("State", "state"),
]

VERBOSE_COLUMNS: list[QueueColumn] = BASE_COLUMNS + [
    ("Ready", "messages_ready"),
    ("Unacked", "messages_unacknowledged"),
    ("Memory", "memory"),
]


def _parse_json_arguments(
    _: click.Context, param: click.Parameter, value: str | None
) -> dict[str, object]:
    if value in (None, ""):
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - click handles error display
        raise click.BadParameter("Arguments must be valid JSON", param=param) from exc
    if not isinstance(data, dict):
        raise click.BadParameter("Arguments must be a JSON object", param=param)
    return data


@click.group()
def queue() -> None:
    """Queue operations."""


@queue.command("list")
@connection_options
@pagination_options
@output_options
@click.option("--vhost", default=None, help="Filter queues by virtual host")
def list_queues(  # pylint: disable=too-many-arguments
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
    """List queues with client-side pagination."""

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
        payload = execute_operation("queues.list", connection, pagination)
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


@queue.command("create")
@connection_options
@click.option("--vhost", default=None, help="Target virtual host (defaults to connection vhost)")
@click.option("--name", required=True, help="Queue name (alphanumeric, dot, dash or underscore)")
@click.option(
    "--durable/--no-durable", default=False, show_default=True, help="Create queue as durable"
)
@click.option(
    "--exclusive/--no-exclusive", default=False, show_default=True, help="Create queue as exclusive"
)
@click.option(
    "--auto-delete/--no-auto-delete",
    default=False,
    show_default=True,
    help="Auto-delete queue when last consumer disconnects",
)
@click.option(
    "--arguments",
    callback=_parse_json_arguments,
    default=None,
    help="Additional queue arguments as JSON (e.g. '{\"x-message-ttl\": 60000}')",
)
def create_queue(  # pylint: disable=too-many-arguments
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    connection_vhost: str,
    vhost: str | None,
    name: str,
    durable: bool,
    exclusive: bool,
    auto_delete: bool,
    arguments: dict[str, object],
) -> None:
    """Create a new queue with the specified options."""

    try:
        validate_name(name)
    except ValidationError as exc:
        raise click.BadParameter(exc.to_user_message(), param_hint="--name") from exc

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
            "durable": durable,
            "exclusive": exclusive,
            "auto_delete": auto_delete,
            "arguments": arguments,
        }
    )

    try:
        result = execute_operation("queues.create", payload, pagination=None)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover - unexpected failure
        raise click.ClickException(str(exc)) from exc

    target_vhost = vhost or payload["connection_vhost"]
    queue_name = result.get("name", name)
    click.echo(f"Queue '{queue_name}' created in vhost '{target_vhost}'")


@queue.command("delete")
@connection_options
@click.option("--vhost", default=None, help="Target virtual host (defaults to connection vhost)")
@click.option("--name", required=True, help="Queue name to delete")
@click.option(
    "--force/--no-force",
    "force",
    default=False,
    show_default=True,
    help="Force deletion even if the queue still contains messages",
)
def delete_queue(  # pylint: disable=too-many-arguments
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    connection_vhost: str,
    vhost: str | None,
    name: str,
    force: bool,
) -> None:
    """Delete a queue safely, enforcing validation rules."""

    try:
        validate_name(name)
    except ValidationError as exc:
        raise click.BadParameter(exc.to_user_message(), param_hint="--name") from exc

    payload = build_connection_payload(
        host=host,
        port=port,
        user=user,
        password=password,
        connection_vhost=connection_vhost,
        use_tls=use_tls,
        vhost=vhost,
    )

    payload.update({"name": name, "force": force})

    try:
        result = execute_operation("queues.delete", payload, pagination=None)
    except RabbitMQError as exc:
        raise click.ClickException(exc.to_user_message()) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise click.ClickException(str(exc)) from exc

    target_vhost = vhost or payload["connection_vhost"]
    message_count = result.get("messages_before_delete")
    if result.get("forced"):
        suffix = (
            f" (force applied, removed {message_count} pending message(s))"
            if message_count is not None
            else " (force applied)"
        )
    else:
        suffix = ""
    click.echo(f"Queue '{name}' deleted from vhost '{target_vhost}'{suffix}")


__all__ = ["queue"]
