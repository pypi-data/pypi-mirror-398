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

"""Configuration reload and signal handling for logging system."""

import os
import signal
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import yaml
from pydantic import ValidationError

from models.log_config import LogConfig

__all__ = [
    "ConfigReloader",
    "install_signal_handlers",
    "load_config_from_yaml",
    "start_config_watcher",
    "stop_config_watcher",
]


_config_reloader: ConfigReloader | None = None
_reloader_lock = threading.Lock()


def load_config_from_yaml(config_path: Path) -> LogConfig:
    """
    Load logging configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        LogConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    # Extract logging section if present
    logging_config = data.get("logging", data)

    return LogConfig(**logging_config)


class ConfigReloader:
    """
    Manages runtime configuration reload with platform-specific strategies.

    Unix/Linux/macOS: Uses SIGHUP/SIGUSR1 signal handlers
    Windows: Uses file modification time polling (5-second default interval)
    """

    def __init__(
        self,
        config_path: Path,
        on_reload: Callable[[LogConfig], None],
        poll_interval: float = 5.0,
    ) -> None:
        """
        Initialize config reloader.

        Args:
            config_path: Path to configuration file to watch
            on_reload: Callback function called with new config when reload occurs
            poll_interval: Polling interval in seconds for file watching (Windows)
        """
        self.config_path = config_path
        self.on_reload = on_reload
        self.poll_interval = poll_interval
        self._lock = threading.Lock()
        self._last_mtime: float | None = None
        self._watcher_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._is_windows = sys.platform == "win32"

    def reload(self) -> None:
        """
        Reload configuration from file (thread-safe).

        This method can be called from signal handlers or polling thread.
        """
        with self._lock:
            try:
                new_config = load_config_from_yaml(self.config_path)
                self.on_reload(new_config)
                # Update mtime after successful reload
                self._last_mtime = self.config_path.stat().st_mtime
            except (FileNotFoundError, ValidationError, yaml.YAMLError) as exc:
                # Log to stderr to avoid circular dependency on logging system
                print(
                    f"WARNING: Failed to reload config from {self.config_path}: {exc}",
                    file=sys.stderr,
                )

    def start_watcher(self) -> None:
        """Start file watcher thread (Windows only)."""
        if not self._is_windows:
            return

        if self._watcher_thread is not None and self._watcher_thread.is_alive():
            return

        # Initialize last_mtime
        if self.config_path.exists():
            self._last_mtime = self.config_path.stat().st_mtime

        self._stop_event.clear()
        self._watcher_thread = threading.Thread(
            target=self._watch_file,
            daemon=True,
            name="ConfigWatcher",
        )
        self._watcher_thread.start()

    def stop_watcher(self) -> None:
        """Stop file watcher thread."""
        if self._watcher_thread is None:
            return

        self._stop_event.set()
        self._watcher_thread.join(timeout=self.poll_interval + 1.0)
        self._watcher_thread = None

    def _watch_file(self) -> None:
        """
        File watching loop (runs in background thread on Windows).

        Polls config file every poll_interval seconds and triggers reload
        when modification time changes.
        """
        while not self._stop_event.is_set():
            try:
                if self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    if self._last_mtime is not None and current_mtime > self._last_mtime:
                        self.reload()
            except Exception as exc:
                print(
                    f"WARNING: Error in config watcher: {exc}",
                    file=sys.stderr,
                )

            # Sleep in small intervals to allow quick shutdown
            for _ in range(int(self.poll_interval * 10)):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)


def install_signal_handlers(reloader: ConfigReloader) -> None:
    """
    Install signal handlers for configuration reload (Unix/Linux/macOS only).

    Registers handlers for:
    - SIGHUP: Hangup signal (traditional config reload signal)
    - SIGUSR1: User-defined signal 1 (alternative reload trigger)

    Args:
        reloader: ConfigReloader instance to trigger on signals
    """
    if sys.platform == "win32":
        # Windows doesn't support POSIX signals
        return

    def signal_handler(signum: int, frame: object | None) -> None:
        """Signal handler that triggers config reload."""
        reloader.reload()

    # Register SIGHUP (traditional config reload signal)
    signal.signal(signal.SIGHUP, signal_handler)

    # Register SIGUSR1 (alternative reload signal)
    signal.signal(signal.SIGUSR1, signal_handler)


def start_config_watcher(
    config_path: Path | str,
    on_reload: Callable[[LogConfig], None],
    poll_interval: float | None = None,
) -> None:
    """
    Start configuration watcher with platform-appropriate strategy.

    Unix/Linux/macOS: Installs signal handlers (SIGHUP, SIGUSR1)
    Windows: Starts file polling thread (default 5-second interval)

    Args:
        config_path: Path to configuration file
        on_reload: Callback function called with new config on reload
        poll_interval: Polling interval (Windows only, default from env or 5.0 seconds)
    """
    global _config_reloader

    if isinstance(config_path, str):
        config_path = Path(config_path)

    # Get polling interval from env var or use provided/default
    if poll_interval is None:
        poll_interval_ms = os.environ.get("LOGGING_CONFIG_POLL_INTERVAL_MS")
        if poll_interval_ms is not None:
            poll_interval = float(poll_interval_ms) / 1000.0
        else:
            poll_interval = 5.0

    with _reloader_lock:
        if _config_reloader is not None:
            # Stop existing watcher
            _config_reloader.stop_watcher()

        _config_reloader = ConfigReloader(
            config_path=config_path,
            on_reload=on_reload,
            poll_interval=poll_interval,
        )

        # Install signal handlers (Unix/Linux/macOS) or start polling (Windows)
        if sys.platform != "win32":
            install_signal_handlers(_config_reloader)
        else:
            _config_reloader.start_watcher()


def stop_config_watcher() -> None:
    """Stop configuration watcher if running."""
    global _config_reloader

    with _reloader_lock:
        if _config_reloader is not None:
            _config_reloader.stop_watcher()
            _config_reloader = None
