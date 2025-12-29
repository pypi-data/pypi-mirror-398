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

import logging
from typing import Any
from urllib.parse import quote

import requests
from requests import Session
from requests.exceptions import HTTPError

from utils.errors import (
    AuthorizationError,
    ConflictError,
    ConnectionError,
    NotFoundError,
    RabbitMQError,
    ValidationError,
)


class RabbitMQExecutor:
    """HTTP client responsible for interacting with the RabbitMQ Management API."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        vhost: str = "/",
        use_tls: bool = False,
        timeout: float = 5.0,
    ) -> None:
        scheme = "https" if use_tls else "http"
        self.base_url = f"{scheme}://{host}:{port}/api"
        self.session = Session()
        self.session.auth = (user, password)
        self.vhost = vhost
        self.timeout = timeout
        self.logger = logging.getLogger("RabbitMQExecutor")  # type: ignore[attr-defined]

    def _encode_vhost(self, vhost: str) -> str:
        return quote(vhost, safe="")

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:  # pragma: no cover - network failure path
            self.logger.error("HTTP request failed", exc_info=exc)
            raise ConnectionError(
                code="NETWORK_ERROR",
                message="Unable to reach RabbitMQ Management API",
                action="Verify network connectivity and API availability",
                context={"url": url, "method": method},
            ) from exc

        status_code = response.status_code
        if status_code in (401, 403):
            self.logger.warning("Unauthorized request to %s", endpoint)
            raise AuthorizationError(
                code="UNAUTHORIZED",
                message="RabbitMQ credentials were rejected",
                action="Verify username, password and permissions",
                context={"endpoint": endpoint, "status": status_code},
            )

        try:
            response.raise_for_status()
        except HTTPError as exc:
            error_context = {
                "endpoint": endpoint,
                "status": status_code,
                "method": method,
            }
            if status_code == 404:
                raise NotFoundError(
                    code="NOT_FOUND",
                    message="Requested resource was not found",
                    action="Ensure the target resource exists before retrying",
                    context=error_context,
                ) from exc
            if status_code == 409:
                raise ConflictError(
                    code="CONFLICT",
                    message="RabbitMQ reported a resource conflict",
                    action="Resolve existing resource state before retrying",
                    context=error_context,
                ) from exc
            if 400 <= status_code < 500:
                raise ValidationError(
                    code=f"HTTP_{status_code}",
                    message=response.text or "RabbitMQ rejected the request",
                    action="Adjust request parameters and retry",
                    context=error_context,
                ) from exc
            raise ConnectionError(
                code="REMOTE_ERROR",
                message="RabbitMQ Management API returned an error",
                action="Retry later or review RabbitMQ server logs",
                context=error_context,
            ) from exc

        if status_code == 204:
            return None

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - unexpected content type
            raise RabbitMQError(
                code="INVALID_RESPONSE",
                message="RabbitMQ responded with non-JSON payload",
                action="Inspect response payload for debugging",
                context={"endpoint": endpoint},
            ) from exc

    def get_queues(self, vhost: str | None = None) -> Any:
        if vhost is None:
            endpoint = "/queues"
        else:
            endpoint = f"/queues/{self._encode_vhost(vhost)}"
        return self._request("GET", endpoint)

    def get_exchanges(self, vhost: str | None = None) -> Any:
        if vhost is None:
            endpoint = "/exchanges"
        else:
            endpoint = f"/exchanges/{self._encode_vhost(vhost)}"
        return self._request("GET", endpoint)

    def get_bindings(self, vhost: str | None = None) -> Any:
        if vhost is None:
            endpoint = "/bindings"
        else:
            endpoint = f"/bindings/{self._encode_vhost(vhost)}"
        return self._request("GET", endpoint)

    def delete_queue(self, vhost: str, queue: str, force: bool = False) -> Any:
        params = {"if-empty": "false"} if force else {}
        endpoint = f"/queues/{self._encode_vhost(vhost)}/{quote(queue, safe='')}"
        return self._request("DELETE", endpoint, params=params)

    def get_queue(self, vhost: str, name: str) -> Any:
        endpoint = f"/queues/{self._encode_vhost(vhost)}/{quote(name, safe='')}"
        return self._request("GET", endpoint)

    def create_queue(self, vhost: str, name: str, payload: dict[str, Any]) -> Any:
        endpoint = f"/queues/{self._encode_vhost(vhost)}/{quote(name, safe='')}"
        return self._request("PUT", endpoint, json=payload)

    def get_exchange(self, vhost: str, name: str) -> Any:
        endpoint = f"/exchanges/{self._encode_vhost(vhost)}/{quote(name, safe='')}"
        return self._request("GET", endpoint)

    def create_exchange(self, vhost: str, name: str, payload: dict[str, Any]) -> Any:
        endpoint = f"/exchanges/{self._encode_vhost(vhost)}/{quote(name, safe='')}"
        return self._request("PUT", endpoint, json=payload)

    def delete_exchange(self, vhost: str, name: str) -> Any:
        endpoint = f"/exchanges/{self._encode_vhost(vhost)}/{quote(name, safe='')}"
        return self._request("DELETE", endpoint)

    def create_binding(
        self,
        vhost: str,
        exchange: str,
        queue: str,
        payload: dict[str, Any],
    ) -> Any:
        endpoint = (
            f"/bindings/{self._encode_vhost(vhost)}/e/{quote(exchange, safe='')}"
            f"/q/{quote(queue, safe='')}"
        )
        return self._request("POST", endpoint, json=payload)

    def list_binding_relations(self, vhost: str, exchange: str, queue: str) -> Any:
        endpoint = (
            f"/bindings/{self._encode_vhost(vhost)}/e/{quote(exchange, safe='')}"
            f"/q/{quote(queue, safe='')}"
        )
        return self._request("GET", endpoint)

    def get_bindings_for_exchange(self, vhost: str, exchange: str) -> Any:
        endpoint = (
            f"/exchanges/{self._encode_vhost(vhost)}/" f"{quote(exchange, safe='')}/bindings/source"
        )
        return self._request("GET", endpoint)

    def delete_binding(
        self,
        vhost: str,
        exchange: str,
        queue: str,
        properties_key: str,
    ) -> Any:
        endpoint = (
            f"/bindings/{self._encode_vhost(vhost)}/e/{quote(exchange, safe='')}"
            f"/q/{quote(queue, safe='')}/{quote(properties_key, safe='')}"
        )
        return self._request("DELETE", endpoint)
