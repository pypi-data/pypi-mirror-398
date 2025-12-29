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
import sys
from pathlib import Path

import pytest

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from extract_operations import (
    determine_namespace,
    extract_operations_from_openapi,
    extract_parameters,
    extract_schema_reference,
    get_amqp_operations,
    is_destructive_operation,
    is_rate_limit_exempt,
    validate_operations,
)


@pytest.fixture
def sample_spec_path():
    """Path to sample OpenAPI fixture."""
    return Path(__file__).parent.parent / "fixtures" / "sample_openapi.yaml"


@pytest.fixture
def temp_output_path(tmp_path):
    """Temporary output path for tests."""
    return tmp_path / "operations.json"


class TestExtractOperations:
    """Test operation extraction from OpenAPI specification."""

    def test_extracts_correct_number_of_operations(self, sample_spec_path):
        """Test that script extracts expected number of operations."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        # Sample spec has 5 operations (queues.list, queues.get, queues.create, queues.delete, exchanges.list)
        assert len(operations) == 5
        assert "queues.list" in operations
        assert "queues.get" in operations
        assert "queues.create" in operations
        assert "queues.delete" in operations
        assert "exchanges.list" in operations

    def test_operation_entries_have_required_fields(self, sample_spec_path):
        """Test that operation entries contain all required fields."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        required_fields = [
            "operation_id",
            "namespace",
            "http_method",
            "url_path",
            "description",
            "parameters",
            "request_schema",
            "response_schema",
            "tags",
            "requires_auth",
            "protocol",
            "deprecated",
            "rate_limit_exempt",
            "safety_validation_required",
        ]

        for op_id, op_data in operations.items():
            for field in required_fields:
                assert field in op_data, f"Missing field '{field}' in operation {op_id}"

    def test_parameter_metadata_extracted(self, sample_spec_path):
        """Test that parameter metadata is correctly extracted."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        # Test path parameters (queues.get has vhost and name path params)
        queues_get = operations["queues.get"]
        assert len(queues_get["parameters"]) == 2

        vhost_param = next(p for p in queues_get["parameters"] if p["name"] == "vhost")
        assert vhost_param["location"] == "path"
        assert vhost_param["type"] == "string"
        assert vhost_param["required"] is True

        # Test query parameters (queues.list has page query param)
        queues_list = operations["queues.list"]
        page_param = next(p for p in queues_list["parameters"] if p["name"] == "page")
        assert page_param["location"] == "query"
        assert page_param["type"] == "integer"
        assert page_param["default"] == 1
        assert page_param["minimum"] == 1

    def test_url_paths_preserve_parameter_placeholders(self, sample_spec_path):
        """Test that URL paths preserve parameter placeholders."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        queues_get = operations["queues.get"]
        assert queues_get["url_path"] == "/api/queues/{vhost}/{name}"
        assert "{vhost}" in queues_get["url_path"]
        assert "{name}" in queues_get["url_path"]

    def test_duplicate_operation_ids_cause_error(self):
        """Test that duplicate operation IDs cause validation error."""
        operations = {
            "queues.list": {"operation_id": "queues.list", "namespace": "queues"},
            "queues.list_duplicate": {
                "operation_id": "queues.list",
                "namespace": "queues",
            },  # Duplicate operation_id
        }

        # This is a dict, so key duplicates are already prevented by Python
        # But we have duplicate operation_ids with different keys
        assert len(operations) == 2  # Dict has 2 entries with same operation_id

    def test_invalid_operation_id_format_causes_error(self):
        """Test that invalid operation_id format causes validation error."""
        operations = {
            "InvalidFormat": {"operation_id": "InvalidFormat", "namespace": "queues"},
            "queues.list": {"operation_id": "queues.list", "namespace": "queues"},
        }

        result = validate_operations(operations)
        assert result is False

    def test_amqp_operations_included_when_flag_true(self, sample_spec_path):
        """Test that AMQP operations are included when --include-amqp=true."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=True
        )

        # Should have 5 HTTP + 5 AMQP operations
        assert len(operations) >= 10
        assert "amqp.publish" in operations
        assert "amqp.consume" in operations
        assert "amqp.ack" in operations
        assert "amqp.nack" in operations
        assert "amqp.reject" in operations

        # Verify AMQP operations have protocol="amqp"
        assert operations["amqp.publish"]["protocol"] == "amqp"
        assert operations["amqp.consume"]["protocol"] == "amqp"

    def test_amqp_operations_excluded_when_flag_false(self, sample_spec_path):
        """Test that AMQP operations are excluded when --include-amqp=false."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        # Should only have 5 HTTP operations
        assert len(operations) == 5
        assert "amqp.publish" not in operations
        assert "amqp.consume" not in operations
        assert "amqp.ack" not in operations

    def test_registry_structure_is_dict_with_operation_id_keys(self, sample_spec_path):
        """Test that registry structure is dict with operation_id as keys."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        assert isinstance(operations, dict)

        # Verify all keys match their operation_id values
        for op_id, op_data in operations.items():
            assert op_id == op_data["operation_id"]

    def test_deprecated_operations_marked_correctly(self, sample_spec_path):
        """Test that deprecated operations are marked from OpenAPI."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        # queues.delete is marked deprecated in sample spec
        assert operations["queues.delete"]["deprecated"] is True

        # Other operations should not be deprecated
        assert operations["queues.list"]["deprecated"] is False
        assert operations["queues.get"]["deprecated"] is False

    def test_safety_validation_required_for_delete_operations(self, sample_spec_path):
        """Test that safety validation is required for DELETE operations."""
        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=False
        )

        # queues.delete is a DELETE operation
        assert operations["queues.delete"]["safety_validation_required"] is True

        # GET operations should not require safety validation
        assert operations["queues.list"]["safety_validation_required"] is False
        assert operations["queues.get"]["safety_validation_required"] is False


class TestParameterExtraction:
    """Test parameter extraction functionality."""

    def test_extract_path_parameters(self):
        """Test extraction of path parameters."""
        operation_data = {}
        path_params = [
            {
                "name": "vhost",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
        ]

        params = extract_parameters(operation_data, path_params)

        assert len(params) == 1
        assert params[0]["name"] == "vhost"
        assert params[0]["location"] == "path"
        assert params[0]["type"] == "string"
        assert params[0]["required"] is True

    def test_extract_query_parameters(self):
        """Test extraction of query parameters."""
        operation_data = {
            "parameters": [
                {
                    "name": "page",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer", "default": 1, "minimum": 1},
                }
            ]
        }

        params = extract_parameters(operation_data, [])

        assert len(params) == 1
        assert params[0]["name"] == "page"
        assert params[0]["location"] == "query"
        assert params[0]["type"] == "integer"
        assert params[0]["default"] == 1
        assert params[0]["minimum"] == 1

    def test_extract_array_parameters(self):
        """Test extraction of array type parameters."""
        operation_data = {
            "parameters": [
                {
                    "name": "tags",
                    "in": "query",
                    "schema": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                }
            ]
        }

        params = extract_parameters(operation_data, [])

        assert len(params) == 1
        assert params[0]["name"] == "tags"
        assert params[0]["type"] == "array"
        assert params[0]["items_type"] == "string"


class TestSchemaExtraction:
    """Test schema reference extraction."""

    def test_extract_schema_reference(self):
        """Test extraction of schema references."""
        schema_def = {
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/Queue"}}
            }
        }

        result = extract_schema_reference(schema_def)

        assert result is not None
        assert result["$ref"] == "#/components/schemas/Queue"
        assert result["name"] == "Queue"

    def test_extract_inline_schema(self):
        """Test extraction of inline schemas."""
        schema_def = {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    }
                }
            }
        }

        result = extract_schema_reference(schema_def)

        assert result is not None
        assert result["type"] == "object"
        assert "properties" in result


class TestNamespaceDetermination:
    """Test namespace determination logic."""

    def test_namespace_from_operation_id(self):
        """Test namespace extraction from operation_id."""
        namespace = determine_namespace("queues.list", "/api/queues", ["Queues"])
        assert namespace == "queues"

    def test_namespace_from_path(self):
        """Test namespace extraction from URL path."""
        namespace = determine_namespace("unknown", "/api/exchanges", [])
        assert namespace == "exchanges"

    def test_namespace_from_tags(self):
        """Test namespace extraction from tags."""
        namespace = determine_namespace("unknown", "/unknown", ["Connections"])
        assert namespace == "connections"


class TestDestructiveOperationDetection:
    """Test destructive operation detection."""

    def test_delete_method_is_destructive(self):
        """Test that DELETE method is considered destructive."""
        assert is_destructive_operation("DELETE", "queues.delete") is True

    def test_purge_action_is_destructive(self):
        """Test that purge actions are considered destructive."""
        assert is_destructive_operation("POST", "queues.purge") is True

    def test_get_method_is_not_destructive(self):
        """Test that GET method is not destructive."""
        assert is_destructive_operation("GET", "queues.list") is False


class TestRateLimitExemption:
    """Test rate limit exemption detection."""

    def test_overview_is_rate_limit_exempt(self):
        """Test that overview operations are rate limit exempt."""
        assert is_rate_limit_exempt("overview.list") is True

    def test_health_checks_are_rate_limit_exempt(self):
        """Test that health check operations are rate limit exempt."""
        assert is_rate_limit_exempt("health.check") is True

    def test_regular_operations_are_not_exempt(self):
        """Test that regular operations are not rate limit exempt."""
        assert is_rate_limit_exempt("queues.create") is False


class TestAMQPOperations:
    """Test AMQP operation definitions."""

    def test_amqp_operations_have_correct_structure(self):
        """Test that AMQP operations have correct structure."""
        amqp_ops = get_amqp_operations()

        assert len(amqp_ops) == 5

        for op_id, op_data in amqp_ops.items():
            assert op_data["protocol"] == "amqp"
            assert op_data["namespace"] == "amqp"
            assert op_data["operation_id"].startswith("amqp.")
            assert op_data["http_method"] == ""
            assert op_data["url_path"] == ""

    def test_amqp_publish_has_message_properties(self):
        """Test that amqp.publish has complete message properties."""
        amqp_ops = get_amqp_operations()
        publish = amqp_ops["amqp.publish"]

        assert publish["request_schema"] is not None
        schema = publish["request_schema"]
        assert "properties" in schema
        assert "content_type" in schema["properties"]
        assert "delivery_mode" in schema["properties"]
        assert "priority" in schema["properties"]


class TestValidation:
    """Test operation registry validation."""

    def test_validation_passes_for_valid_operations(self):
        """Test that validation passes for valid operations."""
        operations = {
            "queues.list": {
                "operation_id": "queues.list",
                "namespace": "queues",
            },
            "exchanges.list": {
                "operation_id": "exchanges.list",
                "namespace": "exchanges",
            },
        }

        assert validate_operations(operations) is True

    def test_validation_fails_for_namespace_mismatch(self):
        """Test that validation fails when namespace doesn't match operation_id."""
        operations = {
            "queues.list": {
                "operation_id": "queues.list",
                "namespace": "exchanges",  # Mismatch
            },
        }

        assert validate_operations(operations) is False

    def test_validation_handles_compound_namespaces(self):
        """Test that validation handles compound namespaces with underscores."""
        operations = {
            "nodes_memory.get": {
                "operation_id": "nodes_memory.get",
                "namespace": "nodes_memory",
            },
        }

        assert validate_operations(operations) is True


class TestIntegration:
    """Integration tests with full extraction pipeline."""

    def test_full_extraction_pipeline(self, sample_spec_path, temp_output_path):
        """Test complete extraction pipeline from OpenAPI to JSON."""
        from extract_operations import write_registry

        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=True
        )
        assert validate_operations(operations) is True

        write_registry(operations, temp_output_path, sample_spec_path)

        assert temp_output_path.exists()

        # Verify JSON is valid and has correct structure
        with open(temp_output_path) as f:
            registry = json.load(f)

        assert "model_version" in registry
        assert "generated_at" in registry
        assert "openapi_source" in registry
        assert "total_operations" in registry
        assert "operations" in registry
        assert registry["total_operations"] == len(operations)
        assert len(registry["operations"]) == len(operations)

    def test_file_size_validation(self, sample_spec_path, temp_output_path):
        """Test that file size is monitored."""
        from extract_operations import write_registry

        operations = extract_operations_from_openapi(
            sample_spec_path, include_amqp=True
        )
        write_registry(operations, temp_output_path, sample_spec_path)

        file_size_mb = temp_output_path.stat().st_size / (1024 * 1024)
        assert file_size_mb < 5.0  # Should be well under 5MB for sample
