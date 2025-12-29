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
Log rotation implementation.

Provides automatic log rotation based on:
- File size (100MB default)
- Time (midnight UTC)
- Compression of rotated files (gzip)
- Retention policy (30 days default)
"""

import gzip
import os
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import orjson

from models.log_config import LogConfig

__all__ = ["RotatingLogHandler"]


class RotatingLogHandler:
    """
    Handler for automatic log file rotation.

    Features:
    - Size-based rotation (default 100MB)
    - Time-based rotation (midnight UTC)
    - Gzip compression of rotated files
    - Retention policy (default 30 days)
    - Thread-safe operations
    """

    def __init__(self, config: LogConfig) -> None:
        """
        Initialize the rotating log handler.

        Args:
            config: LogConfig with rotation settings
        """
        self.config = config
        self.base_path = Path(config.output_file)
        self.max_bytes = config.rotation_max_bytes
        self.retention_days = config.retention_days
        self.compression_enabled = config.compression_enabled

        # Thread safety
        self._lock = threading.Lock()
        self._file = None
        self._current_date = None
        self._current_size = 0

        # Ensure directory exists
        self.base_path.parent.mkdir(parents=True, exist_ok=True)

        # Open initial file
        self._open_file()

        # Cleanup old files
        self.cleanup_old_files()

    def write_log(self, entry: dict[str, Any]) -> None:
        """
        Write a log entry, rotating if necessary.

        Args:
            entry: Log entry dictionary
        """
        with self._lock:
            if self._should_rotate():
                self._rotate()

            # Serialize and write
            try:
                json_bytes = orjson.dumps(entry)
                if self._file is None:
                    self._open_file()
                if self._file is None:
                    return
                self._file.write(json_bytes)
                self._file.write(b"\n")
                self._file.flush()

                # Update size tracking
                self._current_size += len(json_bytes) + 1

            except Exception as e:
                # Log write error to stderr but don't crash
                import sys

                sys.stderr.write(f"ERROR: Failed to write log: {e}\n")

    def _should_rotate(self) -> bool:
        """Check if rotation is needed based on size or date."""
        if self._current_size >= self.max_bytes:
            return True

        today = datetime.utcnow().date()
        if self._current_date is None:
            self._current_date = today
            return False

        if today > self._current_date:
            return True

        self._current_date = today
        return False

    def _rotate(self) -> None:
        """Perform log rotation."""
        # Close current file
        if self._file:
            self._file.close()

        # Generate rotated filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H%M%S-%f")
        rotated_name = f"{self.base_path.stem}-{timestamp}{self.base_path.suffix}"
        rotated_path = self.base_path.parent / rotated_name

        # Rename current file to rotated name
        if self.base_path.exists():
            try:
                self.base_path.rename(rotated_path)

                # Compress if enabled
                if self.compression_enabled:
                    self._compress_file(rotated_path)

            except Exception as e:
                import sys

                sys.stderr.write(f"ERROR: Failed to rotate log file: {e}\n")

        # Open new file
        self._open_file()
        self._current_size = 0
        try:
            self._current_date = datetime.utcnow().date()
        except Exception:
            pass

        # Cleanup old files
        self.cleanup_old_files()

    def _compress_file(self, file_path: Path) -> None:
        """
        Compress a log file with gzip.

        Args:
            file_path: Path to file to compress
        """
        gz_path = Path(str(file_path) + ".gz")

        try:
            with open(file_path, "rb") as f_in:
                with gzip.open(gz_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            file_path.unlink()

        except Exception as e:
            import sys

            sys.stderr.write(f"ERROR: Failed to compress log file {file_path}: {e}\n")

    def _open_file(self) -> None:
        """Open a new log file."""
        try:
            self._file = open(self.base_path, "ab")
            self._current_date = datetime.utcnow().date()

            # Get current file size
            try:
                self._current_size = self.base_path.stat().st_size
            except FileNotFoundError:
                self._current_size = 0

        except Exception as e:
            import sys

            sys.stderr.write(f"ERROR: Failed to open log file {self.base_path}: {e}\n")
            # Create a dummy file object that ignores writes
            import io

            self._file = io.BytesIO()

    def cleanup_old_files(self) -> None:
        """Delete log files older than retention_days."""
        if self.retention_days <= 0:
            return
        cutoff_threshold = (datetime.utcnow() - timedelta(days=self.retention_days)).date()

        # Find all log files in directory
        log_dir = self.base_path.parent
        pattern = f"{self.base_path.stem}-*{self.base_path.suffix}*"

        for log_file in log_dir.glob(pattern):
            try:
                # Skip the active file
                if log_file == self.base_path:
                    continue

                deletion_due = False

                # Attempt to parse date from filename (pattern: name-YYYY-MM-DD*.log[.gz])
                prefix = f"{self.base_path.stem}-"
                name = log_file.name
                if name.startswith(prefix):
                    remainder = name[len(prefix) :]
                    if remainder.endswith(".gz"):
                        remainder = remainder[:-3]
                    if remainder.endswith(self.base_path.suffix):
                        remainder = remainder[: -len(self.base_path.suffix)]

                    # Expect timestamps like YYYY-MM-DD or YYYY-MM-DD-HHMMSS
                    date_fragment = remainder[:10]
                    try:
                        file_date = datetime.strptime(date_fragment, "%Y-%m-%d")
                    except ValueError:
                        file_date = None

                    if file_date and file_date.date() < cutoff_threshold:
                        deletion_due = True

                if not deletion_due:
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime).date()
                    if mtime < cutoff_threshold:
                        deletion_due = True

                if deletion_due:
                    log_file.unlink()

            except Exception as e:
                import sys

                sys.stderr.write(f"ERROR: Failed to delete old log file {log_file}: {e}\n")

    def flush(self) -> None:
        """Flush buffered data to disk."""
        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    os.fsync(self._file.fileno())
                except Exception:
                    pass

    def close(self) -> None:
        """Close the handler and release resources."""
        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    self._file.close()
                except Exception:
                    pass
                finally:
                    self._file = None

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()
