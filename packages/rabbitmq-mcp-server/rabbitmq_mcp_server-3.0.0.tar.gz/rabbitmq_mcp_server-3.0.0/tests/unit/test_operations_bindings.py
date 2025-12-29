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

import time
from types import SimpleNamespace
from typing import Any, cast

import pytest

from tools.operations import bindings
from utils.errors import ConflictError, NotFoundError, ValidationError


class FakeExecutor:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        vhost: str,
        use_tls: bool,
        timeout: float,
    ) -> None:
        self.vhost = vhost
        self.last_requested_vhost: str | None = getattr(self, "last_requested_vhost", None)
        self.created: list[tuple[str, str, str, dict[str, Any]]] = []
        self.exchange_lookup: dict[tuple[str, str], dict[str, Any]] = getattr(
            self, "exchange_lookup", {}
        )
        self.queue_lookup: dict[tuple[str, str], dict[str, Any]] = getattr(self, "queue_lookup", {})
        self.binding_relations_response: list[dict[str, Any]] = getattr(
            self,
            "binding_relations_response",
            [],
        )
        self.binding_relations_response_sequence: list[list[dict[str, Any]]] | None = getattr(
            self,
            "binding_relations_response_sequence",
            None,
        )
        self.bindings_response: list[dict[str, Any]] = getattr(self, "bindings_response", [])
        self.raise_on_create: Exception | None = getattr(self, "raise_on_create", None)
        self.raise_on_list_relations: Exception | None = getattr(
            self, "raise_on_list_relations", None
        )
        self.raise_on_get_exchange: Exception | None = getattr(self, "raise_on_get_exchange", None)
        self.raise_on_get_queue: Exception | None = getattr(self, "raise_on_get_queue", None)
        self.raise_on_delete_binding: Exception | None = getattr(
            self, "raise_on_delete_binding", None
        )
        self.deleted: list[tuple[str, str, str, str]] = getattr(self, "deleted", [])

    def get_bindings(self, vhost: str | None) -> list[dict[str, Any]]:
        self.last_requested_vhost = vhost
        return self.bindings_response

    def get_exchange(self, vhost: str, name: str) -> dict[str, Any]:
        if self.raise_on_get_exchange:
            raise self.raise_on_get_exchange
        key = (vhost, name)
        if key not in self.exchange_lookup:
            raise NotFoundError(
                code="NOT_FOUND",
                message=f"Exchange '{name}' not found",
                action="Create the exchange before using it",
                context={"vhost": vhost, "exchange": name},
            )
        return self.exchange_lookup[key]

    def get_queue(self, vhost: str, name: str) -> dict[str, Any]:
        if self.raise_on_get_queue:
            raise self.raise_on_get_queue
        key = (vhost, name)
        if key not in self.queue_lookup:
            raise NotFoundError(
                code="NOT_FOUND",
                message=f"Queue '{name}' not found",
                action="Create the queue before binding to it",
                context={"vhost": vhost, "queue": name},
            )
        return self.queue_lookup[key]

    def create_binding(
        self, vhost: str, exchange: str, queue: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if self.raise_on_create:
            raise self.raise_on_create
        self.created.append((vhost, exchange, queue, payload))
        return {}

    def list_binding_relations(self, vhost: str, exchange: str, queue: str) -> list[dict[str, Any]]:
        if self.raise_on_list_relations:
            raise self.raise_on_list_relations
        if self.binding_relations_response_sequence is not None:
            if self.binding_relations_response_sequence:
                return self.binding_relations_response_sequence.pop(0)
            return self.binding_relations_response
        return self.binding_relations_response

    def delete_binding(self, vhost: str, exchange: str, queue: str, properties_key: str) -> None:
        if self.raise_on_delete_binding:
            raise self.raise_on_delete_binding
        self.deleted.append((vhost, exchange, queue, properties_key))


class DummyLogger:
    def __init__(self) -> None:
        self.debug_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.info_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **_: Any) -> DummyLogger:
        return self

    def debug(self, *args: Any, **kwargs: Any) -> None:
        self.debug_calls.append((args, kwargs))

    def info(self, event: str, **fields: Any) -> None:
        self.info_calls.append((event, fields))


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_from_yaml(cls: type[Any]) -> Any:
        return SimpleNamespace(
            host="localhost",
            port=15672,
            user="admin",
            password="secret",
            vhost="/",
            use_tls=False,
            crud_timeout=5,
        )

    monkeypatch.setattr(bindings.Settings, "from_yaml", classmethod(fake_from_yaml))


@pytest.fixture(autouse=True)
def _patch_executor(monkeypatch: pytest.MonkeyPatch) -> FakeExecutor:
    executor = FakeExecutor(
        host="localhost",
        port=15672,
        user="admin",
        password="secret",
        vhost="/",
        use_tls=False,
        timeout=5,
    )

    class ExecutorFactory(FakeExecutor):
        def __new__(cls, *args: Any, **kwargs: Any) -> FakeExecutor:
            executor.__init__(*args, **kwargs)  # type: ignore[misc]
            return executor

    monkeypatch.setattr(bindings, "RabbitMQExecutor", ExecutorFactory)
    return executor


def test_list_bindings_returns_paginated_response(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    logger = DummyLogger()
    recorded_vhosts: list[str] = []

    def fake_validate(vhost: str, executor: FakeExecutor) -> None:
        recorded_vhosts.append(vhost)

    _patch_executor.bindings_response = [
        {
            "source": "orders.exchange",
            "destination": "orders.queue",
            "destination_type": "queue",
            "vhost": "/sales",
            "routing_key": "order.created",
        },
        {
            "source": "orders.exchange",
            "destination": "payments.queue",
            "destination_type": "queue",
            "vhost": "/sales",
            "routing_key": "order.paid",
        },
    ]

    monkeypatch.setattr(bindings, "validate_vhost_exists", fake_validate)
    monkeypatch.setattr(bindings, "get_logger", lambda _: logger)

    response = bindings.list_bindings(vhost="/sales", page=2, pageSize=1)

    assert recorded_vhosts == ["/sales"]
    assert response.pagination.totalItems == 2
    assert response.pagination.page == 2
    assert response.pagination.totalPages == 2
    assert response.pagination.hasPreviousPage is True
    assert response.pagination.hasNextPage is False
    assert len(response.items) == 1
    assert response.items[0].destination == "payments.queue"
    assert _patch_executor.last_requested_vhost == "/sales"
    assert len(logger.debug_calls) >= 2
    fetch_args, _ = logger.debug_calls[0]
    assert fetch_args[1] == "/sales"
    return_args, _ = logger.debug_calls[1]
    assert return_args[1] == len(response.items)
    assert return_args[2] == response.pagination.page


def test_list_bindings_default_vhost(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    logger = DummyLogger()

    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(bindings, "get_logger", lambda _: logger)

    bindings.list_bindings()

    assert logger.debug_calls
    fetch_args, _ = logger.debug_calls[0]
    assert fetch_args[1] == "*"


def test_create_binding_success(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    call_sequence: list[str] = []
    logger = DummyLogger()

    monkeypatch.setattr(
        bindings, "validate_vhost_exists", lambda v, e: call_sequence.append(f"vhost:{v}")
    )
    monkeypatch.setattr(
        bindings,
        "validate_routing_key",
        lambda key, exchange_type: call_sequence.append(f"routing:{key}:{exchange_type}"),
    )
    monkeypatch.setattr(bindings, "get_logger", lambda _: logger)

    _patch_executor.exchange_lookup[("/sales", "orders.exchange")] = {
        "name": "orders.exchange",
        "vhost": "/sales",
        "type": "topic",
    }
    _patch_executor.queue_lookup[("/sales", "orders.queue")] = {
        "name": "orders.queue",
        "vhost": "/sales",
    }
    _patch_executor.binding_relations_response_sequence = [
        [],
        [
            {
                "source": "orders.exchange",
                "destination": "orders.queue",
                "destination_type": "queue",
                "vhost": "/sales",
                "routing_key": "order.created",
                "arguments": {"priority": 1},
            }
        ],
    ]

    assert ("/sales", "orders.exchange") in _patch_executor.exchange_lookup
    assert ("/sales", "orders.queue") in _patch_executor.queue_lookup

    result = bindings.create_binding(
        "/sales",
        "orders.exchange",
        "orders.queue",
        "order.created",
        {"priority": 1},
    )

    assert call_sequence == ["vhost:/sales", "routing:order.created:topic"]
    assert result.routing_key == "order.created"
    assert result.arguments == {"priority": 1}
    assert _patch_executor.created == [
        (
            "/sales",
            "orders.exchange",
            "orders.queue",
            {"routing_key": "order.created", "arguments": {"priority": 1}},
        )
    ]
    assert logger.info_calls
    event, fields = logger.info_calls[0]
    assert event == "binding.create.success"
    assert fields["operation"] == "binding.create"
    assert fields["result"] == "success"
    assert "password" not in fields


def test_create_binding_conflict(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    _patch_executor.raise_on_create = ConflictError(
        code="CONFLICT",
        message="Binding exists",
        action="Retry",
    )

    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(bindings, "validate_routing_key", lambda key, exchange_type: None)

    _patch_executor.exchange_lookup[("/", "exchange")] = {
        "name": "exchange",
        "vhost": "/",
        "type": "direct",
    }
    _patch_executor.queue_lookup[("/", "queue")] = {"name": "queue", "vhost": "/"}

    with pytest.raises(ConflictError) as exc:
        bindings.create_binding(None, "exchange", "queue", "key", {})

    assert exc.value.code == "BINDING_ALREADY_EXISTS"
    assert exc.value.context["routing_key"] == "key"
    assert exc.value.message
    assert exc.value.action


def test_create_binding_missing_both_resources(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(bindings, "validate_routing_key", lambda key, exchange_type: None)

    with pytest.raises(NotFoundError) as exc:
        bindings.create_binding("/sales", "missing.exchange", "missing.queue", None, None)

    assert exc.value.code == "RESOURCES_NOT_FOUND"
    assert exc.value.context["missing"] == ["exchange", "queue"]
    assert exc.value.action


def test_create_binding_missing_exchange(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(bindings, "validate_routing_key", lambda key, exchange_type: None)

    _patch_executor.queue_lookup[("/sales", "orders.queue")] = {
        "name": "orders.queue",
        "vhost": "/sales",
    }

    with pytest.raises(NotFoundError) as exc:
        bindings.create_binding("/sales", "missing.exchange", "orders.queue", None, None)

    assert exc.value.code == "EXCHANGE_NOT_FOUND"
    assert exc.value.context["exchange"] == "missing.exchange"
    assert exc.value.action


def test_delete_binding_requires_properties_key(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)

    with pytest.raises(ValidationError) as exc:
        bindings.delete_binding("/", "ex", "queue", cast(str, None))

    assert exc.value.code == "MISSING_PROPERTIES_KEY"


def test_delete_binding_not_found(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)

    _patch_executor.raise_on_delete_binding = NotFoundError(
        code="NOT_FOUND",
        message="missing",
        action="refresh",
    )

    with pytest.raises(NotFoundError) as exc:
        bindings.delete_binding("/", "ex", "queue", "props")

    assert exc.value.code == "BINDING_NOT_FOUND"
    assert exc.value.context["properties_key"] == "props"
    assert exc.value.action


def test_delete_binding_success_logs(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)

    logger = DummyLogger()
    monkeypatch.setattr(bindings, "get_logger", lambda _: logger)

    result = bindings.delete_binding("/", "ex", "queue", "props")

    assert result["status"] == "deleted"
    assert _patch_executor.deleted == [("/", "ex", "queue", "props")]
    assert logger.info_calls[0][0] == "binding.delete.success"
    fields = logger.info_calls[0][1]
    assert fields["operation"] == "binding.delete"
    assert fields["result"] == "success"
    assert fields["properties_key"] == "props"
    assert "password" not in fields


def test_delete_binding_completes_quickly(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(bindings, "get_logger", lambda _: DummyLogger())

    start = time.perf_counter()
    bindings.delete_binding("/", "ex", "queue", "props")
    duration = time.perf_counter() - start

    assert duration < 0.1


def test_list_bindings_completes_under_two_seconds(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(bindings, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(bindings, "get_logger", lambda _: DummyLogger())

    _patch_executor.bindings_response = []

    start = time.perf_counter()
    bindings.list_bindings(page=1, pageSize=50)
    duration = time.perf_counter() - start

    assert duration < 2
