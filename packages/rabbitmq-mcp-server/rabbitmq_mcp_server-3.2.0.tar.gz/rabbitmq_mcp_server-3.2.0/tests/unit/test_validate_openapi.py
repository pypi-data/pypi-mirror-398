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

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from validate_openapi import load_openapi_spec, main, validate_operationids


@pytest.fixture
def valid_openapi_spec() -> dict:
    """Fixture providing a valid minimal OpenAPI 3.0 specification."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "users.list",
                    "summary": "List users",
                    "responses": {"200": {"description": "Success"}},
                }
            },
            "/users/{id}": {
                "get": {
                    "operationId": "users.get",
                    "summary": "Get user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            },
        },
    }


@pytest.fixture
def invalid_openapi_spec_missing_operationid() -> dict:
    """Fixture providing OpenAPI spec with missing operationId."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


@pytest.fixture
def invalid_openapi_spec_duplicate_operationid() -> dict:
    """Fixture providing OpenAPI spec with duplicate operationId."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "users.get",
                    "summary": "List users",
                    "responses": {"200": {"description": "Success"}},
                }
            },
            "/users/{id}": {
                "get": {
                    "operationId": "users.get",
                    "summary": "Get user",
                    "responses": {"200": {"description": "Success"}},
                }
            },
        },
    }


class TestLoadOpenAPISpec:
    """Tests for load_openapi_spec function."""

    def test_load_valid_spec(self, valid_openapi_spec: dict, tmp_path: Path) -> None:
        """Test loading valid OpenAPI specification from file."""
        spec_file = tmp_path / "openapi.yaml"
        with open(spec_file, "w") as f:
            yaml.dump(valid_openapi_spec, f)

        loaded_spec = load_openapi_spec(str(spec_file))
        assert loaded_spec == valid_openapi_spec

    def test_load_nonexistent_file(self) -> None:
        """Test loading OpenAPI spec from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_openapi_spec("nonexistent.yaml")

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading invalid YAML raises error."""
        spec_file = tmp_path / "invalid.yaml"
        with open(spec_file, "w") as f:
            f.write("invalid: yaml: content: [[[")

        with pytest.raises(yaml.YAMLError):
            load_openapi_spec(str(spec_file))


class TestValidateOperationIds:
    """Tests for validate_operationids function."""

    def test_validate_valid_spec(self, valid_openapi_spec: dict) -> None:
        """Test validation passes for spec with unique operationIds."""
        errors = validate_operationids(valid_openapi_spec)
        assert errors == []

    def test_validate_missing_operationid(
        self, invalid_openapi_spec_missing_operationid: dict
    ) -> None:
        """Test validation fails for spec with missing operationId."""
        errors = validate_operationids(invalid_openapi_spec_missing_operationid)
        assert len(errors) == 1
        assert "Missing operationId" in errors[0]
        assert "GET /users" in errors[0]

    def test_validate_duplicate_operationid(
        self, invalid_openapi_spec_duplicate_operationid: dict
    ) -> None:
        """Test validation fails for spec with duplicate operationId."""
        errors = validate_operationids(invalid_openapi_spec_duplicate_operationid)
        assert len(errors) == 1
        assert "Duplicate operationId" in errors[0]
        assert "users.get" in errors[0]

    def test_validate_empty_paths(self) -> None:
        """Test validation passes for spec with no paths."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        errors = validate_operationids(spec)
        assert errors == []

    def test_validate_ignores_non_operation_keys(self) -> None:
        """Test validation ignores non-operation keys in paths."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "parameters": [{"name": "test", "in": "query"}],
                    "get": {
                        "operationId": "users.list",
                        "responses": {"200": {"description": "Success"}},
                    },
                }
            },
        }
        errors = validate_operationids(spec)
        assert errors == []


class TestMainFunction:
    """Tests for main CLI function."""

    def test_main_valid_spec(
        self, valid_openapi_spec: dict, tmp_path: Path, capsys
    ) -> None:
        """Test main function with valid OpenAPI spec."""
        spec_file = tmp_path / "openapi.yaml"
        with open(spec_file, "w") as f:
            yaml.dump(valid_openapi_spec, f)

        with patch(
            "sys.argv",
            [
                "validate_openapi.py",
                "--spec-path",
                str(spec_file),
                "--skip-schema-validation",
            ],
        ):
            main()

        captured = capsys.readouterr()
        assert "valid" in (captured.out + captured.err).lower()

    def test_main_invalid_spec_missing_operationid(
        self,
        invalid_openapi_spec_missing_operationid: dict,
        tmp_path: Path,
        capsys,
    ) -> None:
        """Test main function with spec missing operationId."""
        spec_file = tmp_path / "openapi.yaml"
        with open(spec_file, "w") as f:
            yaml.dump(invalid_openapi_spec_missing_operationid, f)

        with patch(
            "sys.argv",
            [
                "validate_openapi.py",
                "--spec-path",
                str(spec_file),
                "--skip-schema-validation",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Missing operationId" in captured.err

    def test_main_nonexistent_file(self, tmp_path: Path, capsys) -> None:
        """Test main function with nonexistent file."""
        spec_file = tmp_path / "nonexistent.yaml"

        with patch("sys.argv", ["validate_openapi.py", "--spec-path", str(spec_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_main_with_skip_schema_validation(
        self, valid_openapi_spec: dict, tmp_path: Path, capsys
    ) -> None:
        """Test main function with --skip-schema-validation flag."""
        spec_file = tmp_path / "openapi.yaml"
        with open(spec_file, "w") as f:
            yaml.dump(valid_openapi_spec, f)

        with patch(
            "sys.argv",
            [
                "validate_openapi.py",
                "--spec-path",
                str(spec_file),
                "--skip-schema-validation",
            ],
        ):
            main()

        captured = capsys.readouterr()
        assert "valid" in (captured.out + captured.err).lower()


class TestProjectOpenAPISpec:
    """Integration tests for actual project OpenAPI specification."""

    def test_project_spec_exists(self) -> None:
        """Test that project OpenAPI specification file exists."""
        project_root = Path(__file__).parent.parent.parent
        spec_path = project_root / "docs-bmad" / "rabbitmq-http-api-openapi.yaml"
        assert spec_path.exists(), "OpenAPI specification file must exist"

    def test_project_spec_is_valid_yaml(self) -> None:
        """Test that project OpenAPI specification is valid YAML."""
        project_root = Path(__file__).parent.parent.parent
        spec_path = project_root / "docs-bmad" / "rabbitmq-http-api-openapi.yaml"

        spec = load_openapi_spec(str(spec_path))
        assert spec is not None
        assert "openapi" in spec
        assert "paths" in spec

    def test_project_spec_has_operations(self) -> None:
        """Test that project OpenAPI specification has operations."""
        project_root = Path(__file__).parent.parent.parent
        spec_path = project_root / "docs-bmad" / "rabbitmq-http-api-openapi.yaml"

        spec = load_openapi_spec(str(spec_path))
        paths = spec.get("paths", {})

        operation_count = 0
        for path_item in paths.values():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation_count += 1

        assert operation_count >= 100, "Specification should have 100+ operations"

    def test_project_spec_all_operations_have_operationid(self) -> None:
        """Test that all operations in project spec have operationId."""
        project_root = Path(__file__).parent.parent.parent
        spec_path = project_root / "docs-bmad" / "rabbitmq-http-api-openapi.yaml"

        spec = load_openapi_spec(str(spec_path))
        errors = validate_operationids(spec)

        assert errors == [], f"OperationId validation errors: {errors}"

    def test_project_spec_operationid_format(self) -> None:
        """Test that operationIds follow expected format pattern."""
        project_root = Path(__file__).parent.parent.parent
        spec_path = project_root / "docs-bmad" / "rabbitmq-http-api-openapi.yaml"

        spec = load_openapi_spec(str(spec_path))
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in methods and isinstance(methods[method], dict):
                    operation_id = methods[method].get("operationId", "")
                    # Check format: namespace.action or namespace_resource.action
                    assert (
                        "." in operation_id
                    ), f"{method.upper()} {path} operationId missing dot: {operation_id}"
                    parts = operation_id.split(".")
                    assert (
                        len(parts) == 2
                    ), f"{method.upper()} {path} operationId invalid format: {operation_id}"
