# Publishing DocRAG Kit to PyPI

This guide explains how to publish DocRAG Kit to PyPI so users can install it with `pip install docrag-kit`.

## Prerequisites

- [x] All tests passing (65/65)
- [x] Documentation complete
- [x] GitHub Actions workflows configured
- [x] No secrets in code
- [x] LICENSE file present

## Step 1: Register on PyPI

### 1.1 Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Fill in your details:
   - Username
   - Email
   - Password
3. Verify your email address

### 1.2 Enable Two-Factor Authentication (Required)

1. Go to https://pypi.org/manage/account/
2. Click "Account security"
3. Click "Add 2FA"
4. Follow the instructions (use an authenticator app)

**Note:** 2FA is mandatory for publishing packages to PyPI.

### 1.3 Create API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Fill in:
   - Token name: `docrag-kit-upload`
   - Scope: "Entire account" (for first publication)
4. Click "Add token"
5. **IMPORTANT:** Copy the token immediately (it's shown only once!)
   - Format: `pypi-AgEIcHlwaS5vcmc...`

## Step 2: Add Token to GitHub

### 2.1 Add as GitHub Secret

1. Go to your repository: https://github.com/dexiusprime-oss/docrag-kit
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Fill in:
   - Name: `PYPI_API_TOKEN`
   - Value: `pypi-AgE...` (paste your token)
5. Click "Add secret"

## Step 3: Verify Package is Ready

Check that everything is in place:

```bash
# Run all tests
pytest tests/ -v

# Check package metadata
python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project'])"

# Verify no secrets in code
git grep -E "(sk-[a-zA-Z0-9]{20,}|pypi-[a-zA-Z0-9]+)"

# Check that .env is gitignored
git status | grep ".env"  # Should show nothing
```

All checks should pass:
- 65 tests passing
- Package metadata correct
- No secrets in code
- .env files not tracked

## Step 4: Publish to PyPI

### Option A: Automatic Publication (Recommended)

GitHub Actions will automatically publish when you push a version tag:

```bash
# 1. Make sure all changes are committed
git status

# 2. Create a version tag (use current version from pyproject.toml)
git tag v0.1.0

# 3. Push the tag to GitHub
git push origin v0.1.0
```

GitHub Actions will:
1. Run all tests
2. Build the package
3. Publish to PyPI
4. Create a GitHub Release

Monitor the progress:
- Go to: https://github.com/dexiusprime-oss/docrag-kit/actions
- Watch the "Release" workflow

### Option B: Manual Publication

If you prefer to publish manually:

```bash
# 1. Install build tools
pip install build twine

# 2. Build the package
python -m build

# This creates:
# - dist/docrag_kit-0.1.0-py3-none-any.whl
# - dist/docrag-kit-0.1.0.tar.gz

# 3. Check the package
twine check dist/*

# 4. (Optional) Test on Test PyPI first
twine upload --repository testpypi dist/*
# Username: __token__
# Password: pypi-AgE... (your token)

# 5. Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ docrag-kit

# 6. If everything works, publish to PyPI
twine upload dist/*
# Username: __token__
# Password: pypi-AgE... (your token)
```

## Step 5: Verify Publication

After publication, verify the package:

```bash
# 1. Check on PyPI
# Visit: https://pypi.org/project/docrag-kit/

# 2. Install from PyPI
pip install docrag-kit

# 3. Test the installation
docrag --version
docrag --help

# 4. Run a quick test
mkdir test-install
cd test-install
docrag init --non-interactive --template general
docrag config
```

## Step 6: Update Documentation

After successful publication, update README.md:

```markdown
## Installation

### From PyPI

```bash
pip install docrag-kit
```
```

Remove the "(when published)" note.

## Version Management

### Semantic Versioning (SemVer)

Use semantic versioning: `MAJOR.MINOR.PATCH`

- `0.1.0` - Initial release (current)
- `0.1.1` - Bug fixes (backward compatible)
- `0.2.0` - New features (backward compatible)
- `1.0.0` - Stable release

### Releasing a New Version

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.1.1"
   ```

2. Update CHANGELOG.md (if you have one)

3. Commit changes:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.1"
   git push
   ```

4. Create and push tag:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```

5. GitHub Actions will automatically publish

## Troubleshooting

### Error: Package name already exists

If `docrag-kit` is already taken on PyPI:

1. Check: https://pypi.org/project/docrag-kit/
2. Choose a different name in `pyproject.toml`:
   ```toml
   name = "docrag-kit-ai"  # or another unique name
   ```

### Error: Invalid token

- Make sure you copied the entire token
- Token should start with `pypi-`
- Check that token is added to GitHub Secrets correctly

### Error: Version already exists

- You cannot overwrite a published version
- Increment the version number in `pyproject.toml`
- Create a new tag

### Build fails

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Rebuild
python -m build
```

## Security Notes

**NEVER commit your PyPI token to git!**

- Store in GitHub Secrets
- Store in environment variables locally
- Never in code
- Never in configuration files

## Quick Reference

```bash
# Check current version
grep "version" pyproject.toml

# Run tests
pytest tests/ -v

# Build package
python -m build

# Check package
twine check dist/*

# Publish to Test PyPI
twine upload --repository testpypi dist/*

# Publish to PyPI
twine upload dist/*

# Or use GitHub Actions (recommended)
git tag v0.1.0
git push origin v0.1.0
```

## Resources

- PyPI: https://pypi.org/
- Test PyPI: https://test.pypi.org/
- Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/
- GitHub Actions: https://docs.github.com/en/actions

## Support

If you encounter issues:
1. Check the GitHub Actions logs
2. Review this guide
3. Check PyPI documentation
4. Open an issue on GitHub
