# Release Checklist for DocRAG Kit

Use this checklist before publishing a new version to PyPI.

## Pre-Release Checklist

### Code Quality

- [ ] All tests passing (run `pytest tests/ -v`)
  - Current: 65/65 tests passing
- [ ] No linting errors (run `flake8 src/`)
- [ ] Code formatted with black (run `black src/ tests/`)
- [ ] Type checking passes (run `mypy src/`)

### Security

- [ ] No API keys or secrets in code
  - Run: `git grep -E "(sk-[a-zA-Z0-9]{20,}|pypi-[a-zA-Z0-9]+)"`
- [ ] `.env` files not tracked in git
  - Run: `git status | grep ".env"`
- [ ] `.gitignore` properly configured
- [ ] Security scanning passes in CI/CD

### Documentation

- [ ] README.md is up to date
- [ ] CHANGELOG.md updated (if exists)
- [ ] API_REFERENCE.md is current
- [ ] EXAMPLES.md has working examples
- [ ] QUICK_START.md is accurate
- [ ] All documentation links work

### Package Configuration

- [ ] Version number updated in `pyproject.toml`
- [ ] Dependencies are correct and up to date
- [ ] `requires-python` is accurate (>=3.10)
- [ ] Package metadata is complete:
  - [ ] name
  - [ ] version
  - [ ] description
  - [ ] authors
  - [ ] license
  - [ ] keywords
  - [ ] classifiers

### Build & Test

- [ ] Package builds successfully
  ```bash
  python -m build
  ```
- [ ] Package passes checks
  ```bash
  twine check dist/*
  ```
- [ ] Clean installation works
  ```bash
  pip install dist/*.whl
  docrag --version
  docrag --help
  ```

### GitHub

- [ ] All changes committed
- [ ] All changes pushed to main branch
- [ ] GitHub Actions workflows passing
- [ ] No open critical issues
- [ ] PYPI_API_TOKEN secret is set

## Release Process

### 1. Update Version

Edit `pyproject.toml`:
```toml
version = "0.1.0"  # Update this
```

### 2. Commit Version Change

```bash
git add pyproject.toml
git commit -m "Bump version to 0.1.0"
git push origin main
```

### 3. Create Git Tag

```bash
git tag v0.1.0
git push origin v0.1.0
```

### 4. Monitor GitHub Actions

- Go to: https://github.com/dexiusprime-oss/docrag-kit/actions
- Watch the "Release" workflow
- Ensure all steps pass:
  - [ ] Tests
  - [ ] Build
  - [ ] Publish to PyPI
  - [ ] Create GitHub Release

## Post-Release Checklist

### Verify Publication

- [ ] Package appears on PyPI
  - Check: https://pypi.org/project/docrag-kit/
- [ ] Version number is correct
- [ ] Description and metadata are correct
- [ ] Installation works
  ```bash
  pip install docrag-kit
  docrag --version
  ```

### Test Installation

Create a fresh environment and test:

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate

# Install from PyPI
pip install docrag-kit

# Test basic commands
docrag --version
docrag --help
docrag doctor

# Test in a project
mkdir test-project
cd test-project
docrag init --non-interactive --template general
docrag config
```

### Update Documentation

- [ ] Update README.md to remove "(when published)"
- [ ] Add release notes to GitHub Release
- [ ] Update any version-specific documentation
- [ ] Announce release (if applicable)

### Monitor

- [ ] Check for installation issues
- [ ] Monitor GitHub issues
- [ ] Check PyPI download stats
- [ ] Respond to user feedback

## Rollback Plan

If critical issues are found after release:

### Option 1: Quick Fix

1. Fix the issue
2. Increment patch version (e.g., 0.1.0 → 0.1.1)
3. Follow release process again

### Option 2: Yank Release

If the release is broken:

1. Go to PyPI project page
2. Click "Manage" → "Releases"
3. Click "Options" → "Yank release"
4. Add reason for yanking
5. Release fixed version immediately

**Note:** Yanked releases can still be installed explicitly but won't be installed by default.

## Version Numbering Guide

Use Semantic Versioning (SemVer): MAJOR.MINOR.PATCH

### When to increment:

- **PATCH** (0.1.0 → 0.1.1)
  - Bug fixes
  - Documentation updates
  - Performance improvements
  - No API changes

- **MINOR** (0.1.0 → 0.2.0)
  - New features
  - New commands
  - Backward compatible changes
  - Deprecations (with warnings)

- **MAJOR** (0.9.0 → 1.0.0)
  - Breaking changes
  - API redesign
  - Removed deprecated features
  - Major refactoring

### Pre-release versions:

- `0.1.0a1` - Alpha release
- `0.1.0b1` - Beta release
- `0.1.0rc1` - Release candidate

## Common Issues

### Issue: Package name already taken

**Solution:** Change name in `pyproject.toml`
```toml
name = "docrag-kit-ai"  # or another unique name
```

### Issue: Version already exists

**Solution:** Increment version number
- You cannot overwrite published versions
- Always use a new version number

### Issue: Build fails

**Solution:**
```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Rebuild
python -m build
```

### Issue: Tests fail in CI

**Solution:**
- Fix failing tests locally first
- Ensure all dependencies are in `pyproject.toml`
- Check Python version compatibility

## Quick Commands

```bash
# Run all checks
pytest tests/ -v
flake8 src/
black --check src/ tests/
mypy src/

# Build package
python -m build

# Check package
twine check dist/*

# Test installation locally
pip install dist/*.whl

# Create and push tag
git tag v0.1.0
git push origin v0.1.0

# Manual upload (if needed)
twine upload dist/*
```

## Resources

- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

---

**Last Updated:** December 2024
**Current Version:** 0.1.0
**Status:** Ready for first release
