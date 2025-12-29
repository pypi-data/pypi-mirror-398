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

import time
from collections.abc import Callable, Iterable
from pathlib import Path

import pytest

import src.logging.logger as logger_module
from src.logging.handlers import file as file_module
from src.logging.logger import (
    StructuredLogger,
    get_logger,
    reset_structlog_configuration,
    shutdown_all_loggers,
)
from src.models.log_config import LogConfig, LogLevel
from src.models.log_entry import LogCategory


@pytest.fixture(autouse=True)
def reset_logging_state() -> Iterable[None]:
    shutdown_all_loggers()
    reset_structlog_configuration()
    yield
    shutdown_all_loggers()
    reset_structlog_configuration()


@pytest.fixture
def instrumentation(monkeypatch: pytest.MonkeyPatch) -> tuple[list[list[dict]], list[list[dict]]]:
    file_batches: list[list[dict]] = []
    console_batches: list[list[dict]] = []

    def fake_file_writer(self, batch: Iterable[dict]) -> None:  # type: ignore[override]
        file_batches.append(list(batch))

    def fake_console_writer(self, batch: Iterable[dict]) -> None:  # type: ignore[override]
        console_batches.append(list(batch))

    monkeypatch.setattr(file_module.FileLogHandler, "write_batch", fake_file_writer, raising=False)
    monkeypatch.setattr(
        logger_module.ConsoleLogHandler, "write_batch", fake_console_writer, raising=False
    )

    return file_batches, console_batches


@pytest.fixture
def logger_factory(tmp_path: Path) -> Callable[[str], StructuredLogger]:
    def _create(name: str) -> StructuredLogger:
        log_path = tmp_path / f"{name}.log"
        config = LogConfig(  # type: ignore[call-arg]
            output_file=str(log_path),
            log_level=LogLevel.DEBUG,
            async_flush_interval=0.2,
            batch_size=25,
            fallback_to_console=True,
        )
        logger = get_logger(name, config=config)
        return logger

    return _create


def _log_many(logger: StructuredLogger, *, total: int, category: LogCategory) -> None:
    for index in range(total):
        logger.info("performance test", category=category, entry=index)


def test_log_overhead_under_5ms(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    logger = logger_factory("overhead")
    file_batches, console_batches = instrumentation

    iterations = 200
    start = time.perf_counter()
    _log_many(logger, total=iterations, category=LogCategory.PERFORMANCE)
    elapsed = time.perf_counter() - start

    avg_ms = (elapsed / iterations) * 1000
    logger.flush()
    logger.shutdown()

    assert avg_ms < 5.0
    assert console_batches == []
    assert sum(len(batch) for batch in file_batches) == iterations


def test_async_logging_throughput(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    logger = logger_factory("throughput")
    file_batches, _ = instrumentation

    iterations = 1_000
    start = time.perf_counter()
    _log_many(logger, total=iterations, category=LogCategory.OPERATION)
    total_time = time.perf_counter() - start
    logger.flush()
    logger.shutdown()

    assert total_time < 1.0
    assert sum(len(batch) for batch in file_batches) == iterations


def test_batching_reduces_syscalls(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    logger = logger_factory("batching")
    file_batches, console_batches = instrumentation

    iterations = 125
    _log_many(logger, total=iterations, category=LogCategory.SECURITY)
    logger.flush()
    logger.shutdown()

    expected_max_calls = (iterations // 25) + 1
    assert len(file_batches) <= expected_max_calls
    assert console_batches == []


def test_performance_with_large_context_data(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    logger = logger_factory("large-context")
    file_batches, console_batches = instrumentation

    context_payload = {f"key_{i}": i for i in range(200)}

    iterations = 100
    start = time.perf_counter()
    for index in range(iterations):
        logger.info(
            "performance with context",
            category=LogCategory.OPERATION,
            context=context_payload,
            sequence=index,
        )
    elapsed = time.perf_counter() - start
    logger.flush()
    logger.shutdown()

    avg_ms = (elapsed / iterations) * 1000
    assert avg_ms < 8.0
    assert console_batches == []
    assert sum(len(batch) for batch in file_batches) == iterations


# T032: Integration tests for performance logging with timing helpers


def test_performance_logs_include_duration(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    """Test that logs generated with timing helpers include duration_ms field."""
    from src.logging.logger import log_duration

    logger = logger_factory("duration-test")
    file_batches, _ = instrumentation

    with log_duration(logger, "test_operation", user_id=123):
        time.sleep(0.1)

    logger.flush()
    logger.shutdown()

    assert len(file_batches) > 0
    all_logs = [log for batch in file_batches for log in batch]
    assert len(all_logs) == 1

    log_entry = all_logs[0]
    assert "duration_ms" in log_entry
    assert log_entry["duration_ms"] >= 100  # At least 100ms due to sleep
    assert log_entry["category"] == LogCategory.PERFORMANCE.value
    assert log_entry["operation_result"] == "success"
    assert log_entry["user_id"] == 123


def test_decorator_captures_operation_timing(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    """Test that @log_timing decorator captures operation timing correctly."""
    from src.logging.logger import log_timing

    file_batches, _ = instrumentation

    @log_timing(logger_name="decorator-test")
    def slow_operation() -> str:
        time.sleep(0.05)
        return "completed"

    # Create logger to ensure config is set
    logger_factory("decorator-test")

    result = slow_operation()

    # Get logger and flush
    logger = get_logger("decorator-test")
    logger.flush()
    logger.shutdown()

    assert result == "completed"

    all_logs = [log for batch in file_batches for log in batch]
    assert len(all_logs) == 1

    log_entry = all_logs[0]
    assert "duration_ms" in log_entry
    assert log_entry["duration_ms"] >= 50  # At least 50ms due to sleep
    assert log_entry["category"] == LogCategory.PERFORMANCE.value
    assert log_entry["operation_result"] == "success"
    assert "slow_operation" in log_entry["event"]


def test_context_manager_captures_timing(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    """Test that context manager captures timing for operations."""
    from src.logging.logger import log_duration

    logger = logger_factory("context-test")
    file_batches, _ = instrumentation

    with log_duration(logger, "database_query", level="debug", query_id=456):
        time.sleep(0.02)

    logger.flush()
    logger.shutdown()

    all_logs = [log for batch in file_batches for log in batch]
    assert len(all_logs) == 1

    log_entry = all_logs[0]
    assert "duration_ms" in log_entry
    assert log_entry["duration_ms"] >= 20
    assert log_entry["level"] == "DEBUG"
    assert log_entry["category"] == LogCategory.PERFORMANCE.value
    assert log_entry["query_id"] == 456


@pytest.mark.asyncio
async def test_async_operations_dont_block_logging(
    logger_factory: Callable[[str], StructuredLogger],
    instrumentation: tuple[list[list[dict]], list[list[dict]]],
) -> None:
    """Test that async operations with timing don't block the logging system."""
    import asyncio

    from src.logging.logger import log_timing

    file_batches, _ = instrumentation

    @log_timing(logger_name="async-test", level="info")
    async def async_operation() -> str:
        await asyncio.sleep(0.03)
        return "async_completed"

    # Create logger to ensure config is set
    logger_factory("async-test")

    # Run multiple async operations concurrently
    start = time.perf_counter()
    results = await asyncio.gather(
        async_operation(),
        async_operation(),
        async_operation(),
    )
    elapsed = time.perf_counter() - start

    # Get logger and flush
    logger = get_logger("async-test")
    logger.flush()
    logger.shutdown()

    # All operations should complete
    assert results == ["async_completed", "async_completed", "async_completed"]

    # Should take ~30ms (concurrent), not 90ms (sequential)
    assert elapsed < 0.06

    # Should have logged all 3 operations
    all_logs = [log for batch in file_batches for log in batch]
    assert len(all_logs) == 3

    for log_entry in all_logs:
        assert "duration_ms" in log_entry
        assert log_entry["category"] == LogCategory.PERFORMANCE.value
        assert log_entry["operation_result"] == "success"
