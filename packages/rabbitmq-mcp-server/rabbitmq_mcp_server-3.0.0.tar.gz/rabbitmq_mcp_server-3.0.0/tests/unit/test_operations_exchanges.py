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
from typing import Any

import pytest

from tools.operations import exchanges
from utils.errors import ConflictError, NotFoundError


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
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self.last_requested_vhost: str | None = None
        self.created: list[tuple[str, str, dict[str, Any]]] = []
        self.exchange_lookup: dict[tuple[str, str], dict[str, Any]] = getattr(
            self, "exchange_lookup", {}
        )
        self.bindings_lookup: dict[tuple[str, str], list[dict[str, Any]]] = getattr(
            self,
            "bindings_lookup",
            {},
        )
        self.deleted: list[tuple[str, str]] = getattr(self, "deleted", [])
        self.raise_on_create: Exception | None = getattr(self, "raise_on_create", None)
        self.raise_on_get_exchange: Exception | None = getattr(self, "raise_on_get_exchange", None)
        self.raise_on_get_bindings: Exception | None = getattr(self, "raise_on_get_bindings", None)

    def get_exchanges(self, vhost: str | None) -> list[dict[str, Any]]:
        self.last_requested_vhost = vhost
        return [
            {
                "name": "orders.exchange",
                "vhost": vhost or self.vhost,
                "type": "topic",
                "durable": True,
                "auto_delete": False,
                "internal": False,
                "arguments": {},
                "message_stats": {"publish_in": 10, "publish_out": 10},
            },
            {
                "name": "payments.exchange",
                "vhost": vhost or self.vhost,
                "type": "direct",
                "durable": True,
                "auto_delete": False,
                "internal": False,
                "arguments": {},
            },
        ]

    def create_exchange(self, vhost: str, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.raise_on_create:
            raise self.raise_on_create
        self.created.append((vhost, name, payload))
        self.exchange_lookup.setdefault(
            (vhost, name),
            {"name": name, "vhost": vhost, **payload},
        )
        return {}

    def get_exchange(self, vhost: str, name: str) -> dict[str, Any]:
        if self.raise_on_get_exchange:
            raise self.raise_on_get_exchange
        return self.exchange_lookup.get((vhost, name), {"name": name, "vhost": vhost})

    def get_bindings_for_exchange(self, vhost: str, name: str) -> list[dict[str, Any]]:
        if self.raise_on_get_bindings:
            raise self.raise_on_get_bindings
        return self.bindings_lookup.get((vhost, name), [])

    def delete_exchange(self, vhost: str, name: str) -> None:
        self.deleted.append((vhost, name))


class DummyLogger:
    def __init__(self) -> None:
        self.debug_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.info_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **_: Any) -> DummyLogger:
        return self  # type: ignore[return-value]

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

    monkeypatch.setattr(exchanges.Settings, "from_yaml", classmethod(fake_from_yaml))


@pytest.fixture(autouse=True)
def _patch_executor(monkeypatch: pytest.MonkeyPatch) -> FakeExecutor:
    fake_executor = FakeExecutor(
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
            fake_executor.__init__(*args, **kwargs)  # type: ignore[misc]
            return fake_executor

    monkeypatch.setattr(exchanges, "RabbitMQExecutor", ExecutorFactory)
    return fake_executor


def test_list_exchanges_validates_pagination() -> None:
    with pytest.raises(ValueError):
        exchanges.list_exchanges(page=0)
    with pytest.raises(ValueError):
        exchanges.list_exchanges(pageSize=0)
    with pytest.raises(ValueError):
        exchanges.list_exchanges(pageSize=201)


def test_list_exchanges_returns_paginated_response(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    recorded_vhosts: list[str] = []
    logger = DummyLogger()

    def fake_validate(vhost: str, executor: FakeExecutor) -> None:
        recorded_vhosts.append(vhost)

    monkeypatch.setattr(exchanges, "validate_vhost_exists", fake_validate)
    monkeypatch.setattr(exchanges, "get_logger", lambda _: logger)

    response = exchanges.list_exchanges(vhost="/sales", page=1, pageSize=1)

    assert recorded_vhosts == ["/sales"]
    assert response.pagination.totalItems == 2
    assert response.pagination.totalPages == 2
    assert response.pagination.hasNextPage is True
    assert response.pagination.hasPreviousPage is False
    assert len(response.items) == 1
    assert response.items[0].name == "orders.exchange"
    assert _patch_executor.last_requested_vhost == "/sales"
    assert len(logger.debug_calls) >= 2
    fetch_args, _ = logger.debug_calls[0]
    assert fetch_args[1] == "/sales"
    return_args, _ = logger.debug_calls[1]
    assert return_args[1] == len(response.items)
    assert return_args[2] == response.pagination.page
    assert return_args[3] == response.pagination.totalPages


def test_list_exchanges_default_vhost(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    recorded_vhosts: list[str] = []
    logger = DummyLogger()

    def fake_validate(vhost: str, executor: FakeExecutor) -> None:
        recorded_vhosts.append(vhost)

    monkeypatch.setattr(exchanges, "validate_vhost_exists", fake_validate)
    monkeypatch.setattr(exchanges, "get_logger", lambda _: logger)

    response = exchanges.list_exchanges()

    assert recorded_vhosts == ["/"]
    assert response.pagination.totalItems == 2
    assert response.items[0].vhost == "/"
    assert _patch_executor.last_requested_vhost is None
    assert logger.debug_calls
    fetch_args, _ = logger.debug_calls[0]
    assert fetch_args[1] == "/"


def test_create_exchange_success(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    call_sequence: list[str] = []
    logger = DummyLogger()

    monkeypatch.setattr(
        exchanges, "validate_vhost_exists", lambda v, e: call_sequence.append(f"vhost:{v}")
    )
    monkeypatch.setattr(exchanges, "validate_name", lambda n: call_sequence.append(f"name:{n}"))
    monkeypatch.setattr(
        exchanges, "validate_exchange_type", lambda t: call_sequence.append(f"type:{t}")
    )
    monkeypatch.setattr(exchanges, "get_logger", lambda _: logger)

    _patch_executor.exchange_lookup[("/sales", "orders.exchange")] = {
        "name": "orders.exchange",
        "vhost": "/sales",
        "type": "topic",
    }

    options = exchanges.ExchangeOptions(durable=True, auto_delete=False, internal=False)
    result = exchanges.create_exchange("/sales", "orders.exchange", "topic", options)

    assert call_sequence == ["vhost:/sales", "name:orders.exchange", "type:topic"]
    assert result.name == "orders.exchange"
    assert result.vhost == "/sales"
    assert _patch_executor.created == [
        ("/sales", "orders.exchange", {**options.model_dump(exclude_none=True), "type": "topic"})
    ]
    assert logger.info_calls
    event, fields = logger.info_calls[0]
    assert event == "exchange.create.success"
    assert fields["operation"] == "exchange.create"
    assert fields["result"] == "success"
    assert "password" not in fields


def test_create_exchange_conflict(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    _patch_executor.raise_on_create = ConflictError(
        code="CONFLICT",
        message="exists",
        action="retry",
    )

    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(exchanges, "validate_name", lambda n: None)
    monkeypatch.setattr(exchanges, "validate_exchange_type", lambda t: None)

    with pytest.raises(ConflictError) as exc:
        exchanges.create_exchange(None, "dup.exchange", "direct", exchanges.ExchangeOptions())

    assert exc.value.code == "EXCHANGE_ALREADY_EXISTS"
    assert exc.value.context["exchange"] == "dup.exchange"
    assert exc.value.message
    assert exc.value.action


def test_create_exchange_returns_payload_when_lookup_missing(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(exchanges, "validate_name", lambda n: None)
    monkeypatch.setattr(exchanges, "validate_exchange_type", lambda t: None)

    _patch_executor.raise_on_get_exchange = NotFoundError(
        code="NOT_FOUND",
        message="missing",
        action="create",
    )

    options = exchanges.ExchangeOptions(durable=True, auto_delete=False, internal=False)
    result = exchanges.create_exchange(None, "temp.exchange", "fanout", options)

    assert result.name == "temp.exchange"
    assert result.type == "fanout"
    assert result.durable is True


def test_validate_exchange_delete_blocks_system_exchange(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)

    with pytest.raises(ConflictError) as exc:
        exchanges.validate_exchange_delete(
            "/",
            "amq.topic",
            settings=exchanges.Settings.from_yaml(),
            executor=_patch_executor,  # type: ignore[arg-type]
        )

    assert exc.value.code == "SYSTEM_EXCHANGE"
    assert "cannot be deleted" in exc.value.message


def test_validate_exchange_delete_blocks_when_bindings_exist(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)

    _patch_executor.exchange_lookup[("/", "orders.exchange")] = {
        "name": "orders.exchange",
        "vhost": "/",
    }
    _patch_executor.bindings_lookup[("/", "orders.exchange")] = [
        {
            "destination": "orders.queue",
            "destination_type": "queue",
            "routing_key": "order.created",
        }
    ]

    with pytest.raises(ConflictError) as exc:
        exchanges.validate_exchange_delete(
            "/",
            "orders.exchange",
            settings=exchanges.Settings.from_yaml(),
            executor=_patch_executor,  # type: ignore[arg-type]
        )

    assert exc.value.code == "EXCHANGE_HAS_BINDINGS"
    assert "must be detached" in exc.value.message
    assert exc.value.context["binding_count"] == 1
    sample = exc.value.context["sample_bindings"][0]
    assert sample["destination"] == "orders.queue"
    assert exc.value.action


def test_validate_exchange_delete_allows_when_no_bindings(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)

    _patch_executor.exchange_lookup[("/", "idle.exchange")] = {
        "name": "idle.exchange",
        "vhost": "/",
    }
    _patch_executor.bindings_lookup[("/", "idle.exchange")] = []

    logger = DummyLogger()
    monkeypatch.setattr(exchanges, "get_logger", lambda _: logger)

    result = exchanges.validate_exchange_delete(
        "/",
        "idle.exchange",
        settings=exchanges.Settings.from_yaml(),
        executor=_patch_executor,  # type: ignore[arg-type]
    )

    assert result["binding_count"] == 0
    assert logger.debug_calls


def test_delete_exchange_executes_audit_log(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)

    _patch_executor.exchange_lookup[("/", "idle.exchange")] = {
        "name": "idle.exchange",
        "vhost": "/",
    }
    _patch_executor.bindings_lookup[("/", "idle.exchange")] = []

    logger = DummyLogger()
    monkeypatch.setattr(exchanges, "get_logger", lambda _: logger)

    result = exchanges.delete_exchange(None, "idle.exchange")

    assert result["status"] == "deleted"
    assert _patch_executor.deleted == [("/", "idle.exchange")]
    assert logger.info_calls[0][0] == "exchange.delete.success"
    fields = logger.info_calls[0][1]
    assert fields["operation"] == "exchange.delete"
    assert fields["result"] == "success"
    assert fields["exchange_name"] == "idle.exchange"
    assert "password" not in fields


def test_delete_exchange_completes_quickly(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(exchanges, "get_logger", lambda _: DummyLogger())

    _patch_executor.exchange_lookup[("/", "idle.exchange")] = {
        "name": "idle.exchange",
        "vhost": "/",
    }
    _patch_executor.bindings_lookup[("/", "idle.exchange")] = []

    start = time.perf_counter()
    exchanges.delete_exchange(None, "idle.exchange")
    duration = time.perf_counter() - start

    assert duration < 0.1


def test_list_exchanges_completes_under_two_seconds(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(exchanges, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(exchanges, "get_logger", lambda _: DummyLogger())

    start = time.perf_counter()
    exchanges.list_exchanges(page=1, pageSize=50)
    duration = time.perf_counter() - start

    assert duration < 2
