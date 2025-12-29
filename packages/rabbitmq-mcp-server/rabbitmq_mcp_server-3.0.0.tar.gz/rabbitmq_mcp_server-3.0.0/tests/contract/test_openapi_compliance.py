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

from collections.abc import Iterable
from functools import cache
from pathlib import Path
from typing import Any

import pytest

from src.tools.openapi.operation_registry import OperationRegistry
from src.tools.openapi.parser import parse_openapi_spec
from src.tools.operations import bindings, exchanges, queues

ALLOWED_SUCCESS_SCHEMAS = {
    "SuccessResponse",
    "PaginatedQueueResponse",
    "PaginatedExchangeResponse",
    "PaginatedBindingResponse",
    "Queue",
    "Exchange",
    "Binding",
}

CONTRACTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "003-essential-topology-operations"
    / "contracts"
)
CONTRACT_FILES = {
    "queues": CONTRACTS_DIR / "queue-operations.yaml",
    "exchanges": CONTRACTS_DIR / "exchange-operations.yaml",
    "bindings": CONTRACTS_DIR / "binding-operations.yaml",
}
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


@cache
def _load_spec(contract: str) -> dict[str, Any]:
    path = CONTRACT_FILES[contract]
    return parse_openapi_spec(str(path))


def _iter_operations(spec: dict[str, Any]) -> Iterable[tuple[str, str, dict[str, Any]]]:
    for api_path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if method not in HTTP_METHODS:
                continue
            yield api_path, method, operation


def test_all_operation_ids_are_registered() -> None:
    registry = OperationRegistry([str(path) for path in CONTRACT_FILES.values()])

    for contract in CONTRACT_FILES:
        spec = _load_spec(contract)
        for api_path, method, operation in _iter_operations(spec):
            op_id = operation.get("operationId")
            assert op_id, f"Missing operationId for {api_path} {method} in {contract}"
            assert (
                registry.get_operation(op_id) is not None
            ), f"Operation '{op_id}' from {contract} not available in registry"


@pytest.mark.parametrize(
    ("contract", "path", "method"),
    [
        ("queues", "/queues", "get"),
        ("exchanges", "/exchanges", "get"),
        ("bindings", "/bindings", "get"),
    ],
)
def test_list_operations_include_pagination(contract: str, path: str, method: str) -> None:
    spec = _load_spec(contract)
    operation = spec["paths"][path][method]

    param_names = {param["name"] for param in operation.get("parameters", [])}
    assert {"page", "pageSize"}.issubset(
        param_names
    ), f"Pagination params missing in {contract} {path}"

    schema_info = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert (
        schema_info["$ref"].split("/")[-1].startswith("Paginated")
    ), f"List response in {contract} {path} must use paginated schema"


@pytest.mark.parametrize(
    ("contract", "path", "method", "model"),
    [
        ("queues", "/queues", "get", queues.PaginatedQueueResponse),
        (
            "exchanges",
            "/exchanges",
            "get",
            exchanges.PaginatedExchangeResponse,
        ),
        ("bindings", "/bindings", "get", bindings.PaginatedBindingResponse),
    ],
)
def test_paginated_response_examples_validate(
    contract: str, path: str, method: str, model: Any
) -> None:
    spec = _load_spec(contract)
    example = spec["paths"][path][method]["responses"]["200"]["content"]["application/json"][
        "example"
    ]
    instance = model.model_validate(example)
    assert instance.pagination.page >= 1
    assert instance.pagination.pageSize >= 1


@pytest.mark.parametrize(
    ("contract", "path", "method"),
    [
        ("queues", "/queues/{vhost}/{name}", "put"),
        ("exchanges", "/exchanges/{vhost}/{name}", "put"),
        ("bindings", "/bindings/{vhost}/e/{exchange}/q/{queue}", "post"),
    ],
)
def test_request_examples_align_with_supported_payloads(
    contract: str, path: str, method: str
) -> None:
    spec = _load_spec(contract)
    request_body = spec["paths"][path][method]["requestBody"]["content"]["application/json"]

    if "example" in request_body:
        example = request_body["example"]
        if contract == "queues":
            queues.QueueOptions.model_validate(example)
        elif contract == "exchanges":
            exchange_type = example.get("type")
            assert exchange_type in {"direct", "topic", "fanout", "headers"}
            exchanges.ExchangeOptions.model_validate(
                {k: v for k, v in example.items() if k != "type"}
            )
    else:
        examples = request_body.get("examples", {})
        assert examples, f"Expected examples for {contract} {path}"
        for payload in examples.values():
            value = payload["value"]
            assert set(value.keys()) <= {"routing_key", "arguments"}


def test_pagination_metadata_schema_matches_model() -> None:
    spec = _load_spec("queues")
    metadata_schema = spec["components"]["schemas"]["PaginationMetadata"]
    spec_fields = set(metadata_schema["properties"].keys())
    model_fields = set(queues.PaginationMetadata.model_fields.keys())
    assert spec_fields == model_fields
    assert set(metadata_schema["required"]) == model_fields


def test_success_responses_reference_known_components() -> None:
    for contract in CONTRACT_FILES:
        spec = _load_spec(contract)
        for api_path, _method, operation in _iter_operations(spec):
            for status, response in operation.get("responses", {}).items():
                if not status.startswith("2"):
                    continue
                content = response.get("content")
                if not content:
                    continue
                schema = content.get("application/json", {}).get("schema")
                if not schema:
                    continue
                ref = schema.get("$ref")
                assert ref, f"Expected $ref in success schema for {contract} {api_path}"
                target = ref.split("/")[-1]
                assert (
                    target in ALLOWED_SUCCESS_SCHEMAS
                ), f"Unexpected success schema '{target}' in {contract} {api_path} {status}"
