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
import re
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path

import pytest

from src.logging.correlation import reset_correlation_id, set_correlation_id
from src.logging.logger import configure_structlog, get_logger, reset_structlog_configuration
from src.models.log_config import LogConfig
from src.models.log_entry import LogCategory, LogLevel


class _InMemoryLogger:
    """Lightweight logger used to capture rendered log entries in tests."""

    def __init__(self, store: list[str]) -> None:
        self._store = store

    def _record(self, event: str, **kwargs) -> None:
        # structlog processors should finish with JSONRenderer so we capture the rendered string.
        self._store.append(event)

    def msg(self, event: str, **kwargs) -> None:
        self._record(event, **kwargs)

    def info(self, event: str, **kwargs) -> None:
        self._record(event, **kwargs)

    def warning(self, event: str, **kwargs) -> None:
        self._record(event, **kwargs)

    def error(self, event: str, **kwargs) -> None:
        self._record(event, **kwargs)

    def debug(self, event: str, **kwargs) -> None:
        self._record(event, **kwargs)


@pytest.fixture(autouse=True)
def _reset_structlog() -> Iterable[None]:
    reset_structlog_configuration()
    yield
    reset_structlog_configuration()


@pytest.fixture(autouse=True)
def _reset_correlation() -> Iterable[None]:
    reset_correlation_id()
    yield
    reset_correlation_id()


@pytest.fixture
def capture_factory() -> tuple[list[str], Callable[..., _InMemoryLogger]]:
    store: list[str] = []

    class Factory:
        def __call__(self, *args, **kwargs) -> _InMemoryLogger:
            return _InMemoryLogger(store)

    return store, Factory()


def _parse_entries(rendered: Iterable[str]) -> list[dict]:
    return [json.loads(item) for item in rendered]


def _configure_and_get_logger(
    factory: Callable[..., _InMemoryLogger],
    *,
    config: LogConfig,
):
    configure_structlog(logger_factory=factory)
    return get_logger("unit-test", config=config)


def _config_with_path(tmp_path: Path, **overrides) -> LogConfig:
    return LogConfig(output_file=str(tmp_path / "test.log"), **overrides)


def test_logger_supports_all_log_levels(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    store, factory = capture_factory
    logger = _configure_and_get_logger(
        factory,
        config=_config_with_path(tmp_path, log_level=LogLevel.DEBUG),
    )

    set_correlation_id("test-levels")
    logger.error("error happened", category=LogCategory.ERROR)
    logger.warning("warn happened", category=LogCategory.SECURITY)
    logger.info("info happened", category=LogCategory.OPERATION)
    logger.debug("debug happened", category=LogCategory.PERFORMANCE)

    events = _parse_entries(store)
    assert [event["level"] for event in events] == [
        LogLevel.ERROR.value,
        LogLevel.WARN.value,
        LogLevel.INFO.value,
        LogLevel.DEBUG.value,
    ]


def test_logger_supports_all_categories(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    store, factory = capture_factory
    logger = _configure_and_get_logger(
        factory,
        config=_config_with_path(tmp_path, log_level=LogLevel.DEBUG),
    )

    set_correlation_id("test-categories")
    for category in LogCategory:
        logger.info(f"category {category.value}", category=category)

    events = _parse_entries(store)
    assert {event["category"] for event in events} == {category.value for category in LogCategory}


def test_logger_includes_required_fields(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    store, factory = capture_factory
    logger = _configure_and_get_logger(factory, config=_config_with_path(tmp_path))

    set_correlation_id("cid-required")
    logger.info("hello world", category=LogCategory.OPERATION)

    event = _parse_entries(store)[0]
    assert event["schema_version"] == "1.0.0"
    assert event["event"] == "hello world"
    assert event["level"] == LogLevel.INFO.value
    assert event["category"] == LogCategory.OPERATION.value
    assert event["correlation_id"] == "cid-required"
    assert event["timestamp"].endswith("Z")


def test_logger_output_is_valid_json(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    store, factory = capture_factory
    logger = _configure_and_get_logger(factory, config=_config_with_path(tmp_path))

    set_correlation_id("cid-json")
    logger.error("boom", category=LogCategory.ERROR)

    for entry in store:
        assert json.loads(entry)["event"] == "boom"


def test_logger_filters_by_minimum_level(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    store, factory = capture_factory
    logger = _configure_and_get_logger(
        factory,
        config=_config_with_path(tmp_path, log_level=LogLevel.WARN),
    )

    set_correlation_id("cid-filter")
    logger.info("ignore", category=LogCategory.OPERATION)
    logger.error("include", category=LogCategory.ERROR)

    events = _parse_entries(store)
    assert len(events) == 1
    assert events[0]["event"] == "include"
    assert events[0]["level"] == LogLevel.ERROR.value


def test_logger_includes_timestamp_utc(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    store, factory = capture_factory
    logger = _configure_and_get_logger(factory, config=_config_with_path(tmp_path))

    set_correlation_id("cid-ts")
    logger.info("with timestamp", category=LogCategory.CONNECTION)

    event = _parse_entries(store)[0]
    timestamp = event["timestamp"]
    assert timestamp.endswith("Z")
    # Replace terminal Z with +00:00 to satisfy fromisoformat
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    # Basic sanity check: parsed datetime should be timezone-aware UTC
    assert parsed.tzinfo is not None
    assert re.match(r"^\d{4}-\d{2}-\d{2}T", timestamp)


# T039: Tests for configurable log levels (User Story 5)


def test_debug_level_shows_all_logs(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    """DEBUG level should show all log levels: DEBUG, INFO, WARN, ERROR."""
    store, factory = capture_factory
    logger = _configure_and_get_logger(
        factory,
        config=_config_with_path(tmp_path, log_level=LogLevel.DEBUG),
    )

    set_correlation_id("cid-debug-all")
    logger.debug("debug message", category=LogCategory.OPERATION)
    logger.info("info message", category=LogCategory.CONNECTION)
    logger.warn("warn message", category=LogCategory.ERROR)
    logger.error("error message", category=LogCategory.ERROR)

    events = _parse_entries(store)
    assert len(events) == 4
    messages = [e["event"] for e in events]
    assert "debug message" in messages
    assert "info message" in messages
    assert "warn message" in messages
    assert "error message" in messages


def test_info_level_suppresses_debug(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    """INFO level should show INFO, WARN, ERROR but suppress DEBUG."""
    store, factory = capture_factory
    logger = _configure_and_get_logger(
        factory,
        config=_config_with_path(tmp_path, log_level=LogLevel.INFO),
    )

    set_correlation_id("cid-info-filter")
    logger.debug("debug message", category=LogCategory.OPERATION)
    logger.info("info message", category=LogCategory.CONNECTION)
    logger.warn("warn message", category=LogCategory.ERROR)
    logger.error("error message", category=LogCategory.ERROR)

    events = _parse_entries(store)
    assert len(events) == 3
    messages = [e["event"] for e in events]
    assert "debug message" not in messages
    assert "info message" in messages
    assert "warn message" in messages
    assert "error message" in messages


def test_warn_level_suppresses_info_and_debug(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    """WARN level should show only WARN and ERROR, suppress INFO and DEBUG."""
    store, factory = capture_factory
    logger = _configure_and_get_logger(
        factory,
        config=_config_with_path(tmp_path, log_level=LogLevel.WARN),
    )

    set_correlation_id("cid-warn-filter")
    logger.debug("debug message", category=LogCategory.OPERATION)
    logger.info("info message", category=LogCategory.CONNECTION)
    logger.warn("warn message", category=LogCategory.ERROR)
    logger.error("error message", category=LogCategory.ERROR)

    events = _parse_entries(store)
    assert len(events) == 2
    messages = [e["event"] for e in events]
    assert "debug message" not in messages
    assert "info message" not in messages
    assert "warn message" in messages
    assert "error message" in messages


def test_error_level_shows_only_errors(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    """ERROR level should show only ERROR logs."""
    store, factory = capture_factory
    logger = _configure_and_get_logger(
        factory,
        config=_config_with_path(tmp_path, log_level=LogLevel.ERROR),
    )

    set_correlation_id("cid-error-only")
    logger.debug("debug message", category=LogCategory.OPERATION)
    logger.info("info message", category=LogCategory.CONNECTION)
    logger.warn("warn message", category=LogCategory.ERROR)
    logger.error("error message", category=LogCategory.ERROR)

    events = _parse_entries(store)
    assert len(events) == 1
    messages = [e["event"] for e in events]
    assert "debug message" not in messages
    assert "info message" not in messages
    assert "warn message" not in messages
    assert "error message" in messages


def test_log_level_configurable_at_runtime(
    capture_factory: tuple[list[str], Callable[..., _InMemoryLogger]],
    tmp_path: Path,
):
    """Log level should be changeable at runtime without recreating logger."""
    store, factory = capture_factory

    # Start with INFO level
    config = _config_with_path(tmp_path, log_level=LogLevel.INFO)
    logger = _configure_and_get_logger(factory, config=config)

    set_correlation_id("cid-runtime-1")
    logger.debug("debug 1", category=LogCategory.OPERATION)
    logger.info("info 1", category=LogCategory.CONNECTION)

    # Change to DEBUG level at runtime
    logger.set_log_level(LogLevel.DEBUG)

    set_correlation_id("cid-runtime-2")
    logger.debug("debug 2", category=LogCategory.OPERATION)
    logger.info("info 2", category=LogCategory.CONNECTION)

    events = _parse_entries(store)
    messages = [e["event"] for e in events]

    # First phase: debug 1 suppressed, info 1 logged
    assert "debug 1" not in messages
    assert "info 1" in messages

    # Second phase: both debug 2 and info 2 logged
    assert "debug 2" in messages
    assert "info 2" in messages
