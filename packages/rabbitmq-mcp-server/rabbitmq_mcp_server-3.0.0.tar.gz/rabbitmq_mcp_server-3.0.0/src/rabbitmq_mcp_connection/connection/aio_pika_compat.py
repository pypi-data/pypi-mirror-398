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

"""Compatibility layer that provides aio-pika or a fallback stub during tests."""

from types import SimpleNamespace
from typing import Any

AIO_PIKA_IMPORT_ERROR: Exception | None = None

try:  # pragma: no cover - real dependency path
    import aio_pika as _aio_pika

    AIO_PIKA_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - dependency missing
    AIO_PIKA_IMPORT_ERROR = exc
    import_exc = exc  # Store for use in closure

    class _ProbableAuthenticationError(Exception):
        """Fallback exception matching aio-pika signature."""

    def _missing_connect_robust(*_: Any, **__: Any) -> None:
        raise RuntimeError(
            "aio-pika is required for asynchronous RabbitMQ connections. "
            "Install the 'aio-pika' dependency or the 'dev' extra to enable this feature."
        ) from import_exc

    _aio_pika = SimpleNamespace(
        connect_robust=_missing_connect_robust,
        RobustConnection=object,
        exceptions=SimpleNamespace(ProbableAuthenticationError=_ProbableAuthenticationError),
        abc=SimpleNamespace(AbstractChannel=object, AbstractConnection=object),
    )
    RobustConnection = Any
    AbstractChannel = Any
    AbstractConnection = Any
else:  # pragma: no cover - dependency available
    AIO_PIKA_IMPORT_ERROR = None
    from aio_pika import RobustConnection as _RobustConnection
    from aio_pika.abc import AbstractChannel as _AbstractChannel
    from aio_pika.abc import AbstractConnection as _AbstractConnection

    RobustConnection = _RobustConnection
    AbstractChannel = _AbstractChannel
    AbstractConnection = _AbstractConnection


aio_pika = _aio_pika

__all__ = [
    "aio_pika",
    "RobustConnection",
    "AbstractChannel",
    "AbstractConnection",
    "AIO_PIKA_IMPORT_ERROR",
]
