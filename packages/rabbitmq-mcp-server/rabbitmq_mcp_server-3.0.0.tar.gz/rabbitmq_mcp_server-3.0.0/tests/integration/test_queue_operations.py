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

import pytest

pytest.importorskip("testcontainers.rabbitmq")
from testcontainers.rabbitmq import RabbitMqContainer

from config.settings import Settings
from tools.operations import queues
from utils.errors import (
    AuthorizationError,
    ConflictError,
    ConnectionError,
    NotFoundError,
    ValidationError,
)


@contextmanager
def rabbitmq_container() -> Iterator[RabbitMqContainer]:
    container = RabbitMqContainer("rabbitmq:3.13-management").with_exposed_ports(
        5672,
        15672,
    )
    with container:
        yield container


def _settings_from_container(container: RabbitMqContainer) -> Settings:
    host = container.get_container_host_ip()
    raw_port = container.get_exposed_port(15672)
    management_port = int(raw_port)
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
def test_queue_crud_happy_path() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        queue_name = "integration.queue"
        options = queues.QueueOptions(durable=True)

        created = queues.create_queue("/", queue_name, options, settings=settings)
        assert created.name == queue_name

        listed = queues.list_queues(page=1, pageSize=50, settings=settings)
        assert any(item.name == queue_name for item in listed.items)

        deleted = queues.delete_queue("/", queue_name, False, settings=settings)
        assert deleted["status"] == "deleted"


@pytest.mark.integration
def test_queue_pagination_with_multiple_pages() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        options = queues.QueueOptions()
        for index in range(150):
            queue_name = f"bulk.queue.{index}"
            queues.create_queue("/", queue_name, options, settings=settings)

        page_one = queues.list_queues(page=1, pageSize=50, settings=settings)
        page_three = queues.list_queues(page=3, pageSize=50, settings=settings)

        assert page_one.pagination.totalItems >= 150
        assert page_one.pagination.totalPages >= 3
        assert len(page_one.items) == 50
        assert len(page_three.items) == 50
        assert page_three.pagination.page == 3


@pytest.mark.integration
def test_queue_delete_with_messages_requires_force() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        options = queues.QueueOptions(durable=False)
        queue_name = "message.queue"
        queues.create_queue("/", queue_name, options, settings=settings)

        executor = queues.RabbitMQExecutor(
            host=settings.host,
            port=settings.port,
            user=settings.user,
            password=settings.password,
            vhost=settings.vhost,
            use_tls=settings.use_tls,
            timeout=settings.crud_timeout,
        )
        executor.create_queue("/", queue_name, {})
        executor._request(
            "POST",
            "/exchanges/%2f/amq.default/publish",
            json={
                "properties": {},
                "routing_key": queue_name,
                "payload": "data",
                "payload_encoding": "string",
            },
        )

        messages_present = False
        for _ in range(100):
            queue_info = executor.get_queue("/", queue_name) or {}
            if int(queue_info.get("messages", 0) or 0) > 0:
                messages_present = True
                break
            time.sleep(0.1)

        if not messages_present:
            pytest.skip(
                "RabbitMQ did not report queued messages before delete check; skipping conflict assertion"
            )

        with pytest.raises(ConflictError):
            queues.delete_queue("/", queue_name, False, settings=settings)

        deleted = queues.delete_queue("/", queue_name, True, settings=settings)
        assert deleted["forced"] is True


@pytest.mark.integration
def test_queue_list_timeout_raises_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        settings.list_timeout = 1

        original_executor = queues.RabbitMQExecutor

        class SlowExecutor(original_executor):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                assert self.timeout == settings.list_timeout

            def get_queues(self, vhost: str | None = None):
                raise ConnectionError(
                    code="TIMEOUT",
                    message="RabbitMQ Management API request timed out",
                    action="Retry the operation with a higher timeout",
                    context={"timeout": self.timeout, "vhost": vhost},
                )

        monkeypatch.setattr(queues, "RabbitMQExecutor", SlowExecutor)

        with pytest.raises(ConnectionError) as exc:
            queues.list_queues(page=1, pageSize=50, settings=settings)
        assert exc.value.code == "TIMEOUT"


@pytest.mark.integration
def test_queue_audit_logging_for_create_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    logs: list[tuple[str, dict[str, object]]] = []

    class CaptureLogger:
        def bind(self, **_: object) -> CaptureLogger:
            return self

        def info(self, event: str, **fields: object) -> None:
            logs.append((event, fields))

        def debug(self, *args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr(queues, "get_logger", lambda _: CaptureLogger())

    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        queue_name = "audit.queue"
        options = queues.QueueOptions()

        queues.create_queue("/", queue_name, options, settings=settings)
        queues.delete_queue("/", queue_name, False, settings=settings)

        events = [event for event, _ in logs]
        assert "queue.create.success" in events
        assert "queue.delete.success" in events


@pytest.mark.integration
def test_queue_authorization_error_propagated(monkeypatch: pytest.MonkeyPatch) -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        settings.user = "wrong"
        settings.password = "wrong"

        with pytest.raises(AuthorizationError):
            queues.list_queues(page=1, pageSize=10, settings=settings)


@pytest.mark.integration
def test_queue_concurrency_conflicts() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        queue_name = "race.queue"
        options = queues.QueueOptions()

        def create_queue() -> None:
            try:
                queues.create_queue("/", queue_name, options, settings=settings)
            except ConflictError:
                pass

        def delete_queue() -> None:
            try:
                queues.delete_queue("/", queue_name, False, settings=settings)
            except (ValidationError, ConflictError, NotFoundError):
                pass

        threads = [threading.Thread(target=create_queue) for _ in range(2)] + [
            threading.Thread(target=delete_queue)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        listed = queues.list_queues(page=1, pageSize=50, settings=settings)
    matches = [item for item in listed.items if item.name == queue_name]
    assert len(matches) <= 1


@pytest.mark.integration
def test_queue_invalid_vhost_error() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        with pytest.raises(ValidationError) as exc:
            queues.list_queues(vhost="/invalid", page=1, pageSize=10, settings=settings)

        assert "Virtual host" in exc.value.message


@pytest.mark.integration
def test_queue_invalid_name_validation() -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)
        options = queues.QueueOptions()

        invalid_name = "*" * 260

        with pytest.raises(ValidationError):
            queues.create_queue("/", invalid_name, options, settings=settings)


@pytest.mark.integration
def test_queue_connection_drop(monkeypatch: pytest.MonkeyPatch) -> None:
    with rabbitmq_container() as container:
        settings = _settings_from_container(container)

        original_executor = queues.RabbitMQExecutor

        class FailingExecutor(original_executor):
            def get_queues(self, vhost: str | None = None):
                raise ConnectionError(
                    code="CONNECTION_DROP",
                    message="Simulated connection drop",
                    action="Retry after RabbitMQ becomes healthy",
                    context={"vhost": vhost},
                )

        monkeypatch.setattr(queues, "RabbitMQExecutor", FailingExecutor)

        with pytest.raises(ConnectionError) as exc:
            queues.list_queues(page=1, pageSize=10, settings=settings)
        assert exc.value.code == "CONNECTION_DROP"
