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
from unittest import mock

import pytest

from src.utils.async_writer import AsyncLogWriter


@pytest.mark.asyncio
async def test_async_log_writer_writes_items_in_order():
    sink = []

    async def fake_write(batch):
        sink.extend(batch)

    writer = AsyncLogWriter(
        max_queue_size=2, batch_size=1, flush_interval=0.1, write_batch=fake_write
    )
    await writer.start()

    await writer.write_log({"id": 1})
    await writer.write_log({"id": 2})

    await asyncio.wait_for(writer.flush(), timeout=1)
    await writer.stop()

    assert sink == [{"id": 1}, {"id": 2}]


@pytest.mark.asyncio
async def test_async_log_writer_blocks_when_queue_full(monkeypatch):
    sink = []
    block_event = asyncio.Event()

    async def slow_write(batch):
        sink.extend(batch)
        await block_event.wait()

    writer = AsyncLogWriter(
        max_queue_size=1, batch_size=1, flush_interval=0.1, write_batch=slow_write
    )

    original_get = writer._queue.get

    async def gated_get():  # type: ignore[override]
        await block_event.wait()
        return await original_get()

    monkeypatch.setattr(writer._queue, "get", gated_get)

    await writer.start()

    first_task = asyncio.create_task(writer.write_log({"id": "first"}))
    second_task = asyncio.create_task(writer.write_log({"id": "second"}))

    await asyncio.sleep(0)
    assert first_task.done()  # primeiro item pode entrar na fila
    assert not second_task.done()  # segundo deve aguardar capacidade

    block_event.set()
    await asyncio.wait_for(first_task, timeout=1)
    await asyncio.wait_for(second_task, timeout=1)
    await asyncio.wait_for(writer.flush(), timeout=1)
    await writer.stop()

    assert sink == [{"id": "first"}, {"id": "second"}]


@pytest.mark.asyncio
async def test_async_log_writer_batches_entries():
    batches = []

    async def capture_write(batch):
        batches.append(list(batch))

    writer = AsyncLogWriter(
        max_queue_size=10, batch_size=3, flush_interval=0.1, write_batch=capture_write
    )
    await writer.start()

    await writer.write_log({"id": 1})
    await writer.write_log({"id": 2})
    await writer.write_log({"id": 3})

    await asyncio.wait_for(writer.flush(), timeout=1)
    await writer.stop()

    assert batches == [[{"id": 1}, {"id": 2}, {"id": 3}]]


@pytest.mark.asyncio
async def test_async_log_writer_flush_interval_triggers():
    batches = []

    async def capture(batch):
        batches.extend(batch)

    writer = AsyncLogWriter(
        max_queue_size=10, batch_size=10, flush_interval=0.05, write_batch=capture
    )
    await writer.start()

    await writer.write_log({"id": 1})
    await asyncio.sleep(0.1)  # allow flush interval to trigger

    await asyncio.wait_for(writer.stop(), timeout=1)

    assert batches == [{"id": 1}]


@pytest.mark.asyncio
async def test_async_log_writer_stop_drains_queue():
    sink = []

    async def capture(batch):
        sink.extend(batch)

    writer = AsyncLogWriter(
        max_queue_size=10, batch_size=5, flush_interval=0.1, write_batch=capture
    )
    await writer.start()

    for i in range(7):
        await writer.write_log({"id": i})

    await asyncio.wait_for(writer.stop(), timeout=1)

    assert len(sink) == 7


@pytest.mark.asyncio
async def test_async_log_writer_prevents_multiple_starts():
    writer = AsyncLogWriter(write_batch=mock.AsyncMock())
    await writer.start()

    with pytest.raises(RuntimeError):
        await writer.start()

    await writer.stop()


@pytest.mark.asyncio
async def test_async_log_writer_handles_stop_without_start():
    writer = AsyncLogWriter(write_batch=mock.AsyncMock())

    # stop before start should be harmless
    await writer.stop()
