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

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


def extract_parameters(
    operation_data: dict[str, Any], path_params: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Extract parameter metadata from operation definition."""
    parameters = []

    # Combine path-level and operation-level parameters
    all_params = list(path_params)
    if "parameters" in operation_data:
        all_params.extend(operation_data["parameters"])

    for param in all_params:
        # Handle $ref parameters
        if "$ref" in param:
            continue

        param_info = {
            "name": param.get("name", ""),
            "location": param.get("in", ""),
            "type": "string",
            "required": param.get("required", False),
            "description": param.get("description", ""),
        }

        # Extract type from schema
        if "schema" in param:
            schema = param["schema"]
            param_info["type"] = schema.get("type", "string")

            # Handle array types
            if param_info["type"] == "array" and "items" in schema:
                param_info["items_type"] = schema["items"].get("type", "string")

            # Extract constraints
            if "default" in schema:
                param_info["default"] = schema["default"]
            if "minimum" in schema:
                param_info["minimum"] = schema["minimum"]
            if "maximum" in schema:
                param_info["maximum"] = schema["maximum"]
            if "minLength" in schema:
                param_info["minLength"] = schema["minLength"]
            if "maxLength" in schema:
                param_info["maxLength"] = schema["maxLength"]
            if "pattern" in schema:
                param_info["pattern"] = schema["pattern"]
            if "enum" in schema:
                param_info["enum"] = schema["enum"]

        parameters.append(param_info)

    return parameters


def extract_schema_reference(
    schema_def: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Extract schema reference or inline schema structure."""
    if not schema_def:
        return None

    if "content" in schema_def:
        content = schema_def["content"]
        if "application/json" in content:
            json_schema = content["application/json"]
            if "schema" in json_schema:
                schema = json_schema["schema"]
                if "$ref" in schema:
                    # Extract schema name from reference
                    ref = str(schema["$ref"])
                    schema_name = ref.split("/")[-1]
                    return {"$ref": ref, "name": schema_name}
                else:
                    # Inline schema
                    return dict(schema)

    return None


def determine_namespace(operation_id: str, path: str, tags: list[str]) -> str:
    """Determine namespace from operation_id, path, or tags."""
    # Extract from operation_id (format: namespace.action or namespace.resource.action)
    if "." in operation_id:
        parts = operation_id.split(".")
        return parts[0]

    # Extract from path (first segment after /api/)
    path_match = re.match(r"^/api/([a-z_-]+)", path)
    if path_match:
        return path_match.group(1).replace("-", "_")

    # Extract from tags
    if tags:
        return tags[0].lower().replace(" ", "_")

    return "unknown"


def is_destructive_operation(http_method: str, operation_id: str) -> bool:
    """Identify if operation is destructive and requires safety validation."""
    if http_method == "DELETE":
        return True

    destructive_actions = ["delete", "purge", "reset", "clear"]
    operation_lower = operation_id.lower()

    return any(action in operation_lower for action in destructive_actions)


def is_rate_limit_exempt(operation_id: str) -> bool:
    """Identify if operation is exempt from rate limiting."""
    exempt_operations = [
        "overview.list",
        "health",
        "aliveness",
        "healthchecks",
        "nodes.list",
    ]

    return any(exempt in operation_id for exempt in exempt_operations)


def extract_operations_from_openapi(
    spec_path: Path, include_amqp: bool = True
) -> dict[str, dict[str, Any]]:
    """Extract operations from OpenAPI specification."""
    with open(spec_path, encoding="utf-8") as f:
        openapi_spec = yaml.safe_load(f)

    operations = {}
    paths = openapi_spec.get("paths", {})

    # Extract HTTP operations from OpenAPI
    for path, path_item in paths.items():
        # Get path-level parameters
        path_params = path_item.get("parameters", [])

        for method in ["get", "post", "put", "delete", "patch"]:
            if method not in path_item:
                continue

            operation = path_item[method]
            operation_id = operation.get("operationId")

            if not operation_id:
                print(f"Warning: Operation {method.upper()} {path} has no operationId")
                continue

            namespace = determine_namespace(
                operation_id, path, operation.get("tags", [])
            )

            # Extract operation metadata
            op_entry = {
                "operation_id": operation_id,
                "namespace": namespace,
                "http_method": method.upper(),
                "url_path": path,
                "description": operation.get(
                    "summary", operation.get("description", "")
                ),
                "parameters": extract_parameters(operation, path_params),
                "request_schema": extract_schema_reference(
                    operation.get("requestBody")
                ),
                "response_schema": extract_schema_reference(
                    operation.get("responses", {}).get("200")
                    or operation.get("responses", {}).get("201")
                ),
                "tags": operation.get("tags", []),
                "requires_auth": True,  # Default for RabbitMQ Management API
                "protocol": "http",
                "deprecated": operation.get("deprecated", False),
                "rate_limit_exempt": is_rate_limit_exempt(operation_id),
                "safety_validation_required": is_destructive_operation(
                    method.upper(), operation_id
                ),
            }

            operations[operation_id] = op_entry

    # Add AMQP operations manually if requested
    if include_amqp:
        amqp_operations = get_amqp_operations()
        operations.update(amqp_operations)

    return operations


def get_amqp_operations() -> dict[str, dict[str, Any]]:
    """Define AMQP operations manually (not in Management API OpenAPI)."""
    amqp_ops: dict[str, dict[str, Any]] = {
        "amqp.publish": {
            "operation_id": "amqp.publish",
            "namespace": "amqp",
            "http_method": "",
            "url_path": "",
            "description": "Publish a message to an exchange using AMQP protocol",
            "parameters": [
                {
                    "name": "exchange",
                    "location": "amqp",
                    "type": "string",
                    "required": True,
                    "description": "Exchange name to publish to",
                },
                {
                    "name": "routing_key",
                    "location": "amqp",
                    "type": "string",
                    "required": True,
                    "description": "Routing key for message routing",
                },
                {
                    "name": "body",
                    "location": "body",
                    "type": "string",
                    "required": True,
                    "description": "Message body (payload)",
                },
                {
                    "name": "properties",
                    "location": "body",
                    "type": "object",
                    "required": False,
                    "description": "Message properties (content_type, delivery_mode, etc.)",
                },
            ],
            "request_schema": {
                "type": "object",
                "properties": {
                    "content_type": {"type": "string"},
                    "delivery_mode": {"type": "integer", "enum": [1, 2]},
                    "priority": {"type": "integer", "minimum": 0, "maximum": 9},
                    "correlation_id": {"type": "string"},
                    "reply_to": {"type": "string"},
                    "expiration": {"type": "string"},
                    "message_id": {"type": "string"},
                    "timestamp": {"type": "integer"},
                    "type": {"type": "string"},
                    "user_id": {"type": "string"},
                    "app_id": {"type": "string"},
                },
            },
            "response_schema": None,
            "tags": ["AMQP"],
            "requires_auth": True,
            "protocol": "amqp",
            "deprecated": False,
            "rate_limit_exempt": False,
            "safety_validation_required": False,
        },
        "amqp.consume": {
            "operation_id": "amqp.consume",
            "namespace": "amqp",
            "http_method": "",
            "url_path": "",
            "description": "Consume messages from a queue using AMQP protocol",
            "parameters": [
                {
                    "name": "queue",
                    "location": "amqp",
                    "type": "string",
                    "required": True,
                    "description": "Queue name to consume from",
                },
                {
                    "name": "consumer_tag",
                    "location": "amqp",
                    "type": "string",
                    "required": False,
                    "description": "Consumer tag identifier",
                },
                {
                    "name": "auto_ack",
                    "location": "amqp",
                    "type": "boolean",
                    "required": False,
                    "description": "Automatically acknowledge messages",
                    "default": False,
                },
                {
                    "name": "exclusive",
                    "location": "amqp",
                    "type": "boolean",
                    "required": False,
                    "description": "Request exclusive consumer access",
                    "default": False,
                },
            ],
            "request_schema": None,
            "response_schema": {
                "type": "object",
                "properties": {
                    "delivery_tag": {"type": "integer"},
                    "body": {"type": "string"},
                    "properties": {"type": "object"},
                },
            },
            "tags": ["AMQP"],
            "requires_auth": True,
            "protocol": "amqp",
            "deprecated": False,
            "rate_limit_exempt": False,
            "safety_validation_required": False,
        },
        "amqp.ack": {
            "operation_id": "amqp.ack",
            "namespace": "amqp",
            "http_method": "",
            "url_path": "",
            "description": "Acknowledge message delivery",
            "parameters": [
                {
                    "name": "delivery_tag",
                    "location": "amqp",
                    "type": "integer",
                    "required": True,
                    "description": "Delivery tag of the message to acknowledge",
                },
                {
                    "name": "multiple",
                    "location": "amqp",
                    "type": "boolean",
                    "required": False,
                    "description": "Acknowledge all messages up to delivery_tag",
                    "default": False,
                },
            ],
            "request_schema": None,
            "response_schema": None,
            "tags": ["AMQP"],
            "requires_auth": True,
            "protocol": "amqp",
            "deprecated": False,
            "rate_limit_exempt": False,
            "safety_validation_required": False,
        },
        "amqp.nack": {
            "operation_id": "amqp.nack",
            "namespace": "amqp",
            "http_method": "",
            "url_path": "",
            "description": "Negatively acknowledge message delivery",
            "parameters": [
                {
                    "name": "delivery_tag",
                    "location": "amqp",
                    "type": "integer",
                    "required": True,
                    "description": "Delivery tag of the message to nack",
                },
                {
                    "name": "multiple",
                    "location": "amqp",
                    "type": "boolean",
                    "required": False,
                    "description": "Nack all messages up to delivery_tag",
                    "default": False,
                },
                {
                    "name": "requeue",
                    "location": "amqp",
                    "type": "boolean",
                    "required": False,
                    "description": "Requeue the message(s)",
                    "default": True,
                },
            ],
            "request_schema": None,
            "response_schema": None,
            "tags": ["AMQP"],
            "requires_auth": True,
            "protocol": "amqp",
            "deprecated": False,
            "rate_limit_exempt": False,
            "safety_validation_required": False,
        },
        "amqp.reject": {
            "operation_id": "amqp.reject",
            "namespace": "amqp",
            "http_method": "",
            "url_path": "",
            "description": "Reject a message delivery",
            "parameters": [
                {
                    "name": "delivery_tag",
                    "location": "amqp",
                    "type": "integer",
                    "required": True,
                    "description": "Delivery tag of the message to reject",
                },
                {
                    "name": "requeue",
                    "location": "amqp",
                    "type": "boolean",
                    "required": False,
                    "description": "Requeue the message",
                    "default": True,
                },
            ],
            "request_schema": None,
            "response_schema": None,
            "tags": ["AMQP"],
            "requires_auth": True,
            "protocol": "amqp",
            "deprecated": False,
            "rate_limit_exempt": False,
            "safety_validation_required": False,
        },
    }

    return amqp_ops


def validate_operations(operations: dict[str, dict[str, Any]]) -> bool:
    """Validate operation registry for duplicates and format consistency."""
    operation_ids = list(operations.keys())

    # Check for duplicate operation IDs
    if len(operation_ids) != len(set(operation_ids)):
        duplicates = [
            op_id for op_id in operation_ids if operation_ids.count(op_id) > 1
        ]
        print(
            f"ERROR: Duplicate operation IDs found: {set(duplicates)}", file=sys.stderr
        )
        return False

    # Validate operation_id format (allow numeric suffixes for duplicate path disambiguation)
    valid_pattern = re.compile(r"^[a-z_]+\.[a-z_]+(\.[a-z_]+)?(_\d+)?$")
    invalid_ids = [op_id for op_id in operation_ids if not valid_pattern.match(op_id)]

    if invalid_ids:
        print(
            f"ERROR: Invalid operation_id format found: {invalid_ids}", file=sys.stderr
        )
        return False

    # Validate namespace consistency
    allowed_namespaces = [
        "queues",
        "exchanges",
        "bindings",
        "messages",
        "connections",
        "users",
        "permissions",
        "nodes",
        "cluster",
        "amqp",
        "overview",
        "vhosts",
        "channels",
        "consumers",
        "definitions",
        "parameters",
        "policies",
        "health",
        "aliveness_test",
        "nodes_memory",
        "connections_channels",
        "cluster_name",
        "feature_flags",
        "deprecated_features",
        "deprecated_features_used",
        "vhosts_connections",
        "connections_username",
        "vhosts_channels",
        "exchanges_bindings_source",
        "exchanges_bindings_destination",
        "exchanges_publish",
        "queues_detailed",
        "queues_bindings",
        "queues_contents",
        "queues_get",
        "bindings_e_q",
        "bindings_e_e",
        "vhosts_permissions",
        "vhosts_topic_permissions",
        "vhosts_deletion_protection",
        "vhosts_start",
        "users_without_permissions",
        "users_bulk_delete",
        "users_permissions",
        "users_topic_permissions",
        "user_limits",
        "topic_permissions",
        "global_parameters",
        "operator_policies",
        "vhost_limits",
        "federation_links",
        "auth_attempts",
        "auth_attempts_source",
        "auth_hash_password",
        "stream_connections",
        "stream_connections_publishers",
        "stream_connections_consumers",
        "stream_publishers",
        "stream_consumers",
        "health_checks_alarms",
        "health_checks_local_alarms",
        "health_checks_certificate_expiration",
        "health_checks_protocol_listener",
        "health_checks_node_is_quorum_critical",
        "health_checks_ready_to_serve_clients",
        "rebalance_queues",
        "whoami",
        "auth",
    ]

    for op_id, op_data in operations.items():
        namespace = op_data.get("namespace", "")
        op_id_namespace = op_id.split(".")[0]

        if namespace != op_id_namespace:
            print(
                f"ERROR: Namespace mismatch for {op_id}: "
                f"namespace={namespace} vs operation_id prefix={op_id_namespace}",
                file=sys.stderr,
            )
            return False

        if namespace not in allowed_namespaces:
            print(
                f"WARNING: Unexpected namespace '{namespace}' for operation {op_id}",
                file=sys.stderr,
            )

    return True


def write_registry(
    operations: dict[str, dict[str, Any]], output_path: Path, spec_path: Path
) -> None:
    """Write operations registry to JSON file with metadata."""
    registry = {
        "model_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "openapi_source": str(spec_path),
        "total_operations": len(operations),
        "operations": operations,
    }

    # Create data directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with pretty formatting
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 5.0:
        print(
            f"WARNING: Registry file size ({file_size_mb:.2f} MB) exceeds 5MB target",
            file=sys.stderr,
        )


def main() -> int:
    """Main entry point for operation extraction script."""
    parser = argparse.ArgumentParser(
        description="Extract RabbitMQ operations from OpenAPI specification"
    )
    parser.add_argument(
        "--spec-path",
        type=Path,
        default=Path("docs-bmad/rabbitmq-http-api-openapi.yaml"),
        help="Path to OpenAPI specification file",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/operations.json"),
        help="Path to output operations registry JSON file",
    )
    parser.add_argument(
        "--include-amqp",
        action="store_true",
        default=True,
        help="Include manually-defined AMQP operations",
    )
    parser.add_argument(
        "--no-include-amqp",
        action="store_false",
        dest="include_amqp",
        help="Exclude AMQP operations",
    )

    args = parser.parse_args()

    if not args.spec_path.exists():
        print(
            f"ERROR: OpenAPI specification not found: {args.spec_path}", file=sys.stderr
        )
        return 1

    print(f"Extracting operations from: {args.spec_path}")

    # Extract operations
    operations = extract_operations_from_openapi(args.spec_path, args.include_amqp)

    # Validate operations
    if not validate_operations(operations):
        return 1

    # Write registry
    write_registry(operations, args.output_path, args.spec_path)

    # Log summary
    namespaces = set(op["namespace"] for op in operations.values())
    http_count = sum(1 for op in operations.values() if op["protocol"] == "http")
    amqp_count = sum(1 for op in operations.values() if op["protocol"] == "amqp")

    print(f"\n✓ Successfully extracted {len(operations)} operations")
    print(f"  - HTTP operations: {http_count}")
    print(f"  - AMQP operations: {amqp_count}")
    print(f"  - Unique namespaces: {len(namespaces)}")
    print(f"  - Output written to: {args.output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
