# 📦 Deployment Guide: Publishing to PyPI

This guide explains how to publish the `spt-neo-rag-client` package to PyPI so users can install it with `pip` or `uv`.

## 🔧 Prerequisites

### 1. Install Build Tools
```bash
# Using UV (recommended)
uv add --dev build twine

# Or using pip
pip install build twine
```

### 2. Create PyPI Accounts

You need accounts on both platforms:
- **TestPyPI** (for testing): https://test.pypi.org/account/register/
- **PyPI** (production): https://pypi.org/account/register/

### 3. Generate API Tokens

#### TestPyPI Token:
1. Go to https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `spt-neo-rag-client-testpypi`
4. Scope: "Entire account" (for first upload)
5. Copy the token (starts with `pypi-`)

#### PyPI Token:
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token" 
3. Name: `spt-neo-rag-client-pypi`
4. Scope: "Entire account" (for first upload)
5. Copy the token (starts with `pypi-`)

## 🚀 Quick Publish (Using Script)

We've provided a convenient script:

```bash
cd clients/spt-neo-rag-client
./publish.sh
```

The script will:
1. Build the package
2. Ask if you want to upload to TestPyPI or PyPI
3. Handle the upload process

## 📋 Manual Step-by-Step Process

### Step 1: Build the Package

```bash
cd clients/spt-neo-rag-client
python -m build
```

This creates:
- `dist/spt_neo_rag_client-0.2.0.tar.gz` (source distribution)
- `dist/spt_neo_rag_client-0.2.0-py3-none-any.whl` (wheel)

### Step 2: Test Upload to TestPyPI

```bash
twine upload --repository testpypi dist/*
```

When prompted:
- **Username**: `__token__`
- **Password**: Your TestPyPI API token

### Step 3: Test Installation

```bash
# Test with pip
pip install --index-url https://test.pypi.org/simple/ spt-neo-rag-client

# Test with uv
uv add --index-url https://test.pypi.org/simple/ spt-neo-rag-client

# Test the package
python -c "from spt_neo_rag_client import NeoRagClient; print('✅ Package works!')"
```

### Step 4: Upload to Production PyPI

Once testing is successful:

```bash
twine upload dist/*
```

When prompted:
- **Username**: `__token__`  
- **Password**: Your PyPI API token

## 🎉 After Publishing

### Users can now install with:

```bash
# Using pip
pip install spt-neo-rag-client

# Using uv
uv add spt-neo-rag-client

# Using poetry
poetry add spt-neo-rag-client
```

### Update Package Description on PyPI

1. Go to https://pypi.org/project/spt-neo-rag-client/
2. Login and click "Manage"
3. Update project description, add screenshots, etc.

## 🔄 Updating the Package

For future updates:

### 1. Update Version
```bash
# Update version in both files:
# - pyproject.toml
# - src/spt_neo_rag_client/__init__.py
```

### 2. Clean Previous Build
```bash
rm -rf dist/ build/ *.egg-info/
```

### 3. Build and Upload
```bash
python -m build
twine upload dist/*
```

## 📊 Package Statistics

After publishing, you can:
- View download statistics at https://pypistats.org/packages/spt-neo-rag-client
- Monitor package at https://pypi.org/project/spt-neo-rag-client/

## 🛠️ Troubleshooting

### Common Issues:

**"File already exists"**
- You're trying to upload the same version twice
- Increment the version number in `pyproject.toml` and `__init__.py`

**"Invalid authentication credentials"**  
- Check your API token
- Ensure username is `__token__` (with underscores)

**"Package name already taken"**
- The package name `spt-neo-rag-client` should be available
- If not, consider: `spt-neorag-client`, `neo-rag-client`, etc.

**Import errors after installation**
- Check the package structure in `pyproject.toml`
- Verify all dependencies are listed correctly

## 🔐 Security Best Practices

1. **Never commit API tokens** to version control
2. **Use scoped tokens** (project-specific) after first upload
3. **Rotate tokens** periodically
4. **Use 2FA** on your PyPI accounts
5. **Pin dependency versions** for reproducible builds

## 📝 Checklist Before Publishing

- [ ] Version number updated in both files
- [ ] CHANGELOG.md updated
- [ ] README.md is comprehensive
- [ ] All tests pass
- [ ] Package builds without errors
- [ ] Tested on TestPyPI first
- [ ] API tokens are ready
- [ ] Dependencies are correctly specified 