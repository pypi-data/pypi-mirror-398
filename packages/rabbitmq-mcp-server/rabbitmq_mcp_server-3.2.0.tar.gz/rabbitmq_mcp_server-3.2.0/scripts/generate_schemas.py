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
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def should_regenerate(spec_path: Path, output_path: Path, force: bool) -> bool:
    """Check if regeneration is needed based on modification times."""
    if force:
        return True

    if not output_path.exists():
        return True

    spec_mtime = spec_path.stat().st_mtime
    output_mtime = output_path.stat().st_mtime

    return spec_mtime > output_mtime


def inject_rabbitmq_validators(output_path: Path) -> None:
    """Inject RabbitMQ-specific validators into generated code."""
    content = output_path.read_text()

    # Add re import if not present
    if "import re" not in content:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("from pydantic import"):
                lines.insert(i, "import re")
                break
        content = "\n".join(lines)

    # Add field_validator to imports if not present
    if "field_validator" not in content:
        content = content.replace(
            "from pydantic import", "from pydantic import field_validator,"
        )

    # Entity-specific validators with proper field names
    queue_validators = {
        "name": """
    @field_validator('name', mode='after')
    @classmethod
    def validate_queue_name(cls, v: str) -> str:
        if not v or len(v) > 255:
            raise ValueError("Queue name must be 1-255 characters")
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError("Queue name must contain only alphanumeric, underscore, dash, dot")
        return v
""",
        "vhost": """
    @field_validator('vhost', mode='after')
    @classmethod
    def validate_vhost(cls, v: str | None) -> str:
        if not v:
            return "/"
        if not re.match(r'^[a-zA-Z0-9/_-]+$', v):
            raise ValueError("Vhost must contain only URL-safe characters")
        return v
""",
        "durable": """
    @field_validator('durable', mode='after')
    @classmethod
    def validate_durable(cls, v: bool | None) -> bool:
        if v is None:
            return True
        if not isinstance(v, bool):
            raise TypeError("Durable must be a boolean")
        return v
""",
    }

    exchange_validators = {
        "name": """
    @field_validator('name', mode='after')
    @classmethod
    def validate_exchange_name(cls, v: str) -> str:
        if not v or len(v) > 255:
            raise ValueError("Exchange name must be 1-255 characters")
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError("Exchange name must contain only alphanumeric, underscore, dash, dot")
        return v
""",
        "type": """
    @field_validator('type', mode='after')
    @classmethod
    def validate_exchange_type(cls, v: str) -> str:
        valid_types = {"direct", "fanout", "topic", "headers"}
        if v not in valid_types:
            raise ValueError(f"Exchange type must be one of: {', '.join(valid_types)}")
        return v
""",
        "vhost": queue_validators["vhost"],
        "durable": queue_validators["durable"],
    }

    # Map of class patterns to their validators
    entity_validators = {
        "Queue": queue_validators,
        "Exchange": exchange_validators,
    }

    # Split content into lines for safer processing
    lines = content.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # Check if this is a class definition
        if line.strip().startswith("class ") and "(BaseModel)" in line:
            # Extract class name
            class_name_match = line.strip().split()[1].rstrip(":").split("(")[0]

            # Collect the entire class body
            indent_level = len(line) - len(line.lstrip())
            class_lines = [line]
            i += 1

            # Collect all lines that belong to this class
            while i < len(lines):
                next_line = lines[i]
                # Check if we've reached the end of the class
                if (
                    next_line.strip()
                    and not next_line.startswith(" " * (indent_level + 1))
                    and not next_line.strip().startswith("#")
                ):
                    # This line is not part of the class anymore
                    break
                class_lines.append(next_line)
                i += 1

            # Determine which validators to add based on entity type
            class_text = "\n".join(class_lines)
            validators_to_add = []

            # Match entity type to appropriate validators
            applicable_validators = None
            for entity_pattern, validators_dict in entity_validators.items():
                if entity_pattern.lower() in class_name_match.lower():
                    applicable_validators = validators_dict
                    break

            # Only add validators if entity type matches
            if applicable_validators:
                for field_name, validator_code in applicable_validators.items():
                    # Check if field exists in THIS class and validator not already present
                    field_pattern = f"{field_name}:"
                    if field_pattern in class_text or f"{field_name} =" in class_text:
                        validator_func_name = "validate_" + (
                            "exchange_type"
                            if field_name == "type" and "Exchange" in class_name_match
                            else (
                                "exchange_name"
                                if field_name == "name"
                                and "Exchange" in class_name_match
                                else (
                                    "queue_name" if field_name == "name" else field_name
                                )
                            )
                        )
                        if validator_func_name not in class_text:
                            validators_to_add.append(validator_code)

            # Add validators at the end of the class
            if validators_to_add:
                # Remove the last line we added (it will be part of class_lines)
                result_lines.pop()
                result_lines.extend(class_lines[:-1])
                for validator in validators_to_add:
                    result_lines.append(validator)
                # Add the empty line that separates classes
                if class_lines[-1].strip() == "":
                    result_lines.append("")
            else:
                # Just add the rest of the class lines
                result_lines.extend(class_lines[1:])

            continue

        i += 1

    output_path.write_text("\n".join(result_lines))


def count_models_in_openapi(spec_path: Path) -> int:
    """Count component schemas in OpenAPI file."""
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    return len(spec.get("components", {}).get("schemas", {}))


def main() -> int:
    """Generate Pydantic models from OpenAPI specification."""
    parser = argparse.ArgumentParser(
        description="Generate Pydantic models from OpenAPI specification"
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
        default=Path("src/schemas/generated_schemas.py"),
        help="Path to output generated schemas file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if OpenAPI unchanged",
    )
    args = parser.parse_args()

    # Resolve paths relative to project root (if not absolute)
    project_root = Path(__file__).parent.parent
    if not args.spec_path.is_absolute():
        spec_path = project_root / args.spec_path
    else:
        spec_path = args.spec_path

    if not args.output_path.is_absolute():
        output_path = project_root / args.output_path
    else:
        output_path = args.output_path

    # Validate input file exists
    if not spec_path.exists():
        print(f"Error: OpenAPI specification not found at {spec_path}", file=sys.stderr)
        return 1

    # Check if regeneration needed
    if not should_regenerate(spec_path, output_path, args.force):
        spec_mtime = datetime.fromtimestamp(spec_path.stat().st_mtime)
        print(f"Generated schemas are up-to-date (OpenAPI mtime: {spec_mtime})")
        return 0

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Count schemas before generation
    schema_count = count_models_in_openapi(spec_path)

    # Generate using datamodel-code-generator
    try:
        relative_spec_path = spec_path.relative_to(project_root)
    except ValueError:
        relative_spec_path = spec_path

    print(f"Generating Pydantic models from {relative_spec_path}...")

    result = subprocess.run(
        [
            "datamodel-codegen",
            "--input",
            str(spec_path),
            "--output",
            str(output_path),
            "--input-file-type",
            "openapi",
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--use-standard-collections",
            "--use-schema-description",
            "--field-constraints",
            "--use-default",
            "--strict-nullable",
            "--use-annotated",
            "--snake-case-field",
            "--enable-faux-immutability",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error generating schemas:\n{result.stderr}", file=sys.stderr)
        return 1

    # Add file header
    timestamp = datetime.now().isoformat()
    try:
        relative_spec_path = spec_path.relative_to(project_root)
    except ValueError:
        relative_spec_path = spec_path

    header = f"""# Auto-generated from OpenAPI - DO NOT EDIT MANUALLY
# Generated: {timestamp}
# Source: {relative_spec_path}

"""

    content = output_path.read_text()
    output_path.write_text(header + content)

    # Inject RabbitMQ-specific validators
    inject_rabbitmq_validators(output_path)

    # Format with black
    subprocess.run(
        ["black", str(output_path), "--quiet"],
        check=False,
    )

    # Run mypy validation
    print("Validating generated code with mypy...")
    mypy_result = subprocess.run(
        ["mypy", "--strict", str(output_path)],
        capture_output=True,
        text=True,
    )

    if mypy_result.returncode != 0:
        print("Warning: Generated code has type errors:", file=sys.stderr)
        print(mypy_result.stdout, file=sys.stderr)
        print(
            "\nGeneration completed but manual inspection recommended.", file=sys.stderr
        )
    else:
        print("✓ Generated code passes mypy --strict validation")

    try:
        relative_output_path = output_path.relative_to(project_root)
    except ValueError:
        relative_output_path = output_path

    print(f"✓ Generated {schema_count} Pydantic models → {relative_output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
