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

from pathlib import Path
from typing import Any

import yaml

LGPL_HEADER = '''"""
This file is auto-generated from OpenAPI contracts.
LGPL v3.0 applies. See LICENSE in project root.
"""

from pydantic import BaseModel, Field
'''

CONTRACTS_DIR = (
    Path(__file__).parent.parent / "specs" / "003-essential-topology-operations" / "contracts"
)
SCHEMAS_DIR = Path(__file__).parent.parent / "src" / "tools" / "schemas"

# Utility to convert OpenAPI types to Pydantic
OPENAPI_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict",
    "array": "list",
}


def openapi_to_pydantic(name: str, schema: dict[str, Any]) -> str:
    fields = []
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    for prop, details in props.items():
        typ = OPENAPI_TYPE_MAP.get(details.get("type", "string"), "Any")
        default = "..." if prop in required else "None"
        fields.append(f"    {prop}: {typ} = Field({default})")
    return f"class {name}(BaseModel):\n" + "\n".join(fields) + "\n"


def main():
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    for contract_file in CONTRACTS_DIR.glob("*.yaml"):
        with open(contract_file, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        components = spec.get("components", {}).get("schemas", {})
        for name, schema in components.items():
            code = LGPL_HEADER + "\n" + openapi_to_pydantic(name, schema)
            out_path = SCHEMAS_DIR / f"{name.lower()}.py"
            with open(out_path, "w", encoding="utf-8") as out:
                out.write(code)


if __name__ == "__main__":
    main()
