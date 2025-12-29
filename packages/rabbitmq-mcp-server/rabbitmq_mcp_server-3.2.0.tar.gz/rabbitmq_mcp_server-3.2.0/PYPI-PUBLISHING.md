# PyPI Publishing Guide

This project is configured to automatically publish to PyPI on every release.

## 🚀 Automatic Publishing

When you merge to `main` with conventional commits, the GitHub Action will:
1. Create a new version
2. Build the package with `uv build`
3. **Publish to PyPI** automatically
4. Create a GitHub release

## 📋 Prerequisites

### 1. PyPI Account
- Create account at [pypi.org](https://pypi.org/account/register/)
- Verify your email address

### 2. Generate API Token

**For first release:**
1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens"
3. Click "Add API token"
4. Token name: `rabbitmq-mcp-server-releases`
5. Scope: **"Entire account"** (required for first release)
6. Click "Add token"
7. **Copy the token immediately** (starts with `pypi-`)

**After first release (recommended):**
1. Go to your [project settings on PyPI](https://pypi.org/manage/project/rabbitmq-mcp-server/settings/)
2. Create a project-scoped token for better security
3. Update the GitHub secret with the new token

### 3. Add Token to GitHub Secrets

1. Go to: `https://github.com/guercheLE/rabbitmq-mcp-server/settings/secrets/actions`
2. Click "New repository secret"
3. Name: **`PYPI_TOKEN`** (exactly as shown)
4. Value: Paste your PyPI token (including the `pypi-` prefix)
5. Click "Add secret"

## 🧪 Testing Before First Release

### Option 1: Test with TestPyPI

```bash
# 1. Get a token from test.pypi.org
# Visit: https://test.pypi.org/manage/account/token/

# 2. Build the package
uv build

# 3. Publish to TestPyPI
uv publish --token pypi-YOUR_TEST_TOKEN --publish-url https://test.pypi.org/legacy/

# 4. Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ rabbitmq-mcp-server
```

### Option 2: Manual First Release

```bash
# 1. Build the package
uv build

# 2. Check the build artifacts
ls -lh dist/

# 3. Publish to PyPI
uv publish --token pypi-YOUR_TOKEN

# 4. Verify on PyPI
# Visit: https://pypi.org/project/rabbitmq-mcp-server/
```

## 📦 Package Metadata

The package is configured with:
- **Name**: `rabbitmq-mcp-server`
- **Description**: MCP server for RabbitMQ with semantic discovery
- **License**: LGPL-3.0-or-later
- **Python**: >=3.12
- **Keywords**: mcp, rabbitmq, model-context-protocol, llm, ai, semantic-search

### URLs
- Homepage: https://github.com/guercheLE/rabbitmq-mcp-server
- Repository: https://github.com/guercheLE/rabbitmq-mcp-server
- Issues: https://github.com/guercheLE/rabbitmq-mcp-server/issues
- Changelog: https://github.com/guercheLE/rabbitmq-mcp-server/blob/main/CHANGELOG.md

## 🔧 Configuration Details

### pyproject.toml
```toml
[tool.semantic_release]
upload_to_pypi = true
build_command = "uv build"
```

### GitHub Actions Workflow
```yaml
- name: Publish package distributions to PyPI
  if: steps.release.outputs.released == 'true'
  run: |
      uv build
      uv publish --token ${{ secrets.PYPI_TOKEN }}
```

## 🎯 Release Process

### 1. Make Changes
```bash
git checkout -b feature/my-feature
# Make your changes
git add .
git commit -m "feat: add new feature"
```

### 2. Create PR and Merge to Main
```bash
# Push and create PR
git push origin feature/my-feature

# After review and approval, merge to main
```

### 3. Automatic Release
The GitHub Action will:
- ✅ Detect the `feat:` commit
- ✅ Bump version from 0.1.0 → 0.2.0
- ✅ Update version in code and pyproject.toml
- ✅ Generate CHANGELOG.md
- ✅ Build: `uv build` creates `dist/rabbitmq_mcp_server-0.2.0.tar.gz` and `.whl`
- ✅ Publish: `uv publish` uploads to PyPI
- ✅ Create GitHub release with tag `v0.2.0`

### 4. Verify Release
Check:
- 📦 [PyPI page](https://pypi.org/project/rabbitmq-mcp-server/)
- 🏷️ [GitHub releases](https://github.com/guercheLE/rabbitmq-mcp-server/releases)
- 📝 [CHANGELOG.md](https://github.com/guercheLE/rabbitmq-mcp-server/blob/main/CHANGELOG.md)

## 🔐 Security Best Practices

### Token Permissions
- ✅ Use project-scoped tokens after first release
- ✅ Rotate tokens periodically
- ✅ Never commit tokens to git
- ✅ Use GitHub Secrets for CI/CD

### Package Security
```bash
# Scan for vulnerabilities
pip-audit

# Check package metadata
uv build --check

# View what will be published
tar -tzf dist/rabbitmq_mcp_server-*.tar.gz
```

## 🛠️ Manual Publishing Commands

If you need to publish manually:

```bash
# Build the package
uv build

# Publish to PyPI
uv publish --token pypi-YOUR_TOKEN

# Or use environment variable
export UV_PUBLISH_TOKEN=pypi-YOUR_TOKEN
uv publish

# Publish to TestPyPI
uv publish --token pypi-YOUR_TEST_TOKEN \
    --publish-url https://test.pypi.org/legacy/
```

## 📊 After Publishing

Users can install your package with:

```bash
# Using pip
pip install rabbitmq-mcp-server

# Using uv
uv add rabbitmq-mcp-server

# Using uvx (run without installing)
uvx rabbitmq-mcp-server
```

## 🐛 Troubleshooting

### "Package not found" on PyPI
- Ensure the package name is available on PyPI
- Check if first upload succeeded
- Verify token has correct permissions

### "Invalid credentials"
- Verify `PYPI_TOKEN` secret is set correctly in GitHub
- Ensure token starts with `pypi-`
- Check token hasn't expired

### "File already exists"
- You can't overwrite a version on PyPI
- Bump version and try again
- Each version is immutable once published

### Build failures
```bash
# Check build locally
uv build

# Validate package
twine check dist/*

# View package contents
tar -tzf dist/*.tar.gz
```

## 📚 Resources

- [PyPI Documentation](https://packaging.python.org/)
- [uv Publishing Guide](https://docs.astral.sh/uv/guides/publish/)
- [Python Packaging Guide](https://packaging.python.org/guides/distributing-packages-using-setuptools/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)

## ✅ Checklist

Before first release:
- [ ] PyPI account created and verified
- [ ] API token generated (entire account scope)
- [ ] `PYPI_TOKEN` added to GitHub secrets
- [ ] Package name `rabbitmq-mcp-server` is available on PyPI
- [ ] Test build locally: `uv build`
- [ ] (Optional) Test with TestPyPI first
- [ ] Update author name/email in `pyproject.toml`
- [ ] Review README.md for end users
- [ ] Merge to main with conventional commit

After first release:
- [ ] Verify package appears on PyPI
- [ ] Test installation: `pip install rabbitmq-mcp-server`
- [ ] Create project-scoped token
- [ ] Update GitHub secret with project-scoped token
- [ ] Update PYPI_TOKEN scope for better security
