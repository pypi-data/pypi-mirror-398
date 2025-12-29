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

import errno
import os
import sys
from collections.abc import Callable, Iterable
from logging.rotation import RotatingLogHandler
from pathlib import Path
from typing import Any

import orjson

from models.log_config import LogConfig


class FileLogHandler:
    def __init__(
        self,
        path: Path,
        *,
        fallback: Callable[[Iterable[dict[str, Any]]], None] | None = None,
        config: LogConfig | None = None,
    ) -> None:
        self._path = Path(path)
        self._fallback = fallback
        self._permissions_attempted = False
        self._is_windows = os.name == "nt"
        self._config = config

        # Initialize rotation handler if rotation is enabled
        self._rotation_handler = None
        if config and (config.rotation_max_bytes > 0 or config.rotation_when):
            self._rotation_handler = RotatingLogHandler(config)

    def write_batch(self, batch: Iterable[dict[str, Any]]) -> None:
        entries = list(batch)

        # Use rotation handler if configured
        if self._rotation_handler:
            try:
                for item in entries:
                    self._rotation_handler.write_log(item)
            except Exception as exc:
                self._handle_fallback(entries, exc)
            return

        # Original non-rotating logic
        try:
            self._ensure_parent_directory()
            file_existed = self._path.exists()
            with self._path.open("ab") as file:
                if not file_existed:
                    self._apply_secure_permissions()
                for item in entries:
                    file.write(orjson.dumps(item) + b"\n")
        except (PermissionError, BlockingIOError) as exc:
            self._handle_fallback(entries, exc)
        except OSError as exc:
            if exc.errno in (errno.ENOSPC, errno.EROFS):
                self._handle_fallback(entries, exc)
            else:
                raise

    def flush(self) -> None:
        if self._rotation_handler is not None:
            self._rotation_handler.flush()

    def close(self) -> None:
        if self._rotation_handler is not None:
            self._rotation_handler.close()

    def _handle_fallback(self, batch: Iterable[dict[str, Any]], exc: Exception) -> None:
        if self._fallback:
            self._fallback(list(batch))
        else:
            raise exc

    def _ensure_parent_directory(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _apply_secure_permissions(self) -> None:
        if self._permissions_attempted:
            return
        self._permissions_attempted = True
        try:
            os.chmod(self._path, 0o600)
        except NotImplementedError:
            return
        except OSError as exc:
            if self._is_windows:
                return
            self._log_permission_warning(exc)
        else:
            self._log_permission_debug()

    def _log_permission_debug(self) -> None:
        sys.stderr.write(
            f"DEBUG: Secure permissions (600) set successfully on log file {self._path}\n"
        )

    def _log_permission_warning(self, exc: OSError) -> None:
        sys.stderr.write(
            "WARNING: Failed to set secure permissions (600) on log file "
            f"{self._path}: {exc}. Using OS default permissions. This may expose sensitive log data on multi-user systems.\n"
        )
