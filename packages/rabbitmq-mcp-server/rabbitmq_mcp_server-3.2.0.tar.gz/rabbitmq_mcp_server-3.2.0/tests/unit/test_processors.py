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

from src.logging import processors


def test_add_correlation_id_injects_current_value(monkeypatch):
    monkeypatch.setattr(processors, "get_correlation_id", lambda: "abc123")

    result = processors.add_correlation_id(None, "info", {})

    assert result["correlation_id"] == "abc123"


def test_add_correlation_id_skips_when_missing(monkeypatch):
    monkeypatch.setattr(processors, "get_correlation_id", lambda: None)

    result = processors.add_correlation_id(None, "info", {"existing": 1})

    assert "correlation_id" not in result
    assert result["existing"] == 1


def test_redaction_processor_applies_redaction(monkeypatch):
    def fake_apply(event):
        event = dict(event)
        event["password"] = "[REDACTED]"
        return event

    monkeypatch.setattr(processors, "apply_redaction_to_event", fake_apply)

    result = processors.redact_sensitive_data(
        None, "info", {"password": "secret", "other": "value"}
    )

    assert result["password"] == "[REDACTED]"
    assert result["other"] == "value"
