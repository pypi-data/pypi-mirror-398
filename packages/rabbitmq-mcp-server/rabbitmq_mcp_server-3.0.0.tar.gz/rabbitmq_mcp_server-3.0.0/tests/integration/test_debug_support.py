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

"""Integration tests for User Story 5 - Debug Support (T042 checkpoint validation)."""

import json
import os
import signal
import sys
import time
from pathlib import Path

import pytest
import yaml

from src.logging.config import start_config_watcher, stop_config_watcher
from src.logging.correlation import set_correlation_id
from src.logging.logger import get_logger, reset_structlog_configuration
from src.models.log_config import LogConfig, LogLevel
from src.models.log_entry import LogCategory


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    reset_structlog_configuration()
    stop_config_watcher()


def test_debug_level_shows_internal_details(tmp_path: Path):
    """
    US5 Acceptance: DEBUG level shows detailed internal logs.

    Validates that when DEBUG level is configured, all log levels
    (DEBUG, INFO, WARN, ERROR) are captured.
    """
    log_file = tmp_path / "debug.log"
    config = LogConfig(
        log_level=LogLevel.DEBUG,
        output_file=str(log_file),
        async_queue_size=100,
        batch_size=1,
    )

    logger = get_logger("test-debug", config=config)
    set_correlation_id("us5-debug-test")

    # Log at all levels
    logger.debug(
        "Debug message with internal details",
        category=LogCategory.OPERATION,
        internal_state="active",
    )
    logger.info("Info message", category=LogCategory.CONNECTION)
    logger.warn("Warning message", category=LogCategory.ERROR)
    logger.error("Error message", category=LogCategory.ERROR)

    # Flush and shutdown
    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Verify all logs captured
    with open(log_file) as f:
        lines = f.readlines()

    assert len(lines) == 4
    events = [json.loads(line)["event"] for line in lines]
    assert "Debug message with internal details" in events
    assert "Info message" in events
    assert "Warning message" in events
    assert "Error message" in events

    # Verify debug log includes extra details
    debug_log = json.loads(lines[0])
    assert debug_log["level"] == "DEBUG"
    assert debug_log["internal_state"] == "active"


def test_info_level_suppresses_debug_logs(tmp_path: Path):
    """
    US5 Acceptance: INFO level suppresses debug logs.

    Validates that when INFO level is configured, DEBUG logs
    are filtered out but INFO/WARN/ERROR are captured.
    """
    log_file = tmp_path / "info.log"
    config = LogConfig(
        log_level=LogLevel.INFO,
        output_file=str(log_file),
        async_queue_size=100,
        batch_size=1,
    )

    logger = get_logger("test-info", config=config)
    set_correlation_id("us5-info-test")

    # Log at all levels
    logger.debug("Debug message (should be suppressed)", category=LogCategory.OPERATION)
    logger.info("Info message", category=LogCategory.CONNECTION)
    logger.warn("Warning message", category=LogCategory.ERROR)
    logger.error("Error message", category=LogCategory.ERROR)

    # Flush and shutdown
    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Verify only INFO/WARN/ERROR captured
    with open(log_file) as f:
        lines = f.readlines()

    assert len(lines) == 3
    events = [json.loads(line)["event"] for line in lines]
    assert "Debug message (should be suppressed)" not in events
    assert "Info message" in events
    assert "Warning message" in events
    assert "Error message" in events


def test_log_level_changed_at_runtime_without_restart(tmp_path: Path):
    """
    US5 Acceptance: Log level can be changed without restart.

    Validates that log level can be changed at runtime via
    set_log_level() and the change takes effect immediately.
    """
    log_file = tmp_path / "runtime.log"
    config = LogConfig(
        log_level=LogLevel.INFO,
        output_file=str(log_file),
        async_queue_size=100,
        batch_size=1,
    )

    logger = get_logger("test-runtime", config=config)

    # Phase 1: INFO level (debug suppressed)
    set_correlation_id("us5-runtime-phase1")
    logger.debug("Debug 1 (suppressed)", category=LogCategory.OPERATION)
    logger.info("Info 1", category=LogCategory.CONNECTION)

    # Change to DEBUG level at runtime
    logger.set_log_level(LogLevel.DEBUG)

    # Phase 2: DEBUG level (debug visible)
    set_correlation_id("us5-runtime-phase2")
    logger.debug("Debug 2 (visible)", category=LogCategory.OPERATION)
    logger.info("Info 2", category=LogCategory.CONNECTION)

    # Flush and shutdown
    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Verify behavior changed at runtime
    with open(log_file) as f:
        lines = f.readlines()

    events = [json.loads(line)["event"] for line in lines]

    # Phase 1: only info logged
    assert "Debug 1 (suppressed)" not in events
    assert "Info 1" in events

    # Phase 2: both debug and info logged
    assert "Debug 2 (visible)" in events
    assert "Info 2" in events


@pytest.mark.skipif(sys.platform == "win32", reason="Signal handling not supported on Windows")
def test_config_reload_via_signal_unix(tmp_path: Path):
    """
    US5 Acceptance: Config can be reloaded via signal without restart (Unix).

    Validates that sending SIGHUP signal reloads configuration
    and applies new log level immediately.
    """
    log_file = tmp_path / "signal.log"
    config_file = tmp_path / "logging_config.yaml"

    # Create initial config (INFO level)
    config_data = {
        "logging": {
            "log_level": "INFO",
            "output_file": str(log_file),
            "async_queue_size": 100,
            "batch_size": 1,
        }
    }
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = LogConfig(**config_data["logging"])
    logger = get_logger("test-signal", config=config)

    # Setup config watcher with signal handlers
    def on_reload(new_config: LogConfig):
        logger.set_log_level(new_config.log_level)

    start_config_watcher(
        config_path=config_file,
        on_reload=on_reload,
    )

    try:
        # Phase 1: INFO level
        set_correlation_id("us5-signal-phase1")
        logger.debug("Debug 1 (suppressed)", category=LogCategory.OPERATION)
        logger.info("Info 1", category=LogCategory.CONNECTION)

        # Update config file to DEBUG level
        config_data["logging"]["log_level"] = "DEBUG"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Send SIGHUP to trigger reload
        os.kill(os.getpid(), signal.SIGHUP)
        time.sleep(0.2)  # Give signal handler time to execute

        # Phase 2: DEBUG level (after reload)
        set_correlation_id("us5-signal-phase2")
        logger.debug("Debug 2 (visible)", category=LogCategory.OPERATION)
        logger.info("Info 2", category=LogCategory.CONNECTION)

        # Flush and shutdown
        logger.flush()
        logger.shutdown()
        time.sleep(0.1)

        # Verify reload worked
        with open(log_file) as f:
            lines = f.readlines()

        events = [json.loads(line)["event"] for line in lines]

        assert "Debug 1 (suppressed)" not in events
        assert "Info 1" in events
        assert "Debug 2 (visible)" in events
        assert "Info 2" in events

    finally:
        stop_config_watcher()


@pytest.mark.skipif(sys.platform != "win32", reason="File watcher only on Windows")
def test_config_reload_via_file_watcher_windows(tmp_path: Path):
    """
    US5 Acceptance: Config reloaded via file watcher on Windows.

    Validates that file modification triggers config reload
    and applies new log level immediately on Windows.
    """
    log_file = tmp_path / "watcher.log"
    config_file = tmp_path / "logging_config.yaml"

    # Create initial config (INFO level)
    config_data = {
        "logging": {
            "log_level": "INFO",
            "output_file": str(log_file),
            "async_queue_size": 100,
            "batch_size": 1,
        }
    }
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = LogConfig(**config_data["logging"])
    logger = get_logger("test-watcher", config=config)

    # Setup config watcher with file polling
    def on_reload(new_config: LogConfig):
        logger.set_log_level(new_config.log_level)

    start_config_watcher(
        config_path=config_file,
        on_reload=on_reload,
        poll_interval=0.5,  # Fast polling for test
    )

    try:
        # Phase 1: INFO level
        set_correlation_id("us5-watcher-phase1")
        logger.debug("Debug 1 (suppressed)", category=LogCategory.OPERATION)
        logger.info("Info 1", category=LogCategory.CONNECTION)

        # Update config file to DEBUG level
        time.sleep(0.1)  # Ensure file mtime changes
        config_data["logging"]["log_level"] = "DEBUG"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Wait for file watcher to detect change
        time.sleep(1.0)

        # Phase 2: DEBUG level (after reload)
        set_correlation_id("us5-watcher-phase2")
        logger.debug("Debug 2 (visible)", category=LogCategory.OPERATION)
        logger.info("Info 2", category=LogCategory.CONNECTION)

        # Flush and shutdown
        logger.flush()
        logger.shutdown()
        time.sleep(0.1)

        # Verify reload worked
        with open(log_file) as f:
            lines = f.readlines()

        events = [json.loads(line)["event"] for line in lines]

        assert "Debug 1 (suppressed)" not in events
        assert "Info 1" in events
        assert "Debug 2 (visible)" in events
        assert "Info 2" in events

    finally:
        stop_config_watcher()


def test_performance_not_degraded_with_debug_disabled(tmp_path: Path):
    """
    US5 Acceptance: Performance not degraded with DEBUG disabled.

    Validates that filtering debug logs before processing maintains
    low overhead when debug logging is disabled.
    """
    log_file = tmp_path / "perf.log"
    config = LogConfig(
        log_level=LogLevel.INFO,  # DEBUG disabled
        output_file=str(log_file),
        async_queue_size=100,
        batch_size=10,
    )

    logger = get_logger("test-perf", config=config)
    set_correlation_id("us5-perf-test")

    # Measure overhead of suppressed debug logs
    import time as time_module

    start = time_module.perf_counter()

    for i in range(100):
        logger.debug(f"Debug {i} (suppressed)", category=LogCategory.OPERATION)

    overhead_ms = (time_module.perf_counter() - start) * 1000

    # Flush and shutdown
    logger.flush()
    logger.shutdown()
    time.sleep(0.1)

    # Verify no logs written (all suppressed)
    with open(log_file) as f:
        lines = f.readlines()

    assert len(lines) == 0

    # Verify overhead is minimal (<1ms per suppressed log)
    # Note: This is very fast because filtering happens before JSON serialization
    assert overhead_ms < 100  # 100ms for 100 logs = <1ms each
