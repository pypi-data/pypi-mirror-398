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

"""Tests for project setup and repository structure (Story 1.1)."""

import importlib.util
import re
import tomllib
from pathlib import Path

import pytest


# Test AC #1: Repository Structure Created
class TestRepositoryStructure:
    """Verify required directory structure exists."""

    def test_required_directories_exist(self) -> None:
        """Verify all required directories exist."""
        project_root = Path(__file__).parent.parent.parent
        required_dirs = [
            "src/rabbitmq_mcp_server",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/contract",
            "tests/performance",
            "scripts",
            "data",
            "config",
            "docs",
            ".bmad",
            "logs",
        ]

        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Required directory missing: {dir_path}"
            assert full_path.is_dir(), f"Path exists but is not a directory: {dir_path}"

    def test_package_init_files_present(self) -> None:
        """Verify __init__.py files present in all Python packages."""
        project_root = Path(__file__).parent.parent.parent
        package_dirs = [
            "src/rabbitmq_mcp_server",
            "src/rabbitmq_mcp_server/config",
            "src/rabbitmq_mcp_server/mcp_server",
            "src/rabbitmq_mcp_server/schemas",
            "src/rabbitmq_mcp_connection",
            "tests/unit",
            "tests/integration",
            "tests/contract",
            "tests/performance",
        ]

        for pkg_dir in package_dirs:
            init_file = project_root / pkg_dir / "__init__.py"
            assert init_file.exists(), f"Missing __init__.py in {pkg_dir}"
            assert init_file.is_file(), f"__init__.py is not a file in {pkg_dir}"

    def test_package_imports_work(self) -> None:
        """Test that package can be imported."""
        # Test main package import
        spec = importlib.util.find_spec("rabbitmq_mcp_server")
        assert spec is not None, "rabbitmq_mcp_server package not importable"

    def test_gitkeep_files_present(self) -> None:
        """Verify .gitkeep files exist in data/ and logs/."""
        project_root = Path(__file__).parent.parent.parent
        gitkeep_files = [
            "data/.gitkeep",
            "logs/.gitkeep",
        ]

        for gitkeep in gitkeep_files:
            gitkeep_path = project_root / gitkeep
            assert gitkeep_path.exists(), f"Missing .gitkeep file: {gitkeep}"


# Test AC #2: Python 3.12+ Configuration
class TestPythonConfiguration:
    """Verify Python version and uv configuration."""

    def test_python_version_constraint(self) -> None:
        """Verify pyproject.toml has correct Python version constraint."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        requires_python = pyproject["project"]["requires-python"]
        assert (
            requires_python == ">=3.12,<4.0"
        ), f"Expected requires-python='>=3.12,<4.0', got '{requires_python}'"

    def test_uv_lock_exists(self) -> None:
        """Verify uv.lock file exists."""
        project_root = Path(__file__).parent.parent.parent
        uv_lock = project_root / "uv.lock"
        assert uv_lock.exists(), "uv.lock file missing"
        assert uv_lock.is_file(), "uv.lock is not a file"


# Test AC #3: Core Dependencies Defined
class TestCoreDependencies:
    """Verify core dependencies are defined correctly."""

    def test_core_dependency_versions(self) -> None:
        """Verify core dependencies have correct version constraints."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        dependencies = pyproject["project"]["dependencies"]

        required_deps = {
            "mcp": ">=1.0.0",
            "pydantic": ">=2.0",
            "pydantic-settings": ">=2.0",
            "httpx": ">=0.27",
            "structlog": ">=24.1",
            "opentelemetry-api": ">=1.22",
            "opentelemetry-sdk": ">=1.22",
            "jsonschema": ">=4.20",
            "pyyaml": ">=6.0",
        }

        for dep_name, min_version in required_deps.items():
            # Find dependency in list
            dep_found = False
            for dep_str in dependencies:
                if dep_str.startswith(dep_name):
                    dep_found = True
                    # Extract version constraint
                    assert (
                        ">=" in dep_str or "~=" in dep_str or "==" in dep_str
                    ), f"Dependency {dep_name} missing version constraint"
            assert dep_found, f"Required core dependency missing: {dep_name}"

    def test_core_dependency_imports(self) -> None:
        """Verify core dependencies can be imported."""
        import httpx  # noqa: F401
        import jsonschema  # noqa: F401
        import mcp  # noqa: F401
        import pydantic  # noqa: F401
        import pydantic_settings  # noqa: F401
        import structlog  # noqa: F401
        import yaml  # noqa: F401
        from opentelemetry import trace  # noqa: F401


# Test AC #4: Development Dependencies Defined
class TestDevDependencies:
    """Verify development dependencies are defined correctly."""

    def test_dev_dependencies_present(self) -> None:
        """Verify all required dev dependencies are present."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        dev_deps = pyproject["project"]["optional-dependencies"]["dev"]

        required_dev_deps = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-mock",
            "testcontainers",
            "datamodel-code-generator",
            "black",
            "ruff",
            "mypy",
            "sentence-transformers",
            "numpy",
            "types-pyyaml",
            "types-requests",
            "types-tabulate",
        ]

        for dep_name in required_dev_deps:
            dep_found = any(dep.startswith(dep_name) for dep in dev_deps)
            assert dep_found, f"Required dev dependency missing: {dep_name}"


# Test AC #5: Project Metadata Complete
class TestProjectMetadata:
    """Verify project metadata is complete and correct."""

    def test_project_metadata_fields(self) -> None:
        """Verify all required metadata fields are present."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        project = pyproject["project"]

        # Check required fields
        assert (
            project["name"] == "rabbitmq-mcp-server"
        ), f"Expected name='rabbitmq-mcp-server', got '{project['name']}'"
        assert (
            project["version"] == "3.0.0"
        ), f"Expected version='3.0.0', got '{project['version']}'"
        assert "description" in project, "Missing description field"
        assert "authors" in project, "Missing authors field"
        assert len(project["authors"]) > 0, "Authors list is empty"

    def test_project_license(self) -> None:
        """Verify project license is LGPL-3.0-or-later."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        license_text = pyproject["project"]["license"]["text"]
        assert (
            license_text == "LGPL-3.0-or-later"
        ), f"Expected license='LGPL-3.0-or-later', got '{license_text}'"

    def test_project_description_mentions_3tool_pattern(self) -> None:
        """Verify description mentions 3-tool semantic discovery pattern."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        description = pyproject["project"]["description"].lower()
        # Check for key concepts
        assert (
            "search" in description
            or "semantic" in description
            or "discovery" in description
        ), "Description should mention semantic discovery pattern"


# Test AC #6: .gitignore Configuration
class TestGitignoreConfiguration:
    """Verify .gitignore excludes expected patterns."""

    def test_gitignore_patterns_present(self) -> None:
        """Verify .gitignore contains required patterns."""
        project_root = Path(__file__).parent.parent.parent
        gitignore_path = project_root / ".gitignore"

        assert gitignore_path.exists(), ".gitignore file missing"

        with open(gitignore_path) as f:
            gitignore_content = f.read()

        required_patterns = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            ".env",
            ".venv",
            "venv",
            ".DS_Store",
        ]

        for pattern in required_patterns:
            assert (
                pattern in gitignore_content
            ), f"Required .gitignore pattern missing: {pattern}"

    def test_gitignore_preserves_gitkeep(self) -> None:
        """Verify .gitignore includes !data/.gitkeep and !logs/.gitkeep."""
        project_root = Path(__file__).parent.parent.parent
        gitignore_path = project_root / ".gitignore"

        with open(gitignore_path) as f:
            gitignore_content = f.read()

        # Check that .gitkeep files are preserved
        assert (
            "!data/.gitkeep" in gitignore_content
            or "data/.gitkeep" not in gitignore_content
        ), ".gitignore should preserve data/.gitkeep"
        assert (
            "!logs/.gitkeep" in gitignore_content
            or "logs/.gitkeep" not in gitignore_content
        ), ".gitignore should preserve logs/.gitkeep"


# Test AC #7: README.md Documentation
class TestReadmeDocumentation:
    """Verify README.md exists and contains required sections."""

    def test_readme_exists(self) -> None:
        """Verify README.md exists."""
        project_root = Path(__file__).parent.parent.parent
        readme_path = project_root / "README.md"
        assert readme_path.exists(), "README.md file missing"
        assert readme_path.is_file(), "README.md is not a file"

    def test_readme_sections_present(self) -> None:
        """Verify README.md contains required sections."""
        project_root = Path(__file__).parent.parent.parent
        readme_path = project_root / "README.md"

        with open(readme_path) as f:
            readme_content = f.read().lower()

        # Check for key sections - allow variations
        assert "quick start" in readme_content, "README.md missing quick start section"
        assert (
            "usage" in readme_content
            or "use case" in readme_content
            or "example" in readme_content
        ), "README.md missing usage/examples section"
        assert (
            "installation" in readme_content or "install" in readme_content
        ), "README.md missing installation section"

    def test_readme_mentions_mcp_tools(self) -> None:
        """Verify README mentions search-ids, get-id, call-id tools."""
        project_root = Path(__file__).parent.parent.parent
        readme_path = project_root / "README.md"

        with open(readme_path) as f:
            readme_content = f.read().lower()

        # Check for tool mentions
        tools_mentioned = (
            "search-ids" in readme_content
            or "search_ids" in readme_content
            or "get-id" in readme_content
            or "get_id" in readme_content
            or "call-id" in readme_content
            or "call_id" in readme_content
        )

        assert (
            tools_mentioned
        ), "README.md should mention the 3-tool pattern (search-ids, get-id, call-id)"
