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

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

import pytest

pytest.importorskip("testcontainers.rabbitmq")
from testcontainers.rabbitmq import RabbitMqContainer

from config.settings import Settings
from tools.operations import bindings, exchanges, queues
from utils.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError


@contextmanager
def rabbitmq_container() -> Iterator[RabbitMqContainer]:
    container = RabbitMqContainer("rabbitmq:3.13-management").with_exposed_ports(5672, 15672)
    with container:
        yield container


def _settings_from_container(container: RabbitMqContainer) -> Settings:
    host = container.get_container_host_ip()
    management_port = int(container.get_exposed_port(15672))
    return Settings(
        host=host,
        port=management_port,
        user="guest",
        password="guest",
        vhost="/",
        use_tls=False,
        crud_timeout=5,
        list_timeout=30,
    )


def _executor_from_settings(settings: Settings) -> bindings.RabbitMQExecutor:
    return bindings.RabbitMQExecutor(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        vhost=settings.vhost,
        use_tls=settings.use_tls,
        timeout=settings.crud_timeout,
    )


def _wait_for_message_count(
    executor: bindings.RabbitMQExecutor, queue_name: str, expected: int
) -> int:
    current = 0
    for _ in range(30):
        queue_info = executor.get_queue("/", queue_name) or {}
        current = int(queue_info.get("messages_ready", queue_info.get("messages", 0)))
        if current == expected:
            return current
        time.sleep(0.1)
    return current


def _publish_message(
    executor: bindings.RabbitMQExecutor, exchange_name: str, routing_key: str, payload: str = "data"
) -> None:
    executor._request(
        "POST",
        f"/exchanges/%2f/{exchange_name}/publish",
        json={
            "properties": {},
            "routing_key": routing_key,
            "payload": payload,
            "payload_encoding": "string",
        },
    )


def _purge_queue(executor: bindings.RabbitMQExecutor, queue_name: str) -> None:
    executor._request("DELETE", f"/queues/%2f/{queue_name}/contents")


@pytest.mark.integration
def test_binding_create_and_list_simple() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "integration.direct"
        queue_name = "integration.queue"

        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        binding = bindings.create_binding(
            "/", exchange_name, queue_name, "route", None, settings=settings
        )
        assert binding.routing_key == "route"
        assert binding.destination == queue_name

        listed = bindings.list_bindings(page=1, pageSize=50, settings=settings)
        assert any(
            item.destination == queue_name and item.source == exchange_name for item in listed.items
        )


@pytest.mark.integration
def test_binding_wildcard_routing_topic_exchange() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "orders.topic"
        queue_name = "orders.queue"

        exchanges.create_exchange(
            "/", exchange_name, "topic", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        executor = _executor_from_settings(settings)
        binding = bindings.create_binding(
            "/", exchange_name, queue_name, "orders.*.created", None, settings=settings
        )
        assert binding.routing_key == "orders.*.created"

        _purge_queue(executor, queue_name)
        _publish_message(executor, exchange_name, "orders.eu.created")
        assert _wait_for_message_count(executor, queue_name, 1) == 1

        # Drain message to keep queue clean for the next assertion
        executor._request(
            "POST",
            f"/queues/%2f/{queue_name}/get",
            json={"count": 10, "ackmode": "ack_requeue_false", "encoding": "auto"},
        )

        _purge_queue(executor, queue_name)
        _publish_message(executor, exchange_name, "orders.eu.us.created")
        time.sleep(0.2)
        no_match = executor._request(
            "POST",
            f"/queues/%2f/{queue_name}/get",
            json={"count": 10, "ackmode": "ack_requeue_false", "encoding": "auto"},
        )
        assert isinstance(no_match, list)
        assert not no_match, f"Unexpected routing for key 'orders.eu.us.created': {no_match}"
        _purge_queue(executor, queue_name)

        # '#' wildcard should match multiple levels
        bindings.create_binding("/", exchange_name, queue_name, "orders.#", None, settings=settings)
        _purge_queue(executor, queue_name)
        _publish_message(executor, exchange_name, "orders.eu.us.created")
        assert _wait_for_message_count(executor, queue_name, 1) == 1


@pytest.mark.integration
def test_binding_wildcard_rejected_for_direct_exchange() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "direct.no.wildcards"
        queue_name = "direct.queue"

        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        with pytest.raises(ValidationError) as exc:
            bindings.create_binding(
                "/", exchange_name, queue_name, "orders.*", None, settings=settings
            )
        assert exc.value.code == "INVALID_ROUTING_KEY"


@pytest.mark.integration
def test_binding_pagination_with_multiple_pages() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "bulk.exchange"

        exchanges.create_exchange(
            "/", exchange_name, "fanout", exchanges.ExchangeOptions(), settings=settings
        )

        for index in range(120):
            queue_name = f"bulk.queue.{index}"
            queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)
            bindings.create_binding("/", exchange_name, queue_name, "", None, settings=settings)

        page_one = bindings.list_bindings(page=1, pageSize=50, settings=settings)
        page_three = bindings.list_bindings(page=3, pageSize=50, settings=settings)

        assert page_one.pagination.totalItems >= 120
        assert page_one.pagination.totalPages >= 3
        assert len(page_one.items) == 50
        assert page_three.pagination.page == 3
        assert 0 <= len(page_three.items) <= 50


@pytest.mark.integration
def test_binding_duplicate_prevention() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "duplicate.exchange"
        queue_name = "duplicate.queue"

        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        bindings.create_binding("/", exchange_name, queue_name, "route", None, settings=settings)
        with pytest.raises(ConflictError) as exc:
            bindings.create_binding(
                "/", exchange_name, queue_name, "route", None, settings=settings
            )
        assert exc.value.code == "BINDING_ALREADY_EXISTS"


@pytest.mark.integration
def test_binding_delete_flow() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "delete.exchange"
        queue_name = "delete.queue"

        exchanges.create_exchange(
            "/", exchange_name, "fanout", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        binding = bindings.create_binding(
            "/", exchange_name, queue_name, "", None, settings=settings
        )
        assert binding.properties_key is not None

        response = bindings.delete_binding(
            "/", exchange_name, queue_name, binding.properties_key or "", settings=settings
        )
        assert response["status"] == "deleted"

        listed = bindings.list_bindings(page=1, pageSize=10, settings=settings)
        assert all(
            not (item.destination == queue_name and item.source == exchange_name)
            for item in listed.items
        )


@pytest.mark.integration
def test_binding_audit_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    logs: list[tuple[str, dict[str, object]]] = []

    class CaptureLogger:
        def bind(self, **_: object) -> CaptureLogger:
            return self

        def info(self, event: str, **fields: object) -> None:
            logs.append((event, fields))

        def debug(self, *_: object, **__: object) -> None:
            return None

    monkeypatch.setattr(bindings, "get_logger", lambda _: CaptureLogger())

    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "audit.exchange"
        queue_name = "audit.queue"

        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        binding = bindings.create_binding(
            "/", exchange_name, queue_name, "route", None, settings=settings
        )
        bindings.delete_binding(
            "/", exchange_name, queue_name, binding.properties_key or "", settings=settings
        )

    events = [event for event, _ in logs]
    assert "binding.create.success" in events
    assert "binding.delete.success" in events


@pytest.mark.integration
def test_binding_authorization_error_propagated() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        settings.user = "wrong"
        settings.password = "wrong"

        with pytest.raises(AuthorizationError):
            bindings.list_bindings(page=1, pageSize=10, settings=settings)


@pytest.mark.integration
def test_binding_concurrent_create_same_binding() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "concurrent.exchange"
        queue_name = "concurrent.queue"

        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        barrier = threading.Barrier(3)

        def create_binding_task() -> None:
            barrier.wait()
            try:
                bindings.create_binding(
                    "/", exchange_name, queue_name, "route", None, settings=settings
                )
            except ConflictError:
                pass

        threads = [threading.Thread(target=create_binding_task) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()

        listed = bindings.list_bindings(page=1, pageSize=10, settings=settings)
        matches = [
            item
            for item in listed.items
            if item.destination == queue_name and item.source == exchange_name
        ]
        assert len(matches) == 1


@pytest.mark.integration
def test_binding_concurrent_create_and_delete() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "race.binding.exchange"
        queue_name = "race.binding.queue"

        exchanges.create_exchange(
            "/", exchange_name, "topic", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        barrier = threading.Barrier(3)

        def create_binding_task() -> None:
            barrier.wait()
            try:
                bindings.create_binding(
                    "/", exchange_name, queue_name, "route.created", None, settings=settings
                )
            except ConflictError:
                pass

        def delete_binding_task() -> None:
            barrier.wait()
            try:
                current = bindings.list_bindings(page=1, pageSize=10, settings=settings)
                for item in current.items:
                    if (
                        item.source == exchange_name
                        and item.destination == queue_name
                        and item.properties_key
                    ):
                        bindings.delete_binding(
                            "/", exchange_name, queue_name, item.properties_key, settings=settings
                        )
                        break
            except (NotFoundError, ConflictError, ValidationError):
                pass

        # Seed an initial binding so deletion has a target
        seed_binding = bindings.create_binding(
            "/", exchange_name, queue_name, "route.created", None, settings=settings
        )
        assert seed_binding.properties_key

        threads = [
            threading.Thread(target=create_binding_task),
            threading.Thread(target=delete_binding_task),
        ]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()

        listed = bindings.list_bindings(page=1, pageSize=10, settings=settings)
        matches = [
            item
            for item in listed.items
            if item.source == exchange_name and item.destination == queue_name
        ]
        assert len(matches) <= 1


@pytest.mark.integration
def test_binding_missing_resources_errors() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        with pytest.raises(NotFoundError) as exc_exchange:
            bindings.create_binding(
                "/", "missing.exchange", "missing.queue", "", None, settings=settings
            )
        assert exc_exchange.value.code == "RESOURCES_NOT_FOUND"

        exchanges.create_exchange(
            "/", "only.exchange", "fanout", exchanges.ExchangeOptions(), settings=settings
        )
        with pytest.raises(NotFoundError) as exc_queue:
            bindings.create_binding(
                "/", "only.exchange", "missing.queue", "", None, settings=settings
            )
        assert exc_queue.value.code == "QUEUE_NOT_FOUND"

        queues.create_queue("/", "only.queue", queues.QueueOptions(), settings=settings)
        with pytest.raises(NotFoundError) as exc_missing_exchange:
            bindings.create_binding(
                "/", "missing.exchange.2", "only.queue", "", None, settings=settings
            )
        assert exc_missing_exchange.value.code == "EXCHANGE_NOT_FOUND"


@pytest.mark.integration
def test_binding_delete_requires_properties_key() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        exchange_name = "missing.key.exchange"
        queue_name = "missing.key.queue"

        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)

        with pytest.raises(ValidationError) as exc:
            bindings.delete_binding(
                "/", exchange_name, queue_name, cast(str, None), settings=settings
            )
        assert exc.value.code == "MISSING_PROPERTIES_KEY"
