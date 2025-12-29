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

import json
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
def logger_factory(tmp_path: Path) -> Callable[[str], tuple[StructuredLogger, Path]]:
    def _create(name: str) -> tuple[StructuredLogger, Path]:
        log_path = tmp_path / f"{name}.log"
        config = LogConfig(  # type: ignore[call-arg]
            output_file=str(log_path),
            log_level=LogLevel.DEBUG,
            fallback_to_console=True,
        )
        logger = get_logger(name, config=config)
        return logger, log_path

    return _create


def test_file_failure_falls_back_to_console(
    logger_factory: Callable[[str], tuple[StructuredLogger, Path]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_console: list[dict] = []

    def capture_console(self, batch: Iterable[dict]) -> None:  # type: ignore[override]
        captured_console.extend(list(batch))

    def failing_file(self, batch: Iterable[dict]) -> None:  # type: ignore[override]
        raise OSError("disk full")

    monkeypatch.setattr(
        logger_module.ConsoleLogHandler, "write_batch", capture_console, raising=False
    )
    monkeypatch.setattr(file_module.FileLogHandler, "write_batch", failing_file, raising=False)

    logger, log_path = logger_factory("file-fallback")

    logger.info("file failure", category=LogCategory.OPERATION)
    logger.flush()
    logger.shutdown()

    if log_path.exists():
        assert log_path.read_text(encoding="utf-8") == ""
    assert len(captured_console) == 1
    assert captured_console[0]["event"] == "file failure"
    assert captured_console[0]["category"] == LogCategory.OPERATION.value


def test_logs_written_to_all_available_destinations(
    logger_factory: Callable[[str], tuple[StructuredLogger, Path]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_console: list[dict] = []

    def capture_console(self, batch: Iterable[dict]) -> None:  # type: ignore[override]
        captured_console.extend(list(batch))

    original_file_write = file_module.FileLogHandler.write_batch
    call_count = {"value": 0}

    def record_and_optionally_fail(self, batch: Iterable[dict]) -> None:  # type: ignore[override]
        entries = list(batch)
        call_count["value"] += 1
        if call_count["value"] == 2:
            raise OSError("read-only filesystem")
        original_file_write(self, entries)

    monkeypatch.setattr(
        logger_module.ConsoleLogHandler, "write_batch", capture_console, raising=False
    )
    monkeypatch.setattr(
        file_module.FileLogHandler, "write_batch", record_and_optionally_fail, raising=False
    )

    logger, log_path = logger_factory("multi-destination")

    logger.info("first success", category=LogCategory.OPERATION)
    logger.flush()
    logger.info("second fallback", category=LogCategory.ERROR)
    logger.flush()
    logger.shutdown()

    file_contents = log_path.read_text(encoding="utf-8")
    file_entries = [json.loads(line) for line in file_contents.splitlines() if line]

    assert any(entry["event"] == "first success" for entry in file_entries)
    assert captured_console and captured_console[0]["event"] == "second fallback"
    assert captured_console[0]["category"] == LogCategory.ERROR.value


def test_destination_failure_doesnt_block_operations(
    logger_factory: Callable[[str], tuple[StructuredLogger, Path]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_file(self, batch: Iterable[dict]) -> None:  # type: ignore[override]
        raise OSError("io error")

    monkeypatch.setattr(file_module.FileLogHandler, "write_batch", failing_file, raising=False)

    logger, _ = logger_factory("non-blocking")

    start = time.perf_counter()
    logger.info("fast log", category=LogCategory.OPERATION)
    duration = time.perf_counter() - start
    logger.flush()
    logger.shutdown()

    assert duration < 0.5
