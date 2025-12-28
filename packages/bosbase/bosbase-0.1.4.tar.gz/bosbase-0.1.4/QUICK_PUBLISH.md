# Quick Publish Guide

## Prerequisites
```bash
pip install hatch
```

## Publish to PyPI

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.0"  # Update this
   ```

2. **Build the package**:
   ```bash
   cd python-sdk
   hatch build
   ```

3. **Publish to PyPI**:
   ```bash
   hatch publish
   ```
   
   When prompted:
   - Username: `__token__`
   - Password: Your PyPI API token (from https://pypi.org/manage/account/token/)

4. **Verify**:
   ```bash
   pip install bosbase
   ```

## Using Environment Variables

```bash
export HATCH_INDEX_USER=__token__
export HATCH_INDEX_AUTH=your-pypi-api-token
hatch publish
```

## Test on TestPyPI First

```bash
hatch publish --repo testpypi
# Then test: pip install --index-url https://test.pypi.org/simple/ bosbase
```

For detailed instructions, see [PUBLISHING.md](./PUBLISHING.md).


Run test
cd python-sdk
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e . pytest
pytest

/bin/bash -lc 'cd python-sdk && PYTHONPATH=src python3 -m pytest'











