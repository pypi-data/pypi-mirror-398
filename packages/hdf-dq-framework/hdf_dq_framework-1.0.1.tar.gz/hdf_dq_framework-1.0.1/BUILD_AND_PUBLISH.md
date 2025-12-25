# Building and Publishing hdf-dq-framework

This guide explains how to build and publish the `hdf-dq-framework` package to PyPI.

## Prerequisites

1. **Poetry** - Package manager (already installed)

   ```bash
   poetry --version  # Should show Poetry (version 2.0.0)
   ```

2. **PyPI Account** - You need credentials for PyPI

   - Create account at https://pypi.org/account/register/
   - Get API token from https://pypi.org/manage/account/token/

3. **Git** - For version management (optional but recommended)

## Step 1: Update Version

Before building, update the version in `pyproject.toml`:

```bash
# Edit pyproject.toml and update the version
# Current version: 0.6.0
# For new features: 0.7.0
# For bug fixes: 0.6.1
```

Or use the bump script:

```bash
./bump_version.sh  # If available
```

## Step 2: Clean Previous Builds (Optional)

```bash
# Remove old build artifacts
rm -rf dist/
rm -rf build/
rm -rf *.egg-info/
```

## Step 3: Build the Package

Build both wheel and source distribution:

```bash
poetry build
```

This will create:

- `dist/hdf_dq_framework-<version>-py3-none-any.whl` (wheel)
- `dist/hdf_dq_framework-<version>.tar.gz` (source distribution)

### Verify Build

```bash
# List built packages
ls -lh dist/

# Check package contents (optional)
unzip -l dist/hdf_dq_framework-*.whl | head -20
```

## Step 4: Test the Build Locally (Recommended)

Before publishing, test installing the package locally:

```bash
# Install from local wheel
pip install dist/hdf_dq_framework-*.whl --force-reinstall

# Or install in editable mode for development
pip install -e .

# Test import
python -c "from hdf_dq_framework import DQFramework; print('Import successful!')"
```

## Step 5: Configure PyPI Credentials

### Option A: Using Poetry Config (Recommended)

```bash
# Set PyPI token
poetry config pypi-token.pypi <your-api-token>

# Verify configuration
poetry config --list | grep pypi
```

### Option B: Using Environment Variables

```bash
# Set environment variables
export POETRY_PYPI_TOKEN_PYPI=<your-api-token>
```

### Option C: Interactive Login

Poetry will prompt for credentials when publishing:

```bash
poetry publish
# Username: __token__
# Password: <your-api-token>
```

## Step 6: Publish to PyPI

### Dry Run (Test without publishing)

```bash
poetry publish --dry-run
```

This simulates the upload without actually publishing.

### Publish to TestPyPI (Recommended for first time)

```bash
# Configure test repository
poetry config repositories.testpypi https://test.pypi.org/legacy/

# Publish to TestPyPI
poetry publish --repository testpypi

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ hdf-dq-framework
```

### Publish to Production PyPI

```bash
poetry publish
```

This will:

1. Upload the wheel file
2. Upload the source distribution
3. Make the package available on PyPI

## Step 7: Verify Publication

1. **Check PyPI website:**

   ```
   https://pypi.org/project/hdf-dq-framework/
   ```

2. **Test installation:**

   ```bash
   pip install hdf-dq-framework
   ```

3. **Verify version:**
   ```bash
   pip show hdf-dq-framework
   ```

## Complete Workflow Example

```bash
# 1. Update version in pyproject.toml (e.g., 0.7.0)

# 2. Clean and build
rm -rf dist/ build/ *.egg-info/
poetry build

# 3. Test locally
pip install dist/hdf_dq_framework-0.7.0-py3-none-any.whl --force-reinstall
python -c "from hdf_dq_framework import DQFramework; print('OK')"

# 4. Dry run
poetry publish --dry-run

# 5. Publish
poetry publish

# 6. Verify
pip install hdf-dq-framework --upgrade
pip show hdf-dq-framework
```

## Troubleshooting

### Error: "Package already exists"

- Version already published. Increment version in `pyproject.toml`

### Error: "Authentication failed"

- Check your PyPI token is correct
- Verify token has upload permissions
- Try: `poetry config pypi-token.pypi <token>`

### Error: "Package structure issue"

- Verify `hdf_dq_framework/` directory exists
- Check `pyproject.toml` packages configuration
- Ensure `__init__.py` exists in package directory

### Build fails

- Check all dependencies are specified in `pyproject.toml`
- Verify Python version compatibility
- Check for syntax errors in source files

## Version Numbering

Follow semantic versioning (semver):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Current version: **0.6.0**

## Post-Publication Checklist

- [ ] Package appears on PyPI
- [ ] Can install with `pip install hdf-dq-framework`
- [ ] Documentation is up to date
- [ ] Version number incremented
- [ ] Git tag created (optional): `git tag v0.7.0 && git push --tags`

## Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [PyPI Help](https://pypi.org/help/)
- [Python Packaging Guide](https://packaging.python.org/)
