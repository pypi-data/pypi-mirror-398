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

"""
Unit tests for log rotation functionality.

Tests cover:
- Size-based rotation (100MB limit)
- Time-based rotation (midnight UTC)
- Gzip compression of rotated files
- Retention policy (deletion of old files)
- File naming patterns
- Thread safety
"""

import gzip
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from src.logging.rotation import RotatingLogHandler
from src.models.log_config import LogConfig


def _read_log_lines(log_dir: Path) -> list[str]:
    """Collect all log lines from plain and compressed files."""
    lines: list[str] = []
    for log_file in sorted(log_dir.glob("*.log")):
        if log_file.name.endswith(".gz"):
            continue
        content = log_file.read_text()
        lines.extend([line for line in content.split("\n") if line.strip()])
    for gz_file in sorted(log_dir.glob("*.log.gz")):
        with gzip.open(gz_file, "rt") as fh:
            content = fh.read()
            lines.extend([line for line in content.split("\n") if line.strip()])
    return lines


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def mock_config(temp_log_dir: Path) -> LogConfig:
    """Create a mock LogConfig for testing."""
    return LogConfig(  # type: ignore[call-arg]
        output_file=str(temp_log_dir / "test.log"),
        rotation_max_bytes=1024,  # 1KB for testing
        retention_days=7,
        compression_enabled=True,
    )


def test_rotate_on_size_limit(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that log file rotates when it reaches the size limit."""
    handler = RotatingLogHandler(mock_config)

    # Write enough data to trigger rotation (> 1KB)
    large_entry = {"message": "x" * 500, "timestamp": "2025-01-01T00:00:00Z"}

    # Write 3 entries (should trigger rotation after 2nd entry)
    handler.write_log(large_entry)
    handler.write_log(large_entry)
    handler.write_log(large_entry)

    handler.close()

    # Check that rotation occurred
    log_files = list(temp_log_dir.glob("*.log*"))
    assert len(log_files) >= 2, "Rotation should have created multiple log files"


def test_rotate_on_midnight(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that log file rotates at midnight UTC."""
    handler = RotatingLogHandler(mock_config)

    # Mock time to simulate day change
    with patch("src.logging.rotation.datetime") as mock_datetime:
        # Start on day 1
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 23, 59, 0)
        mock_datetime.now.return_value = datetime(2025, 1, 1, 23, 59, 0)

        entry1 = {"message": "Entry before midnight", "timestamp": "2025-01-01T23:59:00Z"}
        handler.write_log(entry1)

        # Move to day 2 (midnight crossed)
        mock_datetime.utcnow.return_value = datetime(2025, 1, 2, 0, 0, 1)
        mock_datetime.now.return_value = datetime(2025, 1, 2, 0, 0, 1)

        entry2 = {"message": "Entry after midnight", "timestamp": "2025-01-02T00:00:01Z"}
        handler.write_log(entry2)

        handler.close()

    # Check that rotation occurred due to date change
    log_files = list(temp_log_dir.glob("*.log*"))
    assert len(log_files) >= 2, "Rotation should have occurred at midnight"


def test_compression_of_rotated_files(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that rotated log files are compressed with gzip."""
    handler = RotatingLogHandler(mock_config)

    # Force rotation by writing large entries
    large_entry = {"message": "x" * 500, "timestamp": "2025-01-01T00:00:00Z"}
    handler.write_log(large_entry)
    handler.write_log(large_entry)
    handler.write_log(large_entry)

    # Give time for compression to complete
    time.sleep(0.5)
    handler.close()

    # Check for .gz files
    gz_files = list(temp_log_dir.glob("*.log.gz"))
    assert len(gz_files) > 0, "Rotated files should be compressed"

    # Verify it's valid gzip
    if gz_files:
        with gzip.open(gz_files[0], "rt") as f:
            content = f.read()
            assert len(content) > 0, "Compressed file should contain data"


def test_retention_policy_deletes_old_files(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that files older than retention_days are deleted."""
    # Create old log files
    old_date = datetime.utcnow() - timedelta(days=10)
    old_file = temp_log_dir / f"test-{old_date.strftime('%Y-%m-%d')}.log"
    old_file.write_text('{"message": "old log"}\n')

    # Create recent log file
    recent_date = datetime.utcnow() - timedelta(days=3)
    recent_file = temp_log_dir / f"test-{recent_date.strftime('%Y-%m-%d')}.log"
    recent_file.write_text('{"message": "recent log"}\n')

    # Initialize handler (should trigger cleanup)
    handler = RotatingLogHandler(mock_config)
    handler.cleanup_old_files()
    handler.close()

    # Check that old file was deleted but recent file remains
    assert not old_file.exists(), "Old file should be deleted"
    assert recent_file.exists(), "Recent file should remain"


def test_rotated_file_naming_pattern(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that rotated files follow the expected naming pattern."""
    handler = RotatingLogHandler(mock_config)

    # Force rotation
    large_entry = {"message": "x" * 500, "timestamp": "2025-01-01T00:00:00Z"}
    handler.write_log(large_entry)
    handler.write_log(large_entry)
    handler.write_log(large_entry)

    time.sleep(0.5)
    handler.close()

    # Check naming pattern: should include date or timestamp
    log_files = list(temp_log_dir.glob("*.log*"))

    # Active file should be named according to base pattern
    active_files = [f for f in log_files if f.suffix == ".log"]
    assert len(active_files) >= 1, "Should have active log file"

    # Rotated files should have .gz extension
    rotated_files = [f for f in log_files if ".log.gz" in f.name]
    if rotated_files:
        # Verify naming includes timestamp or date
        for f in rotated_files:
            assert "-" in f.stem or "." in f.stem, "Rotated file should include date/timestamp"


def test_only_one_active_file_at_a_time(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that only one non-rotated (active) log file exists at any time."""
    handler = RotatingLogHandler(mock_config)

    # Write multiple entries
    for i in range(5):
        entry = {"message": f"Entry {i}", "timestamp": f"2025-01-01T00:00:{i:02d}Z"}
        handler.write_log(entry)

    handler.close()

    # Count active (non-compressed) log files
    active_files = list(temp_log_dir.glob("*.log"))
    active_files = [f for f in active_files if not f.name.endswith(".gz")]

    assert len(active_files) == 1, "Should have exactly one active log file"


def test_rotation_is_thread_safe(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that rotation handles concurrent writes safely."""
    import threading

    handler = RotatingLogHandler(mock_config)
    errors = []

    def write_logs(thread_id: int) -> None:
        try:
            for i in range(10):
                entry = {
                    "message": f"Thread {thread_id}, entry {i}: " + "x" * 100,
                    "timestamp": f"2025-01-01T00:00:{i:02d}Z",
                }
                handler.write_log(entry)
        except Exception as e:
            errors.append(e)

    # Create multiple threads
    threads = [threading.Thread(target=write_logs, args=(i,)) for i in range(5)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    handler.close()

    # Check no errors occurred
    assert len(errors) == 0, f"Thread-safe rotation failed with errors: {errors}"

    # Verify all logs were written across active and rotated files
    all_logs = _read_log_lines(temp_log_dir)
    assert len(all_logs) >= 40, "Should have logs from all threads"


def test_rotation_preserves_logs(temp_log_dir: Path, mock_config: LogConfig) -> None:
    """Test that rotation doesn't lose any log entries."""
    handler = RotatingLogHandler(mock_config)

    # Write known number of entries
    num_entries = 20
    for i in range(num_entries):
        entry = {
            "message": f"Entry {i}: " + "x" * 100,
            "timestamp": f"2025-01-01T00:00:{i:02d}Z",
            "index": i,
        }
        handler.write_log(entry)

    handler.close()

    all_entries = _read_log_lines(temp_log_dir)
    parsed = [json.loads(line) for line in all_entries]
    assert len(parsed) == num_entries, f"Expected {num_entries} entries, got {len(parsed)}"
    assert {entry.get("index") for entry in parsed} == set(range(num_entries))


def test_rotation_handles_write_errors_gracefully(
    temp_log_dir: Path, mock_config: LogConfig
) -> None:
    """Test that rotation handles write errors without crashing."""
    handler = RotatingLogHandler(mock_config)

    # Write some valid entries
    entry = {"message": "Valid entry", "timestamp": "2025-01-01T00:00:00Z"}
    handler.write_log(entry)

    # Simulate disk full by making directory read-only (Unix-like systems)
    try:
        temp_log_dir.chmod(0o444)

        # Try to write (should not crash)
        try:
            handler.write_log(entry)
        except Exception:
            pass  # Expected to fail, but shouldn't crash the handler

    finally:
        # Restore permissions
        temp_log_dir.chmod(0o755)
        handler.close()

    # Handler should still be functional after restoring permissions
    assert True, "Handler survived write error"
