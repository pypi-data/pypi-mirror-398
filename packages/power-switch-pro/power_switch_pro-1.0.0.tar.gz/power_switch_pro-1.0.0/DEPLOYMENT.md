# Deployment Guide

This document outlines the steps to deploy the Power Switch Pro library to GitHub, PyPI, and ReadTheDocs.

## Prerequisites

- Git repository initialized ✅
- All tests passing (98% coverage) ✅
- Documentation built successfully ✅
- Code formatted and linted ✅
- Security scans passed ✅

## 1. GitHub Repository Setup

### Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `power_switch_pro`
3. **Do not** initialize with README, license, or gitignore (we already have these)
4. Set visibility (public recommended for PyPI)

### Push to GitHub

```bash
# Add GitHub remote
git remote add origin https://github.com/bryankemp/power_switch_pro.git

# Push to GitHub
git push -u origin main
```

### Configure GitHub Repository Settings

1. **Branch Protection** (Settings → Branches):
   - Protect `main` branch
   - Require pull request reviews before merging
   - Require status checks to pass (CI tests)
   - Enable "Require branches to be up to date before merging"

2. **Secrets** (Settings → Secrets and variables → Actions):
   - Add `PYPI_API_TOKEN` (for automatic PyPI publishing)
   - Get token from https://pypi.org/manage/account/token/

3. **About Section** (Main page):
   - Add description: "Python library for Digital Loggers Power Switch Pro REST API"
   - Add website: https://power-switch-pro.readthedocs.io
   - Add topics: `python`, `power-management`, `digital-loggers`, `rest-api`, `pdu`, `automation`

## 2. ReadTheDocs Setup

### Link Repository

1. Go to https://readthedocs.org/dashboard/
2. Click "Import a Project"
3. Connect your GitHub account if not already connected
4. Select the `power_switch_pro` repository
5. Click "Import"

### Configure Build

ReadTheDocs will automatically detect:
- `.readthedocs.yaml` configuration
- Python package structure
- Documentation in `docs/` directory

Build should start automatically. Documentation will be available at:
- https://power-switch-pro.readthedocs.io

### Verify Documentation

After build completes:
1. Check that all pages render correctly
2. Verify API documentation is generated
3. Test navigation and search functionality

## 3. PyPI Publishing

### Test PyPI (Optional but Recommended)

First publish to Test PyPI to verify everything works:

```bash
# Build distribution packages
python -m build

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps power-switch-pro
```

### Production PyPI

Publishing to PyPI is handled automatically by GitHub Actions when you create a release:

1. **Create a Git Tag**:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. **Create GitHub Release**:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Select the tag `v0.1.0`
   - Title: "Release v0.1.0"
   - Description: Copy content from CHANGELOG.md
   - Click "Publish release"

3. **Automatic Publishing**:
   - GitHub Actions workflow will automatically:
     - Run tests
     - Build package
     - Publish to PyPI

### Manual PyPI Upload (Alternative)

If you prefer manual publishing:

```bash
# Install build tools
pip install build twine

# Build distribution packages
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

You'll be prompted for your PyPI credentials or API token.

## 4. Post-Deployment Verification

### Verify PyPI Package

```bash
# Install from PyPI
pip install power-switch-pro

# Verify installation
python -c "from power_switch_pro import PowerSwitchPro; print('Success!')"
```

### Verify Documentation

Visit https://power-switch-pro.readthedocs.io and check:
- [ ] Homepage loads correctly
- [ ] Installation instructions are clear
- [ ] Quick start guide works
- [ ] API reference is complete
- [ ] Examples are accessible

### Verify GitHub

Check that:
- [ ] README displays correctly
- [ ] CI badge shows passing status
- [ ] All workflows are green
- [ ] Issues and Discussions are enabled (if desired)

## 5. Enable Pre-commit Hooks (Optional)

For local development, enable pre-commit hooks:

```bash
# Install pre-commit hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

This will automatically run formatters and linters before each commit.

## 6. Ongoing Maintenance

### Version Updates

When releasing new versions:

1. Update version in:
   - `pyproject.toml`
   - `setup.py`
   - `power_switch_pro/__init__.py` (if present)

2. Update CHANGELOG.md with changes

3. Create and push git tag:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

4. Create GitHub release (triggers automatic PyPI publishing)

### Security Updates

Regularly run security scans:

```bash
# Check for vulnerabilities
safety scan

# Update dependencies
pip list --outdated
```

### Documentation Updates

Documentation is automatically rebuilt when you push to main branch.

To build locally:
```bash
cd docs
make html
open _build/html/index.html
```

## Troubleshooting

### CI Fails on GitHub

- Check the Actions tab for detailed error messages
- Verify all dependencies are in pyproject.toml
- Ensure tests pass locally: `pytest`

### PyPI Publishing Fails

- Verify PYPI_API_TOKEN secret is set correctly
- Check that version number hasn't been used before
- Ensure pyproject.toml is properly formatted

### ReadTheDocs Build Fails

- Check build logs at https://readthedocs.org/projects/power-switch-pro/builds/
- Verify .readthedocs.yaml configuration
- Ensure all Sphinx dependencies are specified

## Support

- GitHub Issues: https://github.com/bryankemp/power_switch_pro/issues
- Documentation: https://power-switch-pro.readthedocs.io
- PyPI: https://pypi.org/project/power-switch-pro/

## License

BSD-3-Clause - See LICENSE file for details.

## Author

Bryan Kemp (bryan@kempville.com)
