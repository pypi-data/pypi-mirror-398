# Quick Publish Guide

## 🚀 Quick Commands

### 1. Update Version (if needed)
```bash
# Edit pyproject.toml, change version to 0.7.0 (or next version)
vim pyproject.toml  # or use your editor
```

### 2. Build Package
```bash
poetry build
```

### 3. Test Build Locally (Optional)
```bash
pip install dist/hdf_dq_framework-*.whl --force-reinstall
python -c "from hdf_dq_framework import DQFramework; print('✓ Import successful')"
```

### 4. Dry Run (Test without publishing)
```bash
poetry publish --dry-run
```

### 5. Publish to PyPI
```bash
poetry publish
```

## 📋 Prerequisites Check

```bash
# Check Poetry
poetry --version

# Check PyPI token (if configured)
poetry config --list | grep pypi

# If not configured, set it:
poetry config pypi-token.pypi <your-token>
```

## 🔑 Getting PyPI Token

1. Go to: https://pypi.org/manage/account/token/
2. Create new token (scope: entire account)
3. Copy token
4. Configure: `poetry config pypi-token.pypi <token>`

## ✅ Complete Workflow

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml  # Change version to 0.7.0

# 2. Clean and build
rm -rf dist/ build/ *.egg-info/
poetry build

# 3. Test (optional)
pip install dist/hdf_dq_framework-0.7.0-py3-none-any.whl --force-reinstall

# 4. Dry run
poetry publish --dry-run

# 5. Publish
poetry publish

# 6. Verify
pip install hdf-dq-framework --upgrade
pip show hdf-dq-framework
```

## 🐛 Common Issues

**"Package already exists"**
- Solution: Increment version in `pyproject.toml`

**"Authentication failed"**
- Solution: `poetry config pypi-token.pypi <your-token>`

**"No module named 'hdf_dq_framework'"**
- Solution: Check package structure, ensure `hdf_dq_framework/` directory exists

