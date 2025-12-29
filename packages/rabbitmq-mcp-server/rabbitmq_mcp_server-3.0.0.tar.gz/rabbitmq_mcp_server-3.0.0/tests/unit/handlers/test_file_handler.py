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

import errno
import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from src.logging.handlers import file as file_module
from src.logging.handlers.file import FileLogHandler


@pytest.fixture
def log_entry() -> dict:
    return {"event": "test", "value": 1}


def _read_lines(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def test_file_handler_creates_log_file(tmp_path: Path, log_entry: dict):
    log_file = tmp_path / "logs" / "app.log"
    handler = FileLogHandler(log_file)

    handler.write_batch([log_entry])

    assert log_file.exists()


def test_file_handler_writes_json_entries(tmp_path: Path):
    log_file = tmp_path / "logs" / "app.log"
    handler = FileLogHandler(log_file)
    entries = [{"event": "first"}, {"event": "second", "extra": {"a": 1}}]

    handler.write_batch(entries)

    written = list(_read_lines(log_file))
    assert written == entries


def test_file_handler_appends_multiple_entries(tmp_path: Path, log_entry: dict):
    log_file = tmp_path / "logs" / "app.log"
    handler = FileLogHandler(log_file)

    handler.write_batch([log_entry])
    handler.write_batch([{"event": "second"}])

    written = list(_read_lines(log_file))
    assert written == [log_entry, {"event": "second"}]


def test_file_handler_creates_directory_if_missing(tmp_path: Path, log_entry: dict):
    log_file = tmp_path / "nested" / "structure" / "app.log"
    handler = FileLogHandler(log_file)

    handler.write_batch([log_entry])

    assert log_file.exists()
    assert log_file.parent.exists()


def test_file_handler_falls_back_on_permission_error(
    tmp_path: Path, log_entry: dict, monkeypatch: pytest.MonkeyPatch
):
    log_file = tmp_path / "logs" / "app.log"
    fallback_calls = []

    def fallback(batch):
        fallback_calls.extend(batch)

    handler = FileLogHandler(log_file, fallback=fallback)

    monkeypatch.setattr(
        Path, "open", lambda *_, **__: (_ for _ in ()).throw(PermissionError("denied"))
    )

    handler.write_batch([log_entry])

    assert fallback_calls == [log_entry]
    assert not log_file.exists()


def test_file_handler_handles_disk_full_error(
    tmp_path: Path, log_entry: dict, monkeypatch: pytest.MonkeyPatch
):
    log_file = tmp_path / "logs" / "app.log"
    fallback_calls = []

    def fallback(batch):
        fallback_calls.extend(batch)

    handler = FileLogHandler(log_file, fallback=fallback)

    def raise_disk_full(*args, **kwargs):
        raise OSError(errno.ENOSPC, "No space left")

    monkeypatch.setattr(Path, "open", raise_disk_full)

    handler.write_batch([log_entry])

    assert fallback_calls == [log_entry]


def test_file_handler_handles_concurrent_access(
    tmp_path: Path, log_entry: dict, monkeypatch: pytest.MonkeyPatch
):
    log_file = tmp_path / "logs" / "app.log"
    fallback_calls = []

    def fallback(batch):
        fallback_calls.extend(batch)

    handler = FileLogHandler(log_file, fallback=fallback)

    def raise_blocking(*args, **kwargs):
        raise BlockingIOError("file busy")

    monkeypatch.setattr(Path, "open", raise_blocking)

    handler.write_batch([log_entry])

    assert fallback_calls == [log_entry]


def test_file_handler_handles_read_only_filesystem(
    tmp_path: Path, log_entry: dict, monkeypatch: pytest.MonkeyPatch
):
    log_file = tmp_path / "logs" / "app.log"
    fallback_calls = []

    def fallback(batch):
        fallback_calls.extend(batch)

    handler = FileLogHandler(log_file, fallback=fallback)

    def raise_read_only(*args, **kwargs):
        raise OSError(errno.EROFS, "read-only fs")

    monkeypatch.setattr(Path, "open", raise_read_only)

    handler.write_batch([log_entry])

    assert fallback_calls == [log_entry]


def test_file_handler_sets_secure_permissions_on_creation(
    tmp_path: Path,
    log_entry: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_file = tmp_path / "logs" / "app.log"
    chmod_calls: list[tuple[Path, int]] = []

    def record_chmod(path, mode):
        chmod_calls.append((Path(path), mode))

    monkeypatch.setattr(file_module.os, "chmod", record_chmod)

    handler = FileLogHandler(log_file)
    handler.write_batch([log_entry])

    assert chmod_calls == [(log_file, 0o600)]
    assert log_file.exists()

    stderr = capsys.readouterr().err
    assert f"DEBUG: Secure permissions (600) set successfully on log file {log_file}" in stderr


def test_file_handler_warns_when_permissions_fail_on_unix(
    tmp_path: Path,
    log_entry: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_file = tmp_path / "logs" / "app.log"

    def raise_permission(*args, **kwargs):
        raise PermissionError("operation not permitted")

    monkeypatch.setattr(file_module.os, "chmod", raise_permission)

    handler = FileLogHandler(log_file)
    handler._is_windows = False

    handler.write_batch([log_entry])

    stderr = capsys.readouterr().err
    assert "WARNING: Failed to set secure permissions (600) on log file" in stderr
    assert "operation not permitted" in stderr


def test_file_handler_silences_permission_failure_on_windows(
    tmp_path: Path,
    log_entry: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_file = tmp_path / "logs" / "app.log"

    def raise_permission(*args, **kwargs):
        raise PermissionError("unsupported")

    monkeypatch.setattr(file_module.os, "chmod", raise_permission)

    handler = FileLogHandler(log_file)
    handler._is_windows = True

    handler.write_batch([log_entry])

    stderr = capsys.readouterr().err
    assert stderr == ""
    assert log_file.exists()
