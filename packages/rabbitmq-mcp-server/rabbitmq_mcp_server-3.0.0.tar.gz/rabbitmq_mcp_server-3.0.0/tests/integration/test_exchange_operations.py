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
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

pytest.importorskip("testcontainers.rabbitmq")
from testcontainers.rabbitmq import RabbitMqContainer

from config.settings import Settings
from tools.operations import bindings, exchanges, queues
from utils.errors import AuthorizationError, ConflictError, NotFoundError


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


@pytest.mark.integration
def test_exchange_create_types() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        options = exchanges.ExchangeOptions(durable=True)
        headers_options = exchanges.ExchangeOptions(durable=True, arguments={"format": "json"})
        created_names = []

        for name, exchange_type, opts in [
            ("integration.direct.exchange", "direct", options),
            ("integration.topic.exchange", "topic", options),
            ("integration.fanout.exchange", "fanout", options),
            ("integration.headers.exchange", "headers", headers_options),
        ]:
            created = exchanges.create_exchange("/", name, exchange_type, opts, settings=settings)
            assert created.name == name
            assert created.type == exchange_type
            created_names.append(name)

        listed = exchanges.list_exchanges(page=1, pageSize=200, settings=settings)
        assert all(any(item.name == name for item in listed.items) for name in created_names)


@pytest.mark.integration
def test_exchange_pagination_with_multiple_pages() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        options = exchanges.ExchangeOptions()
        for index in range(0, 160):
            exchanges.create_exchange(
                "/", f"bulk.exchange.{index}", "direct", options, settings=settings
            )

        page_one = exchanges.list_exchanges(page=1, pageSize=50, settings=settings)
        page_three = exchanges.list_exchanges(page=3, pageSize=50, settings=settings)

        assert page_one.pagination.totalItems >= 150
        assert page_one.pagination.totalPages >= 3
        assert len(page_one.items) == 50
        assert page_three.pagination.page == 3
        assert 0 < len(page_three.items) <= 50


@pytest.mark.integration
def test_exchange_delete_blocked_when_bindings_exist() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        exchange_name = "binding.protected.exchange"
        queue_name = "binding.protected.queue"
        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        queues.create_queue("/", queue_name, queues.QueueOptions(), settings=settings)
        bindings.create_binding("/", exchange_name, queue_name, "route", None, settings=settings)

        with pytest.raises(ConflictError) as exc:
            exchanges.delete_exchange("/", exchange_name, settings=settings)
        assert exc.value.code == "EXCHANGE_HAS_BINDINGS"


@pytest.mark.integration
def test_exchange_delete_without_bindings_succeeds() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        exchange_name = "deletable.exchange"
        exchanges.create_exchange(
            "/", exchange_name, "fanout", exchanges.ExchangeOptions(), settings=settings
        )

        result = exchanges.delete_exchange("/", exchange_name, settings=settings)
        assert result["status"] == "deleted"
        assert result["binding_count"] == 0


@pytest.mark.integration
def test_exchange_audit_logging_for_create_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    logs: list[tuple[str, dict[str, object]]] = []

    class CaptureLogger:
        def bind(self, **_: object) -> CaptureLogger:
            return self

        def info(self, event: str, **fields: object) -> None:
            logs.append((event, fields))

        def debug(self, *_: object, **__: object) -> None:
            return None

    monkeypatch.setattr(exchanges, "get_logger", lambda _: CaptureLogger())

    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        exchange_name = "audit.exchange"
        exchanges.create_exchange(
            "/", exchange_name, "direct", exchanges.ExchangeOptions(), settings=settings
        )
        exchanges.delete_exchange("/", exchange_name, settings=settings)

        events = [event for event, _ in logs]
        assert "exchange.create.success" in events
        assert "exchange.delete.success" in events


@pytest.mark.integration
def test_exchange_authorization_error_propagated() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        settings.user = "wrong"
        settings.password = "wrong"

        with pytest.raises(AuthorizationError):
            exchanges.list_exchanges(page=1, pageSize=10, settings=settings)


@pytest.mark.integration
def test_exchange_concurrent_create_and_delete() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        exchange_name = "race.exchange"
        options = exchanges.ExchangeOptions()

        def create_exchange() -> None:
            try:
                exchanges.create_exchange("/", exchange_name, "direct", options, settings=settings)
            except ConflictError:
                pass

        def delete_exchange() -> None:
            try:
                exchanges.delete_exchange("/", exchange_name, settings=settings)
            except (ConflictError, NotFoundError):
                pass

        threads = [threading.Thread(target=create_exchange) for _ in range(2)] + [
            threading.Thread(target=delete_exchange)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        listed = exchanges.list_exchanges(page=1, pageSize=200, settings=settings)
    matches = [item for item in listed.items if item.name == exchange_name]
    assert len(matches) <= 1


@pytest.mark.integration
def test_exchange_duplicate_create_conflict() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        exchange_name = "duplicate.exchange"
        options = exchanges.ExchangeOptions()

        def attempt_create() -> None:
            try:
                exchanges.create_exchange("/", exchange_name, "topic", options, settings=settings)
            except ConflictError:
                pass

        threads = [threading.Thread(target=attempt_create) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        listed = exchanges.list_exchanges(page=1, pageSize=100, settings=settings)
    matches = [item for item in listed.items if item.name == exchange_name]
    assert len(matches) == 1


@pytest.mark.integration
def test_exchange_system_exchange_deletion_blocked() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        for name in ["amq.direct", ""]:
            with pytest.raises(ConflictError) as exc:
                exchanges.delete_exchange("/", name, settings=settings)
            assert exc.value.code == "SYSTEM_EXCHANGE"
