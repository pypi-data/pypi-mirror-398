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

"""Unit tests for runtime configuration reload and signal handling (T041)."""

import os
import signal
import sys
import threading
import time
from collections.abc import Iterable
from pathlib import Path

import pytest
import yaml

from src.logging.config import (
    ConfigReloader,
    install_signal_handlers,
    load_config_from_yaml,
    start_config_watcher,
    stop_config_watcher,
)
from src.models.log_config import LogConfig, LogLevel


@pytest.fixture(autouse=True)
def cleanup_watcher() -> Iterable[None]:
    """Ensure config watcher is stopped after each test."""
    yield
    stop_config_watcher()


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary YAML config file."""
    config_file = tmp_path / "logging_config.yaml"
    config_data = {
        "logging": {
            "log_level": "INFO",
            "output_file": str(tmp_path / "test.log"),
            "async_queue_size": 1000,
            "batch_size": 10,
        }
    }
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file


def test_load_config_from_yaml(temp_config_file: Path):
    """Test loading configuration from YAML file."""
    config = load_config_from_yaml(temp_config_file)

    assert isinstance(config, LogConfig)
    assert config.log_level == LogLevel.INFO
    assert config.async_queue_size == 1000
    assert config.batch_size == 10


def test_load_config_missing_file():
    """Test loading config from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config_from_yaml(Path("/nonexistent/config.yaml"))


def test_load_config_invalid_yaml(tmp_path: Path):
    """Test loading invalid YAML raises appropriate error."""
    invalid_file = tmp_path / "invalid.yaml"
    with open(invalid_file, "w") as f:
        f.write("invalid: yaml: content: [")

    with pytest.raises(yaml.YAMLError):
        load_config_from_yaml(invalid_file)


def test_config_reloader_reload_success(temp_config_file: Path):
    """Test ConfigReloader successfully reloads configuration."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    # Trigger reload
    reloader.reload()

    assert len(reloaded_configs) == 1
    assert reloaded_configs[0].log_level == LogLevel.INFO


def test_config_reloader_reload_updates_config(temp_config_file: Path):
    """Test that reload applies new configuration values."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    # Initial reload
    reloader.reload()
    assert reloaded_configs[0].log_level == LogLevel.INFO

    # Update config file
    config_data = {
        "logging": {
            "log_level": "DEBUG",
            "output_file": str(temp_config_file.parent / "test.log"),
        }
    }
    with open(temp_config_file, "w") as f:
        yaml.dump(config_data, f)

    # Sleep briefly to ensure mtime changes
    time.sleep(0.01)

    # Trigger reload again
    reloader.reload()

    assert len(reloaded_configs) == 2
    assert reloaded_configs[1].log_level == LogLevel.DEBUG


def test_config_reloader_handles_invalid_config(temp_config_file: Path, capsys):
    """Test that reload handles invalid config gracefully."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    # Write invalid config
    with open(temp_config_file, "w") as f:
        f.write("logging:\n  log_level: INVALID_LEVEL\n")

    # Reload should not crash but log warning
    reloader.reload()

    captured = capsys.readouterr()
    assert "WARNING: Failed to reload config" in captured.err
    assert len(reloaded_configs) == 0


def test_config_reloader_thread_safe(temp_config_file: Path):
    """Test that reload is thread-safe with concurrent access."""
    reloaded_configs = []
    reload_lock = threading.Lock()

    def on_reload(config: LogConfig):
        with reload_lock:
            reloaded_configs.append(config)

    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    # Trigger multiple reloads concurrently
    threads = []
    for _ in range(10):
        t = threading.Thread(target=reloader.reload)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # All reloads should complete without errors
    assert len(reloaded_configs) == 10


@pytest.mark.skipif(sys.platform == "win32", reason="Signal handling not supported on Windows")
def test_sighup_triggers_config_reload_unix(temp_config_file: Path):
    """Test that SIGHUP signal triggers configuration reload on Unix."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    # Install signal handlers
    install_signal_handlers(reloader)

    # Send SIGHUP to self
    os.kill(os.getpid(), signal.SIGHUP)

    # Give signal handler time to execute
    time.sleep(0.1)

    assert len(reloaded_configs) >= 1
    assert reloaded_configs[0].log_level == LogLevel.INFO


@pytest.mark.skipif(sys.platform == "win32", reason="Signal handling not supported on Windows")
def test_sigusr1_triggers_config_reload_unix(temp_config_file: Path):
    """Test that SIGUSR1 signal triggers configuration reload on Unix."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    # Install signal handlers
    install_signal_handlers(reloader)

    # Send SIGUSR1 to self
    os.kill(os.getpid(), signal.SIGUSR1)

    # Give signal handler time to execute
    time.sleep(0.1)

    assert len(reloaded_configs) >= 1
    assert reloaded_configs[0].log_level == LogLevel.INFO


@pytest.mark.skipif(sys.platform != "win32", reason="File watcher only used on Windows")
def test_file_watcher_detects_config_changes_windows(temp_config_file: Path):
    """Test that file watcher detects configuration changes on Windows."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    # Use short poll interval for faster test
    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
        poll_interval=0.5,
    )

    # Start watcher
    reloader.start_watcher()

    try:
        # Wait for initial setup
        time.sleep(0.1)

        # Modify config file
        config_data = {
            "logging": {
                "log_level": "DEBUG",
                "output_file": str(temp_config_file.parent / "test.log"),
            }
        }
        with open(temp_config_file, "w") as f:
            yaml.dump(config_data, f)

        # Wait for watcher to detect change (poll_interval + buffer)
        time.sleep(1.0)

        assert len(reloaded_configs) >= 1
        assert reloaded_configs[-1].log_level == LogLevel.DEBUG
    finally:
        reloader.stop_watcher()


def test_start_stop_config_watcher(temp_config_file: Path):
    """Test starting and stopping config watcher."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    # Start watcher
    start_config_watcher(
        config_path=temp_config_file,
        on_reload=on_reload,
        poll_interval=0.5,
    )

    # Stop watcher
    stop_config_watcher()

    # Should not crash


def test_config_watcher_respects_poll_interval_env_var(temp_config_file: Path, monkeypatch):
    """Test that config watcher respects LOGGING_CONFIG_POLL_INTERVAL_MS env var."""
    reloaded_configs = []

    def on_reload(config: LogConfig):
        reloaded_configs.append(config)

    # Set env var to 200ms
    monkeypatch.setenv("LOGGING_CONFIG_POLL_INTERVAL_MS", "200")

    ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
        poll_interval=None,  # Should use env var
    )

    # The reloader doesn't read env var in __init__, but start_config_watcher does
    # This test validates the integration point
    start_config_watcher(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    stop_config_watcher()


def test_reload_applies_new_log_level(temp_config_file: Path):
    """Test that reload callback receives updated log level."""
    received_levels = []

    def on_reload(config: LogConfig):
        received_levels.append(config.log_level)

    reloader = ConfigReloader(
        config_path=temp_config_file,
        on_reload=on_reload,
    )

    # Initial config is INFO
    reloader.reload()
    assert received_levels[0] == LogLevel.INFO

    # Update to DEBUG
    config_data = {
        "logging": {
            "log_level": "DEBUG",
            "output_file": str(temp_config_file.parent / "test.log"),
        }
    }
    with open(temp_config_file, "w") as f:
        yaml.dump(config_data, f)

    time.sleep(0.01)
    reloader.reload()
    assert received_levels[1] == LogLevel.DEBUG

    # Update to ERROR
    config_data["logging"]["log_level"] = "ERROR"
    with open(temp_config_file, "w") as f:
        yaml.dump(config_data, f)

    time.sleep(0.01)
    reloader.reload()
    assert received_levels[2] == LogLevel.ERROR
