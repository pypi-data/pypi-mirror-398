# PyPI Publishing Guide for ARGUS

This guide walks you through publishing ARGUS to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [TestPyPI](https://test.pypi.org/account/register/) (testing)

2. **API Tokens**: Generate API tokens:
   - PyPI: Account Settings → API tokens → Add API token
   - TestPyPI: Same process on test.pypi.org

## Step 1: Install Build Tools

```bash
pip install build twine
```

## Step 2: Verify Package Structure

Ensure your package has:
```
argus/
├── pyproject.toml      ✓
├── README.md           ✓
├── LICENSE             ✓
├── argus/
│   ├── __init__.py     ✓ (with __version__)
│   ├── py.typed        ✓
│   └── ...modules...
└── tests/
```

## Step 3: Update Version

Edit `argus/__init__.py`:
```python
__version__ = "0.1.0"  # Use semantic versioning
```

## Step 4: Build the Package

```bash
cd c:\ingester_ops\argus

# Clean previous builds
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Build source distribution and wheel
python -m build
```

This creates:
- `dist/argus_ai-0.1.0.tar.gz` (source)
- `dist/argus_ai-0.1.0-py3-none-any.whl` (wheel)

## Step 5: Verify the Build

```bash
# Check the distribution
twine check dist/*

# Test install locally
pip install dist/argus_ai-0.1.0-py3-none-any.whl
python -c "import argus; print(argus.__version__)"
```

## Step 6: Upload to TestPyPI (Recommended First)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-`)

Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ argus-ai
```

## Step 7: Upload to PyPI (Production)

```bash
# Upload to PyPI
twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: Your PyPI API token

## Step 8: Verify Installation

```bash
pip install argus-ai
python -c "from argus import RDCOrchestrator; print('Success!')"
```

## Using .pypirc for Convenience

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-PYPI-TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN
```

Then upload simply with:
```bash
twine upload --repository testpypi dist/*
twine upload --repository pypi dist/*
```

## Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):
- `0.1.0` → Initial release
- `0.1.1` → Bug fixes
- `0.2.0` → New features (backward compatible)
- `1.0.0` → Stable API

## Common Issues

### Package Name Conflict
If `argus` is taken, we use `argus-ai`. Already configured in `pyproject.toml`.

### Missing Dependencies
Ensure all dependencies are in `pyproject.toml` under `dependencies`.

### README Rendering
PyPI uses reStructuredText by default. We specify `readme = "README.md"` and `content-type = "text/markdown"` in pyproject.toml.

## Automation with GitHub Actions

Create `.github/workflows/publish.yml`:
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Build
        run: |
          pip install build
          python -m build
      - name: Publish
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

## Quick Commands Reference

```bash
# Full publish workflow
cd c:\ingester_ops\argus
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
python -m build
twine check dist/*
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*                         # Production
```
