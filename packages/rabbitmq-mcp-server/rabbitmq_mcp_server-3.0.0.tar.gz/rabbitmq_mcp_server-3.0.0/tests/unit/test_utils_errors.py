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

import pytest

from utils.errors import (
    AuthorizationError,
    ConflictError,
    ConnectionError,
    NotFoundError,
    RabbitMQError,
    ValidationError,
    format_error,
)


def test_validation_error_to_dict_and_message() -> None:
    error = ValidationError(
        code="INVALID_NAME",
        message="Queue name contains illegal characters",
        field="name",
        expected="alphanumeric, dot, dash or underscore (<=255)",
        actual="orders queue",
        action="Remove spaces or special characters",
        context={"operation": "queues.create"},
    )

    data = error.to_dict()

    assert data["code"] == "INVALID_NAME"
    assert data["message"] == "Queue name contains illegal characters"
    assert data["field"] == "name"
    assert data["expected"].startswith("alphanumeric")
    assert data["actual"] == "orders queue"
    assert data["action"].startswith("Remove")
    assert data["context"] == {"operation": "queues.create"}
    assert "INVALID_NAME" in error.to_user_message()
    assert "Remove" in error.to_user_message()


def test_format_error_passthrough() -> None:
    error = AuthorizationError(
        code="UNAUTHORIZED",
        message="Credentials rejected",
        action="Verify RabbitMQ credentials",
    )

    assert format_error(error) is error


@pytest.mark.parametrize(
    "error_cls, kwargs",
    [
        (AuthorizationError, {"code": "UNAUTHORIZED", "message": "denied", "action": "Retry"}),
        (NotFoundError, {"code": "NOT_FOUND", "message": "missing", "action": "Create resource"}),
        (ConflictError, {"code": "CONFLICT", "message": "conflict", "action": "Resolve"}),
        (
            ConnectionError,
            {"code": "NETWORK_ERROR", "message": "offline", "action": "Check network"},
        ),
    ],
)
def test_error_subclasses_provide_required_fields(
    error_cls: type[RabbitMQError], kwargs: dict[str, str]
) -> None:
    error = error_cls(
        field="resource", expected="value", actual="other", context={"test": True}, **kwargs
    )

    as_dict = error.to_dict()

    assert as_dict["code"] == kwargs["code"]
    assert as_dict["field"] == "resource"
    assert as_dict["expected"] == "value"
    assert as_dict["actual"] == "other"
    assert as_dict["action"] == kwargs["action"]
    assert as_dict["context"] == {"test": True}
    message = error.to_user_message()
    assert kwargs["code"] in message
    assert "Action" in message


def test_format_error_from_value_error() -> None:
    value_error = ValueError("page must be >= 1")

    formatted = format_error(value_error)

    assert isinstance(formatted, ValidationError)
    assert formatted.code == "INVALID_INPUT"
    assert formatted.message == "page must be >= 1"


@pytest.mark.parametrize(
    "exception, expected_code",
    [
        (PermissionError("denied"), "UNAUTHORIZED"),
        (RuntimeError("boom"), "UNHANDLED_ERROR"),
    ],
)
def test_format_error_for_other_exceptions(exception: Exception, expected_code: str) -> None:
    formatted = format_error(exception)
    assert isinstance(formatted, RabbitMQError)
    assert formatted.code == expected_code


def test_format_error_unknown_exception_includes_context() -> None:
    class CustomError(Exception):
        pass

    formatted = format_error(CustomError("boom"))

    assert formatted.code == "UNHANDLED_ERROR"
    assert formatted.context["exception"] == "CustomError"
