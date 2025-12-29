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

from utils import validation
from utils.errors import AuthorizationError, ConnectionError, NotFoundError, ValidationError


class FakeExecutor:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}
        self.base_url = "http://localhost:15672/api"
        self.vhost = "/"
        self.raise_error: Exception | None = None

    def _encode_vhost(self, vhost: str) -> str:
        return vhost.replace("/", "%2F")

    def _request(self, method: str, endpoint: str, **_: Any) -> Any:
        key = f"{method} {endpoint}"
        self.calls[key] = self.calls.get(key, 0) + 1
        if self.raise_error:
            raise self.raise_error
        return {}


def setup_function(_: Any) -> None:
    validation.reset_vhost_cache()


def test_validate_name_success() -> None:
    validation.validate_name("orders.queue-1")


@pytest.mark.parametrize("value", ["orders queue", "", "!invalid", "a" * 256])
def test_validate_name_failure(value: str) -> None:
    with pytest.raises(ValidationError) as exc:
        validation.validate_name(value)
    assert exc.value.code == "INVALID_NAME"
    assert exc.value.field == "name"


@pytest.mark.parametrize(
    "exchange_type",
    ["direct", "topic", "fanout", "headers"],
)
def test_validate_exchange_type_success(exchange_type: str) -> None:
    validation.validate_exchange_type(exchange_type)


def test_validate_exchange_type_failure() -> None:
    with pytest.raises(ValidationError) as exc:
        validation.validate_exchange_type("invalid")
    assert exc.value.code == "INVALID_EXCHANGE_TYPE"
    assert exc.value.field == "type"


@pytest.mark.parametrize(
    "exchange_type, routing_key",
    [
        ("direct", "orders.*"),
        ("fanout", "#"),
        ("headers", "*"),
    ],
)
def test_validate_routing_key_invalid_for_non_topic(exchange_type: str, routing_key: str) -> None:
    with pytest.raises(ValidationError) as exc:
        validation.validate_routing_key(routing_key, exchange_type)
    assert exc.value.code == "INVALID_ROUTING_KEY"


@pytest.mark.parametrize(
    "exchange_type, routing_key",
    [
        ("topic", "orders.*"),
        ("topic", "orders.#"),
        ("direct", "orders.created"),
    ],
)
def test_validate_routing_key_allowed(exchange_type: str, routing_key: str) -> None:
    validation.validate_routing_key(routing_key, exchange_type)


def test_validate_vhost_exists_uses_cache() -> None:
    executor = FakeExecutor()
    validation.validate_vhost_exists("/", executor)  # type: ignore[arg-type]
    validation.validate_vhost_exists("/", executor)  # type: ignore[arg-type]

    # Only one HTTP call should happen due to 60s cache
    assert executor.calls["GET /vhosts/%2F"] == 1


def test_validate_vhost_exists_not_found() -> None:
    executor = FakeExecutor()
    executor.raise_error = NotFoundError(
        code="NOT_FOUND",
        message="Virtual host missing",
        action="Create vhost",
        context={"status": 404},
    )

    with pytest.raises(ValidationError) as exc:
        validation.validate_vhost_exists("/missing", executor)  # type: ignore[arg-type]

    assert exc.value.code == "VHOST_NOT_FOUND"


def test_validate_vhost_exists_auth_error_invalidates_cache() -> None:
    executor = FakeExecutor()
    auth_error = AuthorizationError(
        code="UNAUTHORIZED",
        message="Access denied",
        action="Update credentials",
    )
    executor.raise_error = auth_error

    with pytest.raises(AuthorizationError):
        validation.validate_vhost_exists("/secure", executor)  # type: ignore[arg-type]

    executor.raise_error = None
    validation.validate_vhost_exists("/secure", executor)  # type: ignore[arg-type]
    assert executor.calls["GET /vhosts/%2Fsecure"] == 2


def test_reset_vhost_cache_clears_cached_results() -> None:
    executor = FakeExecutor()
    validation.validate_vhost_exists("/", executor)  # type: ignore[arg-type]
    validation.reset_vhost_cache()

    executor.raise_error = NotFoundError(
        code="NOT_FOUND",
        message="missing",
        action="create",
    )

    with pytest.raises(ValidationError) as exc:
        validation.validate_vhost_exists("/", executor)  # type: ignore[arg-type]

    assert exc.value.code == "VHOST_NOT_FOUND"


def test_validate_vhost_exists_propagates_connection_error() -> None:
    executor = FakeExecutor()
    connection_error = ConnectionError(
        code="NETWORK_ERROR",
        message="offline",
        action="Retry",
    )
    executor.raise_error = connection_error

    with pytest.raises(ConnectionError) as exc:
        validation.validate_vhost_exists("/", executor)  # type: ignore[arg-type]

    assert exc.value is connection_error


def test_validate_vhost_exists_wraps_unexpected_exception() -> None:
    executor = FakeExecutor()
    executor.raise_error = RuntimeError("boom")

    with pytest.raises(ConnectionError) as exc:
        validation.validate_vhost_exists("/", executor)  # type: ignore[arg-type]

    assert exc.value.code == "CONNECTION_ERROR"
