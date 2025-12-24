# Publishing to PyPI

## Steps to publish ide-updater to PyPI:

### 1. Install build tools
```bash
pip install build twine
```

### 2. Build the package
```bash
python -m build
```

### 3. Upload to PyPI (first upload to test PyPI)
```bash
# Test PyPI first
python -m twine upload --repository testpypi dist/*

# Then real PyPI
python -m twine upload dist/*
```

### 4. Users can install with:
```bash
pip install ide-updater
```

## Required files (already have most):
- ✅ pyproject.toml (configured)
- ✅ README.md
- ✅ src/ structure
- ❌ LICENSE file (need to add)
- ❌ CHANGELOG.md (optional but recommended)