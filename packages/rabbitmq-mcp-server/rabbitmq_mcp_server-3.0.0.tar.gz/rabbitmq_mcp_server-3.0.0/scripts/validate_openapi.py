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
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.openapi.parser import OpenAPIParseError, parse_openapi_spec

CONTRACTS_DIR = (
    Path(__file__).parent.parent / "specs" / "003-essential-topology-operations" / "contracts"
)

errors = []
for contract_file in CONTRACTS_DIR.glob("*.yaml"):
    try:
        parse_openapi_spec(str(contract_file))
    except OpenAPIParseError as e:
        errors.append(f"{contract_file}: {e}")

if errors:
    print("OpenAPI validation failed:")
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print("All OpenAPI contracts are valid.")
