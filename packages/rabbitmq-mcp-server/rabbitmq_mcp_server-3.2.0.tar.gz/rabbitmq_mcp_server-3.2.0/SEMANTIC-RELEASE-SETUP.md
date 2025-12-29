# Python Semantic Release Configuration

This project is now configured to use `python-semantic-release` for automated versioning and releases.

## Package Manager: uv

This project uses **uv** instead of Poetry for faster, more reliable dependency management.

### Why uv?
- ⚡ **10-100x faster** than pip and Poetry
- 🔒 **Reproducible** installs with `uv.lock`
- 🎯 **PEP 621 compliant** - standard pyproject.toml format
- 🚀 **Built-in virtual environment** management
- 📦 **Compatible** with all Python packaging tools

### Project Structure
- Dependencies defined in `pyproject.toml` using PEP 621 format
- Build system uses `hatchling` (lightweight, fast)
- Development dependencies in `[project.optional-dependencies]`

## What Has Been Configured

### 1. Version Management
- **Version variable** added to `src/mcp_server/__init__.py`
- **Version sources**: 
  - `pyproject.toml:tool.poetry.version`
  - `src/mcp_server/__init__.py:__version__`

### 2. Dependencies
- Added `python-semantic-release = "^9.0"` to dev dependencies in `pyproject.toml`

### 3. Semantic Release Configuration (`pyproject.toml`)
```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/mcp_server/__init__.py:__version__"]
branch = "main"
upload_to_vcs_release = true
upload_to_pypi = false
build_command = "uv build"
major_on_zero = true
tag_format = "v{version}"
```

**Key settings:**
- Releases on `main` branch only
- Creates GitHub releases automatically
- PyPI publishing **enabled** ✅
- Git tags formatted as `v{version}` (e.g., v1.0.0)
- Major version bumps enabled even for 0.x.x versions

### 4. Commit Message Rules
The following commit types trigger version bumps:

- `feat:` → **MINOR** version bump (0.1.0 → 0.2.0)
- `fix:` → **PATCH** version bump (0.1.0 → 0.1.1)
- `perf:` → **PATCH** version bump (0.1.0 → 0.1.1)
- `feat!:` or `BREAKING CHANGE:` → **MAJOR** version bump (0.1.0 → 1.0.0)

Other types (docs, style, refactor, test, build, ci, chore) don't trigger releases.

### 5. GitHub Actions Workflow
Created `.github/workflows/release.yml` that:
- Triggers on pushes to `main` branch
- Uses Python 3.12
- Installs dependencies via **uv** (fast!)
- Runs semantic release with `uv run`
- **Publishes to PyPI** automatically ✅
- Creates GitHub releases automatically
- Uploads build artifacts to releases

### 6. Documentation
- `CHANGELOG.md` - Will be auto-generated with each release
- `CONTRIBUTING.md` - Commit message guidelines and examples

## Installation Steps

To complete the setup, run:

```bash
# Install uv if not already installed (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv

# Install project dependencies including python-semantic-release
uv sync --all-extras
```

## Usage

### Local Testing
Test what version would be released:
```bash
uv run semantic-release version --print
```

### Manual Release (if needed)
```bash
# Dry run to see what would happen
uv run semantic-release version --noop

# Create a new version and tag
uv run semantic-release version

# Publish the release
uv run semantic-release publish
```

### Using uvx (no project installation)
```bash
# Run semantic-release directly without installing
uvx --from python-semantic-release semantic-release version --print
```

### Automated Releases
Once you push commits to `main` with conventional commit messages, the GitHub Action will:
1. Analyze commits since last release
2. Determine version bump (major/minor/patch)
3. Update version in code and pyproject.toml
4. Generate/update CHANGELOG.md
5. Create a git tag
6. **Publish to PyPI** 🚀
7. Create a GitHub release
8. Upload build artifacts

## Commit Message Examples

```bash
# Feature - triggers minor bump
git commit -m "feat(rabbitmq): add queue management tools"

# Bug fix - triggers patch bump
git commit -m "fix(connection): handle network timeouts"

# Breaking change - triggers major bump
git commit -m "feat(api)!: redesign tool interface

BREAKING CHANGE: Tool response format has changed"

# No release
git commit -m "docs: update README with examples"
git commit -m "chore: update dependencies"
```

## Next Steps

1. ✅ Configuration files created (using uv instead of Poetry)
2. ⏳ Install dependencies: `uv sync --all-extras`
3. ⏳ Test locally: `uv run semantic-release version --print`
4. ⏳ Make commits using conventional commit format
5. ⏳ Merge to main to trigger automated release

## GitHub Permissions & Secrets

The GitHub Action requires the following permissions (already configured in workflow):
- `contents: write` - To create tags and releases
- `issues: write` - To close issues in changelog
- `pull-requests: write` - To reference PRs in changelog

These use the default `GITHUB_TOKEN` and require no additional secrets.

## ⚠️ Required: PyPI Token Setup

PyPI publishing is **enabled**. You need to add your PyPI token to GitHub secrets:

### 1. Get a PyPI API Token

1. Create an account on [PyPI](https://pypi.org/) if you don't have one
2. Go to [Account Settings → API tokens](https://pypi.org/manage/account/token/)
3. Click "Add API token"
4. Name it (e.g., "rabbitmq-mcp-server-releases")
5. Scope: Choose "Entire account" or specific to this project (after first upload)
6. Copy the token (starts with `pypi-`)

### 2. Add Token to GitHub Secrets

1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `PYPI_TOKEN`
5. Value: Paste your PyPI token
6. Click "Add secret"

### 3. First Release

For the first release, you may need to:
- Use a token scoped to "Entire account" (can't scope to project that doesn't exist yet)
- Or manually upload the first version: `uv build && uv publish`
- After first release, you can create a project-scoped token for better security

### Test PyPI (Optional)

To test with TestPyPI first:

1. Get a token from [test.pypi.org](https://test.pypi.org)
2. Test locally:
   ```bash
   uv build
   uv publish --token pypi-your-test-token --publish-url https://test.pypi.org/legacy/
   ```
3. Once working, use the real PyPI token in GitHub secrets
