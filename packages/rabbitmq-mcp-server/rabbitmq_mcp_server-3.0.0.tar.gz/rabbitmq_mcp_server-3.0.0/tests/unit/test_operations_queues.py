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

from tools.operations import queues
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
        self.last_requested_vhost: str | None = None
        self.created: list[tuple[str, str, dict[str, Any]]] = getattr(self, "created", [])
        self.deleted: list[tuple[str, str, bool]] = getattr(self, "deleted", [])
        self.queue_lookup: dict[tuple[str, str], dict[str, Any]] = getattr(self, "queue_lookup", {})
        self.raise_on_create: Exception | None = getattr(self, "raise_on_create", None)
        self.raise_on_get_queue: Exception | None = getattr(self, "raise_on_get_queue", None)

    def get_queues(self, vhost: str | None) -> list[dict[str, Any]]:
        self.last_requested_vhost = vhost
        return [
            {
                "name": "orders.queue",
                "vhost": vhost or self.vhost,
                "durable": True,
                "auto_delete": False,
                "exclusive": False,
                "arguments": {},
                "messages": 10,
                "messages_ready": 8,
                "messages_unacknowledged": 2,
                "consumers": 3,
                "memory": 1024,
            },
            {
                "name": "payments.queue",
                "vhost": vhost or self.vhost,
                "durable": True,
                "auto_delete": False,
                "exclusive": False,
                "arguments": {},
                "messages": 0,
                "messages_ready": 0,
                "messages_unacknowledged": 0,
                "consumers": 1,
                "memory": 2048,
            },
        ]

    def create_queue(self, vhost: str, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.raise_on_create:
            raise self.raise_on_create
        self.created.append((vhost, name, payload))
        self.queue_lookup.setdefault((vhost, name), {"name": name, "vhost": vhost, **payload})
        return {}

    def get_queue(self, vhost: str, name: str) -> dict[str, Any]:
        if self.raise_on_get_queue:
            raise self.raise_on_get_queue
        return self.queue_lookup.get((vhost, name), {"name": name, "vhost": vhost})

    def delete_queue(self, vhost: str, name: str, force: bool = False) -> None:
        self.deleted.append((vhost, name, force))


class DummyLogger:
    def __init__(self) -> None:
        self.debug_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.info_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **_: Any):
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

    monkeypatch.setattr(queues.Settings, "from_yaml", classmethod(fake_from_yaml))


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

    monkeypatch.setattr(queues, "RabbitMQExecutor", ExecutorFactory)
    return executor


def test_list_queues_validates_pagination() -> None:
    with pytest.raises(ValueError):
        queues.list_queues(page=0)
    with pytest.raises(ValueError):
        queues.list_queues(pageSize=0)
    with pytest.raises(ValueError):
        queues.list_queues(pageSize=300)


def test_list_queues_returns_paginated_response(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    recorded_vhosts: list[str] = []
    logger = DummyLogger()

    def fake_validate(vhost: str, executor: FakeExecutor) -> None:
        recorded_vhosts.append(vhost)

    monkeypatch.setattr(queues, "validate_vhost_exists", fake_validate)
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    response = queues.list_queues(vhost="/production", page=2, pageSize=1)

    assert recorded_vhosts == ["/production"]
    assert response.pagination.totalItems == 2
    assert response.pagination.page == 2
    assert response.pagination.totalPages == 2
    assert response.pagination.hasNextPage is False
    assert response.pagination.hasPreviousPage is True
    assert len(response.items) == 1
    assert response.items[0].name == "payments.queue"
    assert _patch_executor.last_requested_vhost == "/production"
    assert len(logger.debug_calls) >= 2
    fetch_args, _ = logger.debug_calls[0]
    assert "Fetching queues" in fetch_args[0]
    assert fetch_args[1] == "/production"
    return_args, _ = logger.debug_calls[1]
    assert "Returning" in return_args[0]
    assert return_args[1] == len(response.items)
    assert return_args[2] == 2
    assert return_args[3] == response.pagination.totalPages


def test_list_queues_default_vhost(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    recorded_vhosts: list[str] = []
    logger = DummyLogger()

    def fake_validate(vhost: str, executor: FakeExecutor) -> None:
        recorded_vhosts.append(vhost)

    monkeypatch.setattr(queues, "validate_vhost_exists", fake_validate)
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    queues.list_queues()

    assert recorded_vhosts == ["/"]
    assert _patch_executor.last_requested_vhost is None
    assert logger.debug_calls
    fetch_args, _ = logger.debug_calls[0]
    assert fetch_args[1] == "/"


def test_create_queue_success(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    call_order: list[tuple[str, str]] = []
    logger = DummyLogger()

    def fake_validate_vhost(vhost: str, executor: FakeExecutor) -> None:
        call_order.append(("vhost", vhost))

    def fake_validate_name(name: str) -> None:
        call_order.append(("name", name))

    monkeypatch.setattr(queues, "validate_vhost_exists", fake_validate_vhost)
    monkeypatch.setattr(queues, "validate_name", fake_validate_name)
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    _patch_executor.queue_lookup[("/sales", "orders.queue")] = {
        "name": "orders.queue",
        "vhost": "/sales",
        "durable": True,
    }

    options = queues.QueueOptions(durable=True, exclusive=False, auto_delete=False)
    result = queues.create_queue("/sales", "orders.queue", options)

    assert call_order == [("vhost", "/sales"), ("name", "orders.queue")]
    assert result.name == "orders.queue"
    assert result.vhost == "/sales"
    assert _patch_executor.created == [
        ("/sales", "orders.queue", options.model_dump(exclude_none=True))
    ]
    assert logger.info_calls
    event, fields = logger.info_calls[0]
    assert event == "queue.create.success"
    assert fields["operation"] == "queue.create"
    assert fields["result"] == "success"
    assert fields["queue_name"] == "orders.queue"
    assert "password" not in fields


def test_create_queue_conflict(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    _patch_executor.raise_on_create = ConflictError(
        code="CONFLICT",
        message="Exists",
        action="Retry",
    )

    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(queues, "validate_name", lambda name: None)

    with pytest.raises(ConflictError) as exc:
        queues.create_queue("/", "orders.queue", queues.QueueOptions())

    assert exc.value.code == "QUEUE_ALREADY_EXISTS"
    assert exc.value.context["queue"] == "orders.queue"
    assert exc.value.message
    assert exc.value.action


def test_create_queue_uses_fallback_when_lookup_missing(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(queues, "validate_name", lambda name: None)
    _patch_executor.raise_on_get_queue = NotFoundError(
        code="NOT_FOUND",
        message="missing",
        action="create",
    )

    options = queues.QueueOptions(durable=False, exclusive=True, auto_delete=True)
    result = queues.create_queue(None, "temp.queue", options)

    assert result.name == "temp.queue"
    assert result.vhost == "/"
    assert result.exclusive is True
    assert result.auto_delete is True


def test_validate_queue_delete_blocks_non_empty_queue(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    logger = DummyLogger()
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    _patch_executor.queue_lookup[("/sales", "busy.queue")] = {
        "name": "busy.queue",
        "vhost": "/sales",
        "messages": 12,
    }

    settings = queues.Settings.from_yaml()

    with pytest.raises(ConflictError) as exc:
        queues.validate_queue_delete(
            "/sales",
            "busy.queue",
            False,
            settings=settings,
            executor=_patch_executor,  # type: ignore[arg-type]
        )

    assert exc.value.code == "QUEUE_NOT_EMPTY"
    assert "cannot be deleted" in exc.value.message
    assert exc.value.context["messages"] == 12
    assert exc.value.action
    assert not _patch_executor.deleted


def test_validate_queue_delete_allows_force(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    logger = DummyLogger()
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    _patch_executor.queue_lookup[("/sales", "busy.queue")] = {
        "name": "busy.queue",
        "vhost": "/sales",
        "messages": 5,
    }

    settings = queues.Settings.from_yaml()

    result = queues.validate_queue_delete(
        "/sales",
        "busy.queue",
        True,
        settings=settings,
        executor=_patch_executor,  # type: ignore[arg-type]
    )

    assert result["messages"] == 5
    assert logger.debug_calls  # validation logged
    _, kwargs = logger.debug_calls[0]
    assert kwargs["force"] is True


def test_validate_queue_delete_handles_missing_queue(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(queues, "get_logger", lambda _: DummyLogger())

    _patch_executor.raise_on_get_queue = NotFoundError(
        code="NOT_FOUND",
        message="missing",
        action="create",
    )

    settings = queues.Settings.from_yaml()

    with pytest.raises(NotFoundError) as exc:
        queues.validate_queue_delete(
            "/sales",
            "unknown.queue",
            False,
            settings=settings,
            executor=_patch_executor,  # type: ignore[arg-type]
        )

    assert exc.value.code == "QUEUE_NOT_FOUND"
    assert exc.value.action
    assert exc.value.context["queue"] == "unknown.queue"


def test_delete_queue_executes_and_logs(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    logger = DummyLogger()
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    _patch_executor.queue_lookup[("/sales", "idle.queue")] = {
        "name": "idle.queue",
        "vhost": "/sales",
        "messages": 0,
    }

    result = queues.delete_queue("/sales", "idle.queue", False)

    assert result["status"] == "deleted"
    assert result["forced"] is False
    assert _patch_executor.deleted == [("/sales", "idle.queue", False)]
    assert logger.info_calls[0][0] == "queue.delete.success"
    fields = logger.info_calls[0][1]
    assert fields["operation"] == "queue.delete"
    assert fields["vhost"] == "/sales"
    assert fields["result"] == "success"
    assert "password" not in fields


def test_delete_queue_force_true_tracks_messages(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    logger = DummyLogger()
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    _patch_executor.queue_lookup[("/sales", "busy.queue")] = {
        "name": "busy.queue",
        "vhost": "/sales",
        "messages": 7,
    }

    result = queues.delete_queue("/sales", "busy.queue", True)

    assert result["forced"] is True
    assert result["messages_before_delete"] == 7
    assert _patch_executor.deleted == [("/sales", "busy.queue", True)]
    fields = logger.info_calls[0][1]
    assert fields["forced"] is True
    assert fields["messages_before_delete"] == 7


def test_delete_queue_completes_quickly(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(queues, "get_logger", lambda _: DummyLogger())

    _patch_executor.queue_lookup[("/sales", "idle.queue")] = {
        "name": "idle.queue",
        "vhost": "/sales",
        "messages": 0,
    }

    start = time.perf_counter()
    queues.delete_queue("/sales", "idle.queue", False)
    duration = time.perf_counter() - start

    assert duration < 0.1


def test_list_queues_completes_under_two_seconds(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(queues, "get_logger", lambda _: DummyLogger())

    start = time.perf_counter()
    queues.list_queues(page=1, pageSize=50)
    duration = time.perf_counter() - start

    assert duration < 2


def test_create_queue_hundred_percent_logging(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(queues, "validate_name", lambda name: None)
    logger = DummyLogger()
    monkeypatch.setattr(queues, "get_logger", lambda _: logger)

    options = queues.QueueOptions(durable=True)
    for index in range(10):
        _patch_executor.queue_lookup[("/", f"queue-{index}")] = {
            "name": f"queue-{index}",
            "vhost": "/",
        }
        queues.create_queue("/", f"queue-{index}", options)

    assert len(logger.info_calls) == 10
    for _, fields in logger.info_calls:
        assert fields["operation"] == "queue.create"


def test_list_queues_memory_usage_below_one_gigabyte(
    monkeypatch: pytest.MonkeyPatch, _patch_executor: FakeExecutor
) -> None:
    monkeypatch.setattr(queues, "validate_vhost_exists", lambda v, e: None)
    monkeypatch.setattr(queues, "get_logger", lambda _: DummyLogger())

    large_dataset = [
        {
            "name": f"queue-{idx}",
            "vhost": "/",
            "durable": True,
            "auto_delete": False,
            "exclusive": False,
            "arguments": {},
            "messages": idx,
            "messages_ready": idx,
            "messages_unacknowledged": 0,
            "consumers": 1,
            "memory": 1024,
        }
        for idx in range(1000)
    ]

    def huge_get_queues(_: str | None) -> list[dict[str, Any]]:
        return large_dataset

    _patch_executor.get_queues = huge_get_queues  # type: ignore[assignment]

    import tracemalloc

    tracemalloc.start()
    queues.list_queues(page=1, pageSize=50)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < 1_000_000_000
