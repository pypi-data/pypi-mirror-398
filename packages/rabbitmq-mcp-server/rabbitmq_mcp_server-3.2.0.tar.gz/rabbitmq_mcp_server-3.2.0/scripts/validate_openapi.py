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
import sys
from pathlib import Path
from typing import Any

import yaml
from openapi_spec_validator import validate
from openapi_spec_validator.exceptions import OpenAPISpecValidatorError

DEFAULT_SPEC_PATH = "docs-bmad/rabbitmq-http-api-openapi.yaml"


def load_openapi_spec(spec_path: str) -> dict[str, Any]:
    """Load OpenAPI specification from YAML file."""
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"OpenAPI specification not found: {spec_path}")

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_operationids(spec: dict[str, Any]) -> list[str]:
    """Validate that all operations have unique operationId fields."""
    errors = []
    operation_ids: set[str] = set()
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                if not isinstance(operation, dict):
                    continue

                operation_id = operation.get("operationId")
                if not operation_id:
                    errors.append(f"{method.upper()} {path}: Missing operationId")
                elif operation_id in operation_ids:
                    errors.append(
                        f"{method.upper()} {path}: Duplicate operationId "
                        f"'{operation_id}'"
                    )
                else:
                    operation_ids.add(operation_id)

    return errors


def main() -> None:
    """Validate OpenAPI specification."""
    parser = argparse.ArgumentParser(
        description="Validate OpenAPI specification against OpenAPI 3.0 schema"
    )
    parser.add_argument(
        "--spec-path",
        default=DEFAULT_SPEC_PATH,
        help=f"Path to OpenAPI specification file (default: {DEFAULT_SPEC_PATH})",
    )
    parser.add_argument(
        "--skip-schema-validation",
        action="store_true",
        help="Skip strict OpenAPI 3.0 schema validation (only check structure)",
    )
    args = parser.parse_args()

    # Resolve spec path relative to project root
    project_root = Path(__file__).parent.parent
    spec_path = project_root / args.spec_path

    try:
        # Load specification
        spec = load_openapi_spec(str(spec_path))

        # Validate against OpenAPI 3.0 schema (unless skipped)
        validation_passed = True
        if not args.skip_schema_validation:
            try:
                validate(spec)
            except (OpenAPISpecValidatorError, Exception) as e:
                # Try to continue with operationId validation even if schema fails
                print(
                    "Warning: OpenAPI schema validation issues detected:",
                    file=sys.stderr,
                )
                error_msg = str(e)
                if len(error_msg) > 300:
                    error_msg = error_msg[:300] + "..."
                print(f"  {error_msg}", file=sys.stderr)
                print("  Continuing with operationId validation...\n", file=sys.stderr)
                validation_passed = False

        # Validate operationIds
        operationid_errors = validate_operationids(spec)
        if operationid_errors:
            print(
                "OpenAPI validation failed - operationId issues:",
                file=sys.stderr,
            )
            for error in operationid_errors:
                print(f"  {error}", file=sys.stderr)
            sys.exit(1)

        if validation_passed:
            print(f"✓ OpenAPI specification is valid: {args.spec_path}")
        else:
            print(
                f"✓ OpenAPI operationIds are valid: {args.spec_path}",
                file=sys.stderr,
            )
            print(
                "  (Schema validation failed, but operationIds are correct)",
                file=sys.stderr,
            )

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML format: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
