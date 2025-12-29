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

import json
from pathlib import Path

import pytest

from mcp_server.utils.logging import (
    SENSITIVE_FIELD_PATTERNS,
    _redact_string,
    configure_logging,
    reset_logging,
)


@pytest.fixture(autouse=True)
def _reset_logging_state():
    reset_logging()
    yield
    reset_logging()


def _read_records(handler):
    path = handler.current_log_path
    if path is None or not Path(path).exists():
        return []
    raw = Path(path).read_text(encoding="utf-8")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def test_structured_logger_outputs_json_and_redacts_sensitive_fields(tmp_path):
    ctx = configure_logging(output_dir=tmp_path, app_name="rabbitmq-mcp-test")
    logger = ctx.logger

    payload = {pattern: f"{pattern}-secret" for pattern in SENSITIVE_FIELD_PATTERNS}
    message = " ".join(f"{pattern}=topsecret" for pattern in SENSITIVE_FIELD_PATTERNS)

    logger.info(message, **payload)
    ctx.flush()

    general_handler = next(handler for handler in ctx.handlers if handler.name == "general")
    records = _read_records(general_handler)
    assert records, "esperava pelo menos um registro de log"

    record = records[-1]
    assert record.get("message")
    assert "timestamp" in record
    assert record.get("level") in {"info", "INFO"}

    for pattern in SENSITIVE_FIELD_PATTERNS:
        assert record.get(pattern) == "***", f"{pattern} não foi redatado"
        assert f"{pattern}=topsecret" not in record["message"].lower()
        assert f"{pattern}=***" in _redact_string(record["message"]).lower()


def test_logger_respects_environment_log_level(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    ctx = configure_logging(output_dir=tmp_path, app_name="rabbitmq-mcp-test")
    logger = ctx.logger

    logger.info("mensagem ignorada", password="secret")
    ctx.flush()

    general_handler = next(handler for handler in ctx.handlers if handler.name == "general")
    records = _read_records(general_handler)
    assert not records, "logs INFO não deveriam ser registrados quando LOG_LEVEL=ERROR"


def test_error_logs_include_exception_context(tmp_path):
    ctx = configure_logging(output_dir=tmp_path, app_name="rabbitmq-mcp-test")
    logger = ctx.logger

    try:
        raise ValueError("falha proposital")
    except ValueError:
        logger.exception("falha na operação", request_id="req-123")

    ctx.flush()

    general_handler = next(handler for handler in ctx.handlers if handler.name == "general")
    records = _read_records(general_handler)
    assert records

    record = records[-1]
    assert record["message"] == "falha na operação"
    assert record["request_id"] == "req-123"
    assert "exception" in record
    assert "ValueError" in record["exception"]


def test_rotation_policy_metadata(tmp_path):
    ctx = configure_logging(output_dir=tmp_path, app_name="rabbitmq-mcp-test")

    policies = ctx.policies
    assert policies["general"]["retention_days"] == 30
    assert policies["general"]["max_bytes"] == 100 * 1024 * 1024
    assert policies["general"]["rotation"] == "daily"

    assert policies["errors"]["retention_days"] == 90
    assert policies["audit"]["retention_days"] == 365

    general_handler = next(handler for handler in ctx.handlers if handler.name == "general")
    assert getattr(general_handler, "max_bytes", None) == 100 * 1024 * 1024
    assert getattr(general_handler, "retention_days", None) == 30
