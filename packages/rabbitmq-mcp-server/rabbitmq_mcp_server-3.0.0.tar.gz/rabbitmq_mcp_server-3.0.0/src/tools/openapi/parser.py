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

from typing import Any

import yaml


class OpenAPIParseError(Exception):
    pass


def parse_openapi_spec(path: str) -> dict[str, Any]:
    """
    Loads and validates an OpenAPI 3.1.0 YAML file.
    Returns parsed spec as dict.
    Raises OpenAPIParseError on error.
    """
    try:
        with open(path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        # Basic validation
        if not isinstance(spec, dict):
            raise OpenAPIParseError("Spec root is not a dict")
        if spec.get("openapi", "").split(".")[0] != "3":
            raise OpenAPIParseError("OpenAPI version must be 3.x.x")
        if "paths" not in spec or "components" not in spec:
            raise OpenAPIParseError("Missing required OpenAPI sections: paths/components")
        return spec
    except Exception as e:
        raise OpenAPIParseError(f"Failed to parse OpenAPI spec: {e}")
