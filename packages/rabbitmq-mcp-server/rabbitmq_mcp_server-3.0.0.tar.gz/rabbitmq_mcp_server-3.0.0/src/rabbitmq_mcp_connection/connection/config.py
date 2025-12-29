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

"""Carregamento multi-fonte de configurações de conexão AMQP.

Este módulo implementa a lógica descrita na tasks T008/T011-T017 para
obter uma instância validada de ``ConnectionConfig`` respeitando a
precedência: argumentos explícitos > variáveis de ambiente > arquivo TOML
> valores padrão do schema.
"""

import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rabbitmq_mcp_connection.logging.config import get_logger
from rabbitmq_mcp_connection.schemas.connection import ConnectionConfig

try:  # pragma: no cover - disponibilidade depende da versão do Python
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]

LOGGER = get_logger(__name__)

ENV_PREFIX = "AMQP_"
ENV_MAPPING: Mapping[str, str] = {
    "AMQP_HOST": "host",
    "AMQP_PORT": "port",
    "AMQP_USER": "user",
    "AMQP_PASSWORD": "password",
    "AMQP_VHOST": "vhost",
    "AMQP_TIMEOUT": "timeout",
    "AMQP_HEARTBEAT": "heartbeat",
}

DEFAULT_CONFIG_PATHS: tuple[Path, ...] = (
    Path("config/config.toml"),
    Path("config.toml"),
)


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - erro raro
        LOGGER.error("config.toml_invalid", path=str(path), exception=str(exc))
        raise

    # Suportar estruturas simples ou aninhadas (e.g. [amqp])
    if "amqp" in data and isinstance(data["amqp"], Mapping):
        amqp_section = data["amqp"]
    else:
        amqp_section = data

    return {
        key: amqp_section.get(key)
        for key in ConnectionConfig.model_fields.keys()
        if isinstance(amqp_section, Mapping)
    }


def _load_env_values() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for env_key, field_name in ENV_MAPPING.items():
        raw_value = os.getenv(env_key)
        if raw_value is None:
            continue
        values[field_name] = raw_value
    return values


def _apply_overrides(base: dict[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in overrides.items():
        if key in ConnectionConfig.model_fields:
            result[key] = value
    return result


def _iter_existing_paths(custom_path: Path | None) -> Iterable[Path]:
    if custom_path:
        yield custom_path
    for candidate in DEFAULT_CONFIG_PATHS:
        if candidate.exists():
            yield candidate


def load_config(config_file: str | Path | None = None, **overrides: Any) -> ConnectionConfig:
    """Carrega configuração de conexão com precedência definida.

    Parameters
    ----------
    config_file:
        Caminho explícito para arquivo TOML. Quando ``None`` serão
        utilizados valores padrão conhecidos.
    overrides:
        Argumentos com maior precedência. Apenas campos válidos do
        ``ConnectionConfig`` são considerados.

    Returns
    -------
    ConnectionConfig
        Instância validada pronta para uso com ``ConnectionManager``.
    """

    base: dict[str, Any] = {}

    path_obj: Path | None = Path(config_file) if config_file else None
    for path in _iter_existing_paths(path_obj):
        base.update({k: v for k, v in _load_toml(path).items() if v is not None})

    env_values = _load_env_values()
    base.update(env_values)

    base = _apply_overrides(base, overrides)
    try:
        return ConnectionConfig(**base)
    except ValidationError as exc:
        LOGGER.error("config.validation_failed", errors=exc.errors())
        raise


__all__ = ["load_config"]
