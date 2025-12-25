# Publishing to PyPI with uv

Using `uv` is the modern, fast way to publish Python packages. Here's how:

## Prerequisites

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **PyPI Account & Token**:
   - Create account: https://pypi.org/account/register/
   - Generate API token: https://pypi.org/manage/account/token/
   - Save the token (starts with `pypi-...`)

## Quick Publish (3 Steps)

### Step 1: Build with uv
```bash
# Clean previous builds
rm -rf dist/

# Build with uv (much faster than traditional tools!)
uv build
```

This creates:
- `dist/resume_generator_mcp-1.0.0-py3-none-any.whl`
- `dist/resume_generator_mcp-1.0.0.tar.gz`

### Step 2: Publish with uv
```bash
# Publish to PyPI
uv publish

# You'll be prompted for:
# Username: __token__
# Password: <paste-your-pypi-token>
```

That's it! Your package is now live on PyPI.

### Step 3: Verify
```bash
# Wait a few minutes, then try installing
uv venv test_env
source test_env/bin/activate
uv pip install resume-generator-mcp

# Test it works
python -m resume_generator_mcp
```

## Using Environment Variables (Recommended)

Instead of typing credentials each time, set environment variables:

```bash
# Add to your ~/.bashrc or ~/.zshrc
export UV_PUBLISH_TOKEN="pypi-YOUR-TOKEN-HERE"
export UV_PUBLISH_USERNAME="__token__"
```

Then publish becomes one command:
```bash
uv publish
```

## Test PyPI First (Recommended)

Test your package on Test PyPI before publishing to production:

### Step 1: Get Test PyPI Token
- Go to: https://test.pypi.org/manage/account/token/
- Generate a token

### Step 2: Publish to Test PyPI
```bash
# Set environment variables
export UV_PUBLISH_TOKEN="pypi-YOUR-TEST-TOKEN"
export UV_PUBLISH_USERNAME="__token__"

# Publish to Test PyPI
uv publish --index-url https://test.pypi.org/legacy/
```

### Step 3: Test Installation
```bash
# Create test environment
uv venv test_env
source test_env/bin/activate

# Install from Test PyPI
uv pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  resume-generator-mcp

# Test it
python -m resume_generator_mcp

# Clean up
deactivate
rm -rf test_env
```

### Step 4: Publish to Production PyPI
```bash
# Update token for production
export UV_PUBLISH_TOKEN="pypi-YOUR-PRODUCTION-TOKEN"

# Publish
uv publish
```

## Complete Workflow with uv

```bash
# 1. Make changes to your code
vim resume_generator_mcp/server.py

# 2. Update version in pyproject.toml
vim pyproject.toml  # Change version = "1.0.0" to "1.0.1"

# 3. Clean and build
rm -rf dist/
uv build

# 4. Publish
export UV_PUBLISH_TOKEN="your-token"
uv publish

# Done!
```

## Advantages of uv

Compared to traditional tools (build + twine):

| Feature | uv | Traditional |
|---------|-----|-------------|
| Speed | ⚡ 10-100x faster | Slow |
| Commands | 2 (`uv build`, `uv publish`) | 3+ (`pip install build`, `python -m build`, `twine upload`) |
| Dependencies | Zero (Rust binary) | Multiple Python packages |
| Install size | ~10MB | ~50MB+ |
| Unified tool | ✅ Build + publish | ❌ Separate tools |

## Configuration File (Optional)

Create `.pypirc` in your home directory for permanent config:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-TOKEN
```

Set permissions:
```bash
chmod 600 ~/.pypirc
```

Then you can publish without any prompts:
```bash
uv publish  # Uses config from .pypirc
```

## Troubleshooting

### "File already exists"
You can't re-upload the same version. Fix:
```bash
# Update version in pyproject.toml
vim pyproject.toml  # Change version number

# Rebuild and publish
rm -rf dist/
uv build
uv publish
```

### "Invalid token"
- Make sure you're using `__token__` as username (not your PyPI username)
- Token should start with `pypi-`
- Generate a new token if needed

### "Network error"
- Check your internet connection
- Try again (PyPI sometimes has timeouts)

## After Publishing

Your package is now available at:
- **PyPI page**: https://pypi.org/project/resume-generator-mcp/
- **Install command**: `pip install resume-generator-mcp` or `uv pip install resume-generator-mcp`
- **Stats**: https://pypistats.org/packages/resume-generator-mcp

## Quick Reference

```bash
# Build
uv build

# Publish to Test PyPI
uv publish --index-url https://test.pypi.org/legacy/

# Publish to Production PyPI
uv publish

# Build and publish in one go
rm -rf dist/ && uv build && uv publish
```

## Comparison: Traditional vs uv

**Traditional method:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install build twine
python -m build
python -m twine upload dist/*
```

**With uv:**
```bash
uv build
uv publish
```

Much simpler! 🚀

## Next Steps

After publishing with uv:

1. ✅ Test installation: `uv pip install resume-generator-mcp`
2. ✅ Create GitHub repo and push code
3. ✅ Submit to MCP directory
4. ✅ Announce on social media
5. ✅ Update documentation with real GitHub URLs

See `DISTRIBUTION_SUMMARY.md` for complete checklist.
