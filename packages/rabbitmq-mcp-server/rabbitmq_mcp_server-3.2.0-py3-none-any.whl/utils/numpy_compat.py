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

"""Lightweight compatibility helpers for third-party packages using deprecated NumPy aliases."""

from typing import Any


def ensure_numpy_compat() -> None:
    """Restore deprecated NumPy aliases when running on NumPy 2.x."""

    try:
        import numpy as np
    except Exception:  # pragma: no cover - numpy not installed
        return

    aliases: dict[str, Any] = {
        "bool": bool,
        "int": int,
        "float": float,
        "complex": complex,
        "object": object,
    }

    for name, target in aliases.items():
        if getattr(np, name, None) is None:
            setattr(np, name, target)

    if getattr(np, "float_", None) is None:
        setattr(np, "float_", float)
    if getattr(np, "int_", None) is None:
        setattr(np, "int_", int)
