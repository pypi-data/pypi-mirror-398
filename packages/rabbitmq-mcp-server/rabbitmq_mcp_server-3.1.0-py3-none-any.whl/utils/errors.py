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

"""Standardized error types for RabbitMQ MCP server."""

from typing import Any

__all__ = [
    "RabbitMQError",
    "ValidationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "ConnectionError",
    "format_error",
]


class RabbitMQError(Exception):
    """Base error carrying structured details according to FR-025."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        field: str | None = None,
        expected: str | None = None,
        actual: str | None = None,
        action: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
        self.expected = expected
        self.actual = actual
        self.action = action
        self.context: dict[str, Any] = context.copy() if context else {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "action": self.action,
            "context": self.context,
        }

    def to_user_message(self) -> str:
        parts: list[str] = [f"[{self.code}] {self.message}"]
        if self.field and (self.expected or self.actual):
            expected = f"expected {self.expected}" if self.expected else None
            actual = f"got {self.actual}" if self.actual else None
            expectation = ", ".join(filter(None, [expected, actual]))
            parts.append(f"Field '{self.field}' {expectation}.".rstrip())
        if self.action:
            parts.append(f"Action: {self.action}")
        return " ".join(parts)


class ValidationError(RabbitMQError):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class AuthorizationError(RabbitMQError):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class NotFoundError(RabbitMQError):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class ConflictError(RabbitMQError):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class ConnectionError(RabbitMQError):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


def format_error(error: Exception) -> RabbitMQError:
    """Normalize generic exceptions to RabbitMQError hierarchy."""

    if isinstance(error, RabbitMQError):
        return error

    if isinstance(error, ValueError):
        return ValidationError(
            code="INVALID_INPUT",
            message=str(error) or "Invalid input provided",
            action="Adjust the input parameters and retry",
            context={"exception": error.__class__.__name__},
        )

    if isinstance(error, PermissionError):
        return AuthorizationError(
            code="UNAUTHORIZED",
            message=str(error) or "Authentication or authorization failed",
            action="Verify RabbitMQ credentials and permissions",
            context={"exception": error.__class__.__name__},
        )

    return RabbitMQError(
        code="UNHANDLED_ERROR",
        message=str(error) or "An unexpected error occurred",
        action="Check logs for full stack trace",
        context={"exception": error.__class__.__name__},
    )
