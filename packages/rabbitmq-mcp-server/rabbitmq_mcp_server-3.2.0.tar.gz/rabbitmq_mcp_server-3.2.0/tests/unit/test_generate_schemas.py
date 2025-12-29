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

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def sample_openapi():
    """Sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "TestQueue": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Queue name",
                            "minLength": 1,
                            "maxLength": 255,
                        },
                        "vhost": {"type": "string", "description": "Virtual host"},
                        "durable": {
                            "type": "boolean",
                            "default": True,
                            "description": "Durability flag",
                        },
                        "message_count": {
                            "type": "integer",
                            "description": "Number of messages",
                        },
                    },
                },
                "TestExchange": {
                    "type": "object",
                    "required": ["name", "type"],
                    "properties": {
                        "name": {"type": "string", "description": "Exchange name"},
                        "type": {
                            "type": "string",
                            "description": "Exchange type",
                            "enum": ["direct", "fanout", "topic", "headers"],
                        },
                        "durable": {"type": "boolean", "default": True},
                    },
                },
                "TestNestedObject": {
                    "type": "object",
                    "properties": {
                        "simple_field": {"type": "string"},
                        "array_field": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "nullable_field": {"type": "string", "nullable": True},
                    },
                },
            }
        },
    }


def test_script_exists():
    """Test that script exists at expected path."""
    script_path = Path("scripts/generate_schemas.py")
    assert script_path.exists(), "Script not found at scripts/generate_schemas.py"


def test_script_executable():
    """Test that script is executable via uv run python."""
    result = subprocess.run(
        ["uv", "run", "python", "scripts/generate_schemas.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Script should execute successfully"
    assert "Generate Pydantic models" in result.stdout


def test_cli_arguments():
    """Test that script accepts required CLI arguments."""
    result = subprocess.run(
        ["uv", "run", "python", "scripts/generate_schemas.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert "--spec-path" in result.stdout
    assert "--output-path" in result.stdout
    assert "--force" in result.stdout


def test_generation_with_valid_openapi(sample_openapi, tmp_path):
    """Test that valid OpenAPI generates models."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Generation failed: {result.stderr}"
    assert output_path.exists(), "Output file not created"
    assert output_path.stat().st_size > 0, "Output file is empty"


def test_generated_models_have_correct_names(sample_openapi, tmp_path):
    """Test that generated models match OpenAPI schema names."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    content = output_path.read_text()
    assert "class TestQueue" in content
    assert "class TestExchange" in content
    assert "class TestNestedObject" in content


def test_file_header_present(sample_openapi, tmp_path):
    """Test that generated file includes proper header."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    content = output_path.read_text()
    assert "# Auto-generated from OpenAPI - DO NOT EDIT MANUALLY" in content
    assert "# Generated:" in content
    assert "# Source:" in content


def test_field_type_mapping(sample_openapi, tmp_path):
    """Test that OpenAPI types are correctly mapped to Python types."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    content = output_path.read_text()
    # Check string → str
    assert "name: str" in content or "name: Annotated[str" in content
    # Check integer → int
    assert "message_count: int" in content or "message_count: Annotated[int" in content
    # Check boolean → bool
    assert "durable: bool" in content or "durable: Annotated[bool" in content
    # Check array → list
    assert "list[" in content or "List[" in content


def test_required_vs_optional_fields(sample_openapi, tmp_path):
    """Test that required fields use correct notation."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    content = output_path.read_text()
    # Optional fields should have | None or Optional
    assert "| None" in content or "Optional[" in content


def test_field_descriptions_preserved(sample_openapi, tmp_path):
    """Test that field descriptions from OpenAPI are preserved."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    content = output_path.read_text()
    # Check that Field() with descriptions exist
    assert "Field(" in content


def test_rabbitmq_validators_present(sample_openapi, tmp_path):
    """Test that RabbitMQ validators are injected."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    content = output_path.read_text()
    # Check for validators
    assert "validate_queue_name" in content or "validate_" in content
    assert "field_validator" in content
    assert "@classmethod" in content


def test_change_detection_works(sample_openapi, tmp_path):
    """Test that change detection skips regeneration if OpenAPI unchanged."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    # First generation
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    # Second generation should skip
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )

    assert "up-to-date" in result.stdout


def test_force_flag_forces_regeneration(sample_openapi, tmp_path):
    """Test that --force flag forces regeneration."""
    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi, f)

    # First generation
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    # Force regeneration
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
            "--force",
        ],
        capture_output=True,
        text=True,
    )

    assert "Generating Pydantic models" in result.stdout
    assert "up-to-date" not in result.stdout


def test_mypy_validation_passes():
    """Test that generated code passes mypy validation."""
    result = subprocess.run(
        ["mypy", "--strict", "src/schemas/generated_schemas.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"mypy validation failed:\n{result.stdout}"


def test_invalid_openapi_fails_gracefully(tmp_path):
    """Test that invalid OpenAPI fails with error message."""
    spec_path = tmp_path / "invalid-spec.yaml"
    output_path = tmp_path / "generated.py"

    # Create invalid YAML
    spec_path.write_text("invalid: yaml: content: [[[")

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0


def test_nonexistent_spec_fails(tmp_path):
    """Test that missing OpenAPI file fails with error."""
    spec_path = tmp_path / "nonexistent.yaml"
    output_path = tmp_path / "generated.py"

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()


def test_validators_only_on_appropriate_entities(tmp_path):
    """Test that validators are only applied to appropriate entity types."""
    # Create OpenAPI with Queue, Exchange, and User entities
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "Queue": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "vhost": {"type": "string"},
                        "durable": {"type": "boolean"},
                    },
                },
                "Exchange": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "vhost": {"type": "string"},
                        "durable": {"type": "boolean"},
                    },
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "tags": {"type": "string"},
                    },
                },
            }
        },
    }

    spec_path = tmp_path / "test-spec.yaml"
    output_path = tmp_path / "generated.py"

    with open(spec_path, "w") as f:
        yaml.dump(spec, f)

    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_schemas.py",
            "--spec-path",
            str(spec_path),
            "--output-path",
            str(output_path),
        ],
        check=True,
    )

    content = output_path.read_text()

    # Find Queue class and check it has queue validators
    queue_start = content.find("class Queue(BaseModel)")
    queue_end = content.find("\nclass ", queue_start + 1)
    if queue_end == -1:
        queue_end = len(content)
    queue_section = content[queue_start:queue_end]
    assert (
        "validate_queue_name" in queue_section
    ), "Queue should have queue name validator"
    assert "validate_vhost" in queue_section, "Queue should have vhost validator"
    assert "validate_durable" in queue_section, "Queue should have durable validator"

    # Find Exchange class and check it has exchange validators
    exchange_start = content.find("class Exchange(BaseModel)")
    exchange_end = content.find("\nclass ", exchange_start + 1)
    if exchange_end == -1:
        exchange_end = len(content)
    exchange_section = content[exchange_start:exchange_end]
    assert (
        "validate_exchange_name" in exchange_section
    ), "Exchange should have exchange name validator"
    assert (
        "validate_exchange_type" in exchange_section
    ), "Exchange should have exchange type validator"
    assert "validate_vhost" in exchange_section, "Exchange should have vhost validator"
    assert (
        "validate_durable" in exchange_section
    ), "Exchange should have durable validator"

    # Find User class and check it has NO validators
    user_start = content.find("class User(BaseModel)")
    user_end = content.find("\nclass ", user_start + 1)
    if user_end == -1:
        user_end = len(content)
    user_section = content[user_start:user_end]
    assert "@field_validator" not in user_section, "User should NOT have validators"
    assert (
        "validate_queue_name" not in user_section
    ), "User should NOT have queue name validator"
