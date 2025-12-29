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

import asyncio
import re
from unittest import mock

import pytest

from src.logging.correlation import (
    generate_correlation_id,
    get_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)


@pytest.fixture(autouse=True)
def _reset_context():
    reset_correlation_id()
    yield
    reset_correlation_id()


UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def test_generate_correlation_id_returns_uuid_v4():
    correlation_id = generate_correlation_id()
    assert UUID_REGEX.match(correlation_id)


def test_generate_correlation_id_fallback_when_uuid_fails():
    with mock.patch("uuid.uuid4", side_effect=RuntimeError("fail")):
        correlation_id = generate_correlation_id()
    assert correlation_id
    assert correlation_id != "fail"
    # fallback usa timestamp com hyphen
    assert "-" in correlation_id


def test_get_correlation_id_returns_none_when_not_set():
    assert get_correlation_id() is None


def test_set_correlation_id_generates_and_returns_value():
    generated = set_correlation_id()
    assert generated == get_correlation_id()
    assert UUID_REGEX.match(generated)


def test_set_correlation_id_accepts_explicit_value():
    set_correlation_id("abc123")
    assert get_correlation_id() == "abc123"


def test_multiple_operations_have_different_ids():
    first = set_correlation_id()
    reset_correlation_id()
    second = set_correlation_id()

    assert first != second
    assert UUID_REGEX.match(first)
    assert UUID_REGEX.match(second)


def test_nested_operations_share_correlation_id():
    outer = set_correlation_id("outer-id")

    def nested_operation():
        return get_correlation_id()

    nested_id = nested_operation()

    assert nested_id == outer
    assert get_correlation_id() == outer


@pytest.mark.asyncio
async def test_correlation_id_isolated_between_async_tasks():
    async def worker(prefix: str):
        value = set_correlation_id(f"{prefix}-{prefix}")
        await asyncio.sleep(0)
        return value, get_correlation_id()

    first, second = await asyncio.gather(worker("first"), worker("second"))

    assert first[0] == "first-first"
    assert first[1] == "first-first"
    assert second[0] == "second-second"
    assert second[1] == "second-second"
    assert first != second


@pytest.mark.asyncio
async def test_generate_correlation_id_propagates_through_awaits():
    async def nested():
        await asyncio.sleep(0)
        return get_correlation_id()

    set_correlation_id("outer")
    result = await nested()
    assert result == "outer"
    assert get_correlation_id() == "outer"
