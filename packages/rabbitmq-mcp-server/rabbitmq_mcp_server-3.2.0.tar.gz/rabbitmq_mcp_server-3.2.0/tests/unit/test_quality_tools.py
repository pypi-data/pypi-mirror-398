"""Tests for Story 1.2: Development Quality Tools & CI/CD Pipeline.

This module validates that all quality tools are properly configured and function
as expected according to acceptance criteria.
"""

import os
import subprocess
from pathlib import Path

import pytest
import yaml


class TestPrecommitConfiguration:
    """Test AC #1: Pre-commit Configuration Created."""

    def test_precommit_config_exists(self):
        """Verify .pre-commit-config.yaml file exists in repository root."""
        config_path = Path(".pre-commit-config.yaml")
        assert config_path.exists(), ".pre-commit-config.yaml not found"

    def test_precommit_config_has_required_hooks(self):
        """Verify configured hooks: black, isort, mypy, ruff."""
        config_path = Path(".pre-commit-config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Extract hook IDs from repos
        hook_ids = []
        for repo in config.get("repos", []):
            for hook in repo.get("hooks", []):
                hook_ids.append(hook["id"])

        assert "black" in hook_ids, "black hook not configured"
        assert "isort" in hook_ids, "isort hook not configured"
        assert "mypy" in hook_ids, "mypy hook not configured"
        assert "ruff" in hook_ids, "ruff hook not configured"

    def test_precommit_hooks_have_pinned_versions(self):
        """Verify each hook has pinned version in configuration."""
        config_path = Path(".pre-commit-config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        for repo in config.get("repos", []):
            assert "rev" in repo, f"Repository {repo.get('repo')} missing 'rev' field"
            assert repo["rev"], f"Repository {repo.get('repo')} has empty 'rev' field"

    def test_black_hook_configuration(self):
        """Verify black hook has correct args (line-length: 88, target-version: py312)."""
        config_path = Path(".pre-commit-config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        black_repo = None
        for repo in config.get("repos", []):
            if "black" in repo.get("repo", ""):
                black_repo = repo
                break

        assert black_repo is not None, "Black repository not found"

        black_hook = None
        for hook in black_repo.get("hooks", []):
            if hook["id"] == "black":
                black_hook = hook
                break

        assert black_hook is not None, "Black hook not found"
        assert "--line-length=88" in black_hook.get(
            "args", []
        ), "Black line-length not set to 88"
        assert "--target-version=py312" in black_hook.get(
            "args", []
        ), "Black target-version not set to py312"

    def test_isort_hook_configuration(self):
        """Verify isort hook has correct args (profile: black)."""
        config_path = Path(".pre-commit-config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        isort_repo = None
        for repo in config.get("repos", []):
            if "isort" in repo.get("repo", ""):
                isort_repo = repo
                break

        assert isort_repo is not None, "isort repository not found"

        isort_hook = None
        for hook in isort_repo.get("hooks", []):
            if hook["id"] == "isort":
                isort_hook = hook
                break

        assert isort_hook is not None, "isort hook not found"
        assert "--profile=black" in isort_hook.get(
            "args", []
        ), "isort profile not set to black"

    def test_mypy_hook_configuration(self):
        """Verify mypy hook has additional dependencies configured."""
        config_path = Path(".pre-commit-config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        mypy_repo = None
        for repo in config.get("repos", []):
            if "mypy" in repo.get("repo", ""):
                mypy_repo = repo
                break

        assert mypy_repo is not None, "mypy repository not found"

        mypy_hook = None
        for hook in mypy_repo.get("hooks", []):
            if hook["id"] == "mypy":
                mypy_hook = hook
                break

        assert mypy_hook is not None, "mypy hook not found"
        assert (
            "additional_dependencies" in mypy_hook
        ), "mypy hook missing additional_dependencies"
        deps = mypy_hook["additional_dependencies"]
        assert any(
            "pydantic" in dep for dep in deps
        ), "pydantic not in mypy additional_dependencies"


class TestPrecommitHooksFunctionality:
    """Test AC #2: Pre-commit Hooks Function Correctly."""

    def test_precommit_can_be_installed(self):
        """Verify hooks can be installed via 'pre-commit install' command."""
        result = subprocess.run(
            ["uv", "run", "pre-commit", "install", "--install-hooks"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"pre-commit install failed: {result.stderr}"

    def test_precommit_hooks_run_on_all_files(self):
        """Verify hooks run with 'pre-commit run --all-files'."""
        result = subprocess.run(
            ["uv", "run", "pre-commit", "run", "--all-files", "--show-diff-on-failure"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        # Note: This may fail if code needs formatting, but verifies hooks run
        assert (
            "black" in result.stdout or "black" in result.stderr
        ), "black hook did not run"
        assert (
            "isort" in result.stdout or "isort" in result.stderr
        ), "isort hook did not run"
        assert (
            "ruff" in result.stdout or "ruff" in result.stderr
        ), "ruff hook did not run"


class TestGitHubActionsCIWorkflow:
    """Test AC #3: GitHub Actions CI/CD Pipeline Created."""

    def test_ci_workflow_file_exists(self):
        """Verify .github/workflows/ci.yml file exists."""
        workflow_path = Path(".github/workflows/ci.yml")
        assert workflow_path.exists(), ".github/workflows/ci.yml not found"

    def test_ci_workflow_has_correct_triggers(self):
        """Verify pipeline triggers on: pull_request, push to main."""
        workflow_path = Path(".github/workflows/ci.yml")
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        assert "on" in workflow or True in workflow, "Workflow missing 'on' triggers"
        on_config = workflow.get("on", workflow.get(True, {}))

        assert "pull_request" in on_config, "Missing pull_request trigger"
        assert "push" in on_config, "Missing push trigger"

        # Check branches for pull_request
        pr_config = on_config["pull_request"]
        if isinstance(pr_config, dict):
            assert "main" in pr_config.get(
                "branches", []
            ), "pull_request not configured for main branch"

        # Check branches for push
        push_config = on_config["push"]
        if isinstance(push_config, dict):
            assert "main" in push_config.get(
                "branches", []
            ), "push not configured for main branch"

    def test_ci_workflow_has_python_matrix(self):
        """Verify workflow runs on multiple Python versions: 3.12 and 3.13."""
        workflow_path = Path(".github/workflows/ci.yml")
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get("jobs", {})
        assert jobs, "Workflow has no jobs"

        # Find first job with matrix
        matrix_found = False
        for job_name, job_config in jobs.items():
            strategy = job_config.get("strategy", {})
            matrix = strategy.get("matrix", {})
            if "python-version" in matrix:
                matrix_found = True
                python_versions = matrix["python-version"]
                assert "3.12" in python_versions, "Python 3.12 not in matrix"
                assert "3.13" in python_versions, "Python 3.13 not in matrix"
                break

        assert matrix_found, "No Python version matrix found in workflow"

    def test_ci_workflow_includes_required_steps(self):
        """Verify workflow includes: checkout, setup, install, test, lint, type check."""
        workflow_path = Path(".github/workflows/ci.yml")
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get("jobs", {})
        assert jobs, "Workflow has no jobs"

        # Get first job steps
        first_job = list(jobs.values())[0]
        steps = first_job.get("steps", [])

        step_names = [step.get("name", "").lower() for step in steps]
        step_uses = [step.get("uses", "").lower() for step in steps]
        step_runs = [step.get("run", "").lower() for step in steps]

        # Check for required steps
        assert any(
            "checkout" in name or "checkout" in use
            for name, use in zip(step_names, step_uses)
        ), "Missing checkout step"
        assert any(
            "python" in name or "python" in use
            for name, use in zip(step_names, step_uses)
        ), "Missing Python setup step"
        assert any(
            "uv sync" in run or "install" in name
            for name, run in zip(step_names, step_runs)
        ), "Missing dependency install step"
        assert any(
            "pytest" in run or "test" in name
            for name, run in zip(step_names, step_runs)
        ), "Missing test step"
        assert any(
            "ruff" in run or "lint" in name for name, run in zip(step_names, step_runs)
        ), "Missing linting step"
        assert any(
            "mypy" in run or "type check" in name
            for name, run in zip(step_names, step_runs)
        ), "Missing type checking step"

    def test_ci_workflow_has_caching(self):
        """Verify workflow uses caching for dependencies (actions/cache)."""
        workflow_path = Path(".github/workflows/ci.yml")
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get("jobs", {})
        first_job = list(jobs.values())[0]
        steps = first_job.get("steps", [])

        # Check for cache action
        cache_found = any("actions/cache" in step.get("uses", "") for step in steps)
        assert cache_found, "No caching configured in workflow"


class TestCIQualityGates:
    """Test AC #4: CI/CD Quality Gates Enforced."""

    def test_coverage_threshold_configured(self):
        """Verify coverage threshold >80% in pyproject.toml."""
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        pytest_config = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
        addopts = pytest_config.get("addopts", "")

        assert (
            "--cov-fail-under=80" in addopts
        ), "Coverage threshold not set to 80% in pytest config"

    def test_ci_steps_have_continue_on_error_false(self):
        """Verify CI steps fail on error (continue-on-error: false)."""
        workflow_path = Path(".github/workflows/ci.yml")
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get("jobs", {})
        first_job = list(jobs.values())[0]
        steps = first_job.get("steps", [])

        # Check critical steps don't have continue-on-error: true
        for step in steps:
            step_run = step.get("run", "")
            if any(cmd in step_run for cmd in ["pytest", "ruff check", "mypy"]):
                continue_on_error = step.get("continue-on-error", False)
                assert (
                    continue_on_error is False
                ), f"Step '{step.get('name')}' has continue-on-error: true"


class TestToolConfiguration:
    """Test AC #6: Development Tool Configuration."""

    def test_pyproject_has_black_config(self):
        """Verify [tool.black] section with line-length=88, target-version=['py312']."""
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        black_config = config.get("tool", {}).get("black", {})
        assert black_config, "[tool.black] section not found"
        assert black_config.get("line-length") == 88, "Black line-length not set to 88"
        assert "py312" in black_config.get(
            "target-version", []
        ), "Black target-version missing py312"

    def test_pyproject_has_isort_config(self):
        """Verify [tool.isort] section with profile='black'."""
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        isort_config = config.get("tool", {}).get("isort", {})
        assert isort_config, "[tool.isort] section not found"
        assert (
            isort_config.get("profile") == "black"
        ), "isort profile not set to 'black'"
        assert isort_config.get("line_length") == 88, "isort line_length not set to 88"

    def test_pyproject_has_ruff_config(self):
        """Verify [tool.ruff] section with correct rule selection."""
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        ruff_config = config.get("tool", {}).get("ruff", {})
        assert ruff_config, "[tool.ruff] section not found"
        assert ruff_config.get("line-length") == 88, "Ruff line-length not set to 88"
        assert (
            ruff_config.get("target-version") == "py312"
        ), "Ruff target-version not set to py312"

        ruff_lint = ruff_config.get("lint", {})
        selected_rules = ruff_lint.get("select", [])
        assert "E" in selected_rules, "Ruff missing 'E' rule category"
        assert "F" in selected_rules, "Ruff missing 'F' rule category"
        assert "I" in selected_rules, "Ruff missing 'I' rule category"

    def test_pyproject_has_mypy_config(self):
        """Verify [tool.mypy] section with strict=true and required settings."""
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        mypy_config = config.get("tool", {}).get("mypy", {})
        assert mypy_config, "[tool.mypy] section not found"
        assert mypy_config.get("strict") is True, "mypy strict mode not enabled"
        assert (
            mypy_config.get("disallow_untyped_defs") is True
        ), "mypy disallow_untyped_defs not enabled"
        assert (
            mypy_config.get("warn_return_any") is True
        ), "mypy warn_return_any not enabled"

    def test_pyproject_has_pytest_config(self):
        """Verify [tool.pytest.ini_options] section with coverage settings."""
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        pytest_config = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
        assert pytest_config, "[tool.pytest.ini_options] section not found"
        assert (
            pytest_config.get("asyncio_mode") == "auto"
        ), "pytest asyncio_mode not set to 'auto'"
        assert pytest_config.get("testpaths") == [
            "tests"
        ], "pytest testpaths not set to ['tests']"

        addopts = pytest_config.get("addopts", "")
        assert "--cov=" in addopts, "pytest coverage not configured"
        assert (
            "--cov-report=term-missing" in addopts
        ), "pytest missing term-missing coverage report"
        assert "--cov-report=xml" in addopts, "pytest missing xml coverage report"

    def test_pyproject_has_coverage_config(self):
        """Verify [tool.coverage.run] and [tool.coverage.report] sections."""
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        coverage_config = config.get("tool", {}).get("coverage", {})
        assert coverage_config, "[tool.coverage] section not found"

        run_config = coverage_config.get("run", {})
        assert run_config, "[tool.coverage.run] section not found"
        assert "source" in run_config, "coverage source not configured"

        report_config = coverage_config.get("report", {})
        assert report_config, "[tool.coverage.report] section not found"
        assert "exclude_lines" in report_config, "coverage exclude_lines not configured"


class TestDocumentationUpdated:
    """Test AC #7: Documentation Updated."""

    def test_readme_has_development_section(self):
        """Verify README.md includes Development Workflow or Contributing section."""
        readme_path = Path("README.md")
        with open(readme_path) as f:
            content = f.read().lower()

        assert (
            "development" in content or "contributing" in content
        ), "README.md missing Development/Contributing section"

    def test_readme_documents_precommit_installation(self):
        """Verify README documents how to install pre-commit hooks."""
        readme_path = Path("README.md")
        with open(readme_path) as f:
            content = f.read().lower()

        assert (
            "pre-commit install" in content
        ), "README.md missing pre-commit installation instructions"

    def test_readme_documents_quality_checks(self):
        """Verify README documents how to run quality checks locally."""
        readme_path = Path("README.md")
        with open(readme_path) as f:
            content = f.read().lower()

        assert "black" in content, "README.md missing black documentation"
        assert "ruff" in content, "README.md missing ruff documentation"
        assert "mypy" in content, "README.md missing mypy documentation"

    def test_readme_documents_ci_pipeline(self):
        """Verify README documents CI/CD pipeline behavior and quality gates."""
        readme_path = Path("README.md")
        with open(readme_path) as f:
            content = f.read().lower()

        assert (
            "ci/cd" in content or "ci" in content
        ), "README.md missing CI/CD documentation"
        assert (
            "quality gate" in content or "coverage" in content
        ), "README.md missing quality gates documentation"

    def test_gitignore_excludes_coverage_files(self):
        """Verify .gitignore excludes coverage files (.coverage, htmlcov/, coverage.xml)."""
        gitignore_path = Path(".gitignore")
        with open(gitignore_path) as f:
            content = f.read()

        assert ".coverage" in content, ".gitignore missing .coverage"
        assert "htmlcov/" in content, ".gitignore missing htmlcov/"
        assert "coverage.xml" in content, ".gitignore missing coverage.xml"

    def test_gitignore_excludes_dist(self):
        """Verify .gitignore excludes dist/ (from Story 1.1 review)."""
        gitignore_path = Path(".gitignore")
        with open(gitignore_path) as f:
            content = f.read()

        assert "dist/" in content, ".gitignore missing dist/"
