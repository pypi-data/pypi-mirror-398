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

from typing import Any

import pytest

from tools import call_id
from tools.operations.bindings import Binding
from tools.operations.exchanges import Exchange
from tools.operations.queues import (
    PaginatedQueueResponse,
    PaginationMetadata,
    Queue,
    QueueOptions,
)
from utils.errors import RabbitMQError, ValidationError


@pytest.fixture
def connection_params() -> dict[str, Any]:
    return {
        "host": "localhost",
        "port": 15672,
        "user": "guest",
        "password": "guest",
        "connection_vhost": "/",
        "use_tls": False,
    }


def test_call_id_dispatches_list_operation(
    monkeypatch: pytest.MonkeyPatch, connection_params: dict[str, Any]
) -> None:
    captured: dict[str, Any] = {}
    payload = PaginatedQueueResponse(
        items=[
            Queue(
                name="orders.queue",
                vhost="/",
                durable=True,
                auto_delete=False,
                exclusive=False,
                arguments={},
            )
        ],
        pagination=PaginationMetadata(
            totalItems=1,
            totalPages=1,
            page=1,
            pageSize=1,
            hasNextPage=False,
            hasPreviousPage=False,
        ),
    )

    def fake_list(**kwargs: Any) -> PaginatedQueueResponse:
        captured.update(kwargs)
        return payload

    monkeypatch.setitem(call_id._LIST_HANDLERS, "queues.list", fake_list)

    result = call_id.call_id(
        "queues.list",
        params=connection_params,
        pagination={"page": 1, "pageSize": 1},
    )

    assert result == payload
    assert captured["vhost"] is None
    assert captured["page"] == 1
    assert captured["pageSize"] == 1
    assert captured["settings"].host == "localhost"


def test_call_id_validates_pagination(connection_params: dict[str, Any]) -> None:
    with pytest.raises(ValidationError) as exc:
        call_id.call_id("queues.list", params=connection_params, pagination={"page": 0})

    assert exc.value.code == "INVALID_INPUT"
    assert exc.value.action


def test_call_id_handles_queue_creation(
    monkeypatch: pytest.MonkeyPatch, connection_params: dict[str, Any]
) -> None:
    captured: dict[str, Any] = {}

    def fake_create(**kwargs: Any) -> Queue:
        captured.update(kwargs)
        return Queue(
            name=kwargs["name"],
            vhost=kwargs["vhost"],
            durable=True,
            auto_delete=False,
            exclusive=False,
            arguments={},
        )

    monkeypatch.setattr(call_id, "create_queue", fake_create)

    params = connection_params | {
        "name": "orders.queue",
        "durable": True,
        "exclusive": False,
        "auto_delete": False,
        "arguments": {},
    }

    result = call_id.call_id("queues.create", params=params, pagination=None)

    assert isinstance(result, Queue)
    assert result.name == "orders.queue"
    assert captured["options"] == QueueOptions(
        durable=True, exclusive=False, auto_delete=False, arguments={}
    )


def test_call_id_propagates_business_errors(
    monkeypatch: pytest.MonkeyPatch, connection_params: dict[str, Any]
) -> None:
    def fake_create(**_: Any) -> Exchange:
        raise ValidationError(
            code="INVALID_EXCHANGE_TYPE",
            message="Only topic exchanges support wildcards",
            field="type",
            expected="direct|topic|fanout|headers",
            actual="fanout",
            action="Choose a supported exchange type",
        )

    monkeypatch.setattr(call_id, "create_exchange", fake_create)

    params = connection_params | {
        "name": "orders.exchange",
        "type": "fanout",
        "durable": True,
        "auto_delete": False,
        "internal": False,
        "arguments": {},
    }

    with pytest.raises(ValidationError) as exc:
        call_id.call_id("exchanges.create", params=params, pagination=None)

    assert exc.value.code == "INVALID_EXCHANGE_TYPE"
    assert exc.value.field == "type"


def test_call_id_raises_for_unknown_operation(connection_params: dict[str, Any]) -> None:
    with pytest.raises(ValueError) as exc:
        call_id.call_id("unknown.operation", params=connection_params, pagination=None)

    assert "Unsupported" in str(exc.value)


def test_call_id_creates_binding(
    monkeypatch: pytest.MonkeyPatch, connection_params: dict[str, Any]
) -> None:
    def fake_create_binding(**kwargs: Any) -> Binding:
        return Binding(
            source=kwargs["exchange"],
            destination=kwargs["queue"],
            destination_type="queue",
            vhost=kwargs["vhost"],
            routing_key=kwargs["routing_key"],
            arguments=kwargs["args"],
            properties_key="orders.binding",
        )

    monkeypatch.setattr(call_id, "create_binding", fake_create_binding)

    params = connection_params | {
        "exchange": "orders.exchange",
        "queue": "orders.queue",
        "routing_key": "orders.*",
        "arguments": {"x-priority": 1},
    }

    binding = call_id.call_id("bindings.create", params=params, pagination=None)

    assert isinstance(binding, Binding)
    assert binding.routing_key == "orders.*"
    assert binding.source == "orders.exchange"


def test_call_id_delete_queue_requires_name(connection_params: dict[str, Any]) -> None:
    with pytest.raises(ValidationError) as exc:
        call_id.call_id("queues.delete", params=connection_params, pagination=None)

    assert exc.value.code == "INVALID_INPUT"


def test_call_id_propagates_rabbitmq_errors(
    monkeypatch: pytest.MonkeyPatch, connection_params: dict[str, Any]
) -> None:
    expected_error = RabbitMQError(
        code="QUEUE_FETCH_FAILURE",
        message="Unable to collect queues",
        action="Check RabbitMQ availability",
    )

    def fake_list(**_: Any) -> PaginatedQueueResponse:
        raise expected_error

    monkeypatch.setitem(call_id._LIST_HANDLERS, "queues.list", fake_list)

    with pytest.raises(RabbitMQError) as exc:
        call_id.call_id(
            "queues.list",
            params=connection_params,
            pagination={"page": 1, "pageSize": 10},
        )

    assert exc.value is expected_error


def test_call_id_delete_binding(
    monkeypatch: pytest.MonkeyPatch, connection_params: dict[str, Any]
) -> None:
    captured: dict[str, Any] = {}

    def fake_delete(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"status": "deleted"}

    monkeypatch.setattr(call_id, "delete_binding", fake_delete)

    params = connection_params | {
        "exchange": "orders.exchange",
        "queue": "orders.queue",
        "properties_key": "orders.binding",
    }

    result = call_id.call_id("bindings.delete", params=params, pagination=None)

    assert isinstance(result, dict)
    assert result["status"] == "deleted"
    assert captured["properties_key"] == "orders.binding"
