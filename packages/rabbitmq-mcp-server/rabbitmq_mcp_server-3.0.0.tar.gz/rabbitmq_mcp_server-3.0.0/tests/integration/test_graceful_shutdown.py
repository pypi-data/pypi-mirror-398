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

"""
Integration tests for graceful shutdown with zero log loss.

Tests validate that system flushes all buffered logs during shutdown,
preventing log loss even when shutdown is triggered by signals (SIGTERM, SIGINT).
"""

import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from src.logging.logger import get_logger, shutdown_all_loggers
from src.models.log_config import LogConfig
from src.models.log_entry import LogCategory


def test_flush_completes_before_shutdown(tmp_path: Path) -> None:
    """
    Test that all buffered logs are written before shutdown completes.

    Validates FR-028: System must flush all buffered logs during graceful shutdown.
    """
    log_file = tmp_path / "test.log"

    config = LogConfig(
        output_file=str(log_file),
        async_queue_size=1000,
        batch_size=50,
        async_flush_interval=10.0,  # Long interval to ensure buffering
    )

    logger = get_logger("test-flush", config=config)

    # Write many logs quickly to fill buffer
    num_logs = 200
    for i in range(num_logs):
        logger.info(
            f"Test log {i}",
            category=LogCategory.OPERATION,
            sequence=i,
        )

    # Shutdown should flush all logs
    shutdown_all_loggers()

    # Verify all logs were written
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")

    # Should have all 200 logs
    assert len(lines) == num_logs, (
        f"Expected {num_logs} logs, got {len(lines)}. " f"Log loss detected during shutdown!"
    )


def test_shutdown_timeout_prevents_hang(tmp_path: Path) -> None:
    """
    Test that shutdown times out after 30 seconds to prevent indefinite hang.

    Validates that even if flush takes too long, shutdown completes within
    reasonable timeout.
    """
    log_file = tmp_path / "test.log"

    config = LogConfig(
        output_file=str(log_file),
        async_queue_size=100,
    )

    logger = get_logger("test-timeout", config=config)
    logger.info("Test log", category=LogCategory.OPERATION)

    # Measure shutdown time
    start = time.time()
    shutdown_all_loggers()
    elapsed = time.time() - start

    # Should complete quickly (< 5 seconds for normal case)
    assert elapsed < 5.0, f"Shutdown took {elapsed:.2f}s, expected < 5s for small queue"


def test_atexit_handler_flushes_logs_on_normal_exit(tmp_path: Path) -> None:
    """
    Test that atexit handler flushes logs on normal program exit.

    Validates that logs are not lost even if user doesn't call shutdown manually.
    """
    log_file = tmp_path / "test.log"

    # Create Python script that logs and exits normally
    script = tmp_path / "test_script.py"
    script.write_text(
        f"""
import sys
sys.path.insert(0, '{Path.cwd()}')

from src.logging.logger import get_logger
from src.models.log_config import LogConfig
from src.models.log_entry import LogCategory

config = LogConfig(output_file='{log_file}')
logger = get_logger('test-atexit', config=config)

for i in range(10):
    logger.info(f'Test log {{i}}', category=LogCategory.OPERATION)

# Exit without calling shutdown - atexit should handle it
"""
    )

    # Run script
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify logs were written by atexit handler
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 10, f"Expected 10 logs via atexit, got {len(lines)}"


@pytest.mark.skipif(sys.platform == "win32", reason="SIGTERM not available on Windows")
def test_sigterm_triggers_graceful_shutdown(tmp_path: Path) -> None:
    """
    Test that SIGTERM signal triggers graceful shutdown with log flush.

    Validates that system handles SIGTERM (e.g., from Docker/systemd) gracefully.
    """
    log_file = tmp_path / "test.log"

    # Create Python script that logs continuously and handles SIGTERM
    script = tmp_path / "test_script.py"
    script.write_text(
        f"""
import sys
import time
sys.path.insert(0, '{Path.cwd()}')

from src.logging.logger import get_logger
from src.models.log_config import LogConfig
from src.models.log_entry import LogCategory

config = LogConfig(output_file='{log_file}')
logger = get_logger('test-sigterm', config=config)

# Write some logs
for i in range(20):
    logger.info(f'Test log {{i}}', category=LogCategory.OPERATION)

# Simulate some work
time.sleep(0.5)

# Write more logs
for i in range(20, 40):
    logger.info(f'Test log {{i}}', category=LogCategory.OPERATION)

# Wait for SIGTERM (script will be killed by test)
time.sleep(10)
"""
    )

    # Start script
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Let it write some logs
    time.sleep(1.0)

    # Send SIGTERM
    proc.send_signal(signal.SIGTERM)

    # Wait for graceful shutdown
    try:
        proc.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail("Process didn't shutdown gracefully within 5 seconds")

    # Verify logs were flushed before exit
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")

    # Should have at least first batch of 20 logs
    assert len(lines) >= 20, f"Expected >= 20 logs after SIGTERM, got {len(lines)}"


@pytest.mark.skipif(sys.platform == "win32", reason="SIGINT handling differs on Windows")
def test_sigint_triggers_graceful_shutdown(tmp_path: Path) -> None:
    """
    Test that SIGINT (Ctrl+C) triggers graceful shutdown with log flush.

    Validates that Ctrl+C in terminal doesn't lose logs.
    """
    log_file = tmp_path / "test.log"

    # Create Python script that logs and waits for SIGINT
    script = tmp_path / "test_script.py"
    script.write_text(
        f"""
import sys
import time
sys.path.insert(0, '{Path.cwd()}')

from src.logging.logger import get_logger
from src.models.log_config import LogConfig
from src.models.log_entry import LogCategory

config = LogConfig(output_file='{log_file}')
logger = get_logger('test-sigint', config=config)

# Write logs
for i in range(15):
    logger.info(f'Test log {{i}}', category=LogCategory.OPERATION)

# Wait for SIGINT
time.sleep(10)
"""
    )

    # Start script
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Let it write logs
    time.sleep(1.0)

    # Send SIGINT (Ctrl+C)
    proc.send_signal(signal.SIGINT)

    # Wait for graceful shutdown
    try:
        proc.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail("Process didn't shutdown gracefully within 5 seconds")

    # Verify logs were flushed
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 15, f"Expected 15 logs after SIGINT, got {len(lines)}"


def test_multiple_loggers_all_flushed_on_shutdown(tmp_path: Path) -> None:
    """
    Test that shutdown flushes all registered loggers, not just one.

    Validates that system tracks all active loggers and flushes them all.
    """
    log_file_1 = tmp_path / "logger1.log"
    log_file_2 = tmp_path / "logger2.log"

    config1 = LogConfig(output_file=str(log_file_1))
    config2 = LogConfig(output_file=str(log_file_2))

    logger1 = get_logger("logger1", config=config1)
    logger2 = get_logger("logger2", config=config2)

    # Write logs to both
    for i in range(10):
        logger1.info(f"Logger1 log {i}", category=LogCategory.OPERATION)
        logger2.info(f"Logger2 log {i}", category=LogCategory.OPERATION)

    # Shutdown should flush both
    shutdown_all_loggers()

    # Verify both files have all logs
    assert log_file_1.exists()
    assert log_file_2.exists()

    lines1 = log_file_1.read_text().strip().split("\n")
    lines2 = log_file_2.read_text().strip().split("\n")

    assert len(lines1) == 10, f"Logger1 missing logs: {len(lines1)}/10"
    assert len(lines2) == 10, f"Logger2 missing logs: {len(lines2)}/10"


def test_zero_log_loss_under_rapid_shutdown(tmp_path: Path) -> None:
    """
    Test zero log loss when shutdown occurs immediately after logging.

    Validates worst-case scenario: logs written, immediate shutdown.
    """
    log_file = tmp_path / "test.log"

    config = LogConfig(
        output_file=str(log_file),
        async_queue_size=500,
        batch_size=100,
        async_flush_interval=10.0,  # Long interval
    )

    logger = get_logger("test-rapid", config=config)

    # Rapid fire logs
    num_logs = 100
    for i in range(num_logs):
        logger.info(f"Rapid log {i}", category=LogCategory.OPERATION, index=i)

    # Immediate shutdown (worst case)
    shutdown_all_loggers()

    # Verify zero log loss
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")

    assert len(lines) == num_logs, f"Log loss detected! Expected {num_logs}, got {len(lines)}"
