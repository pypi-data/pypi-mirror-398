# Publishing Guide

This document describes how to publish new versions of `pyeuclid` to PyPI.

## Prerequisites
1. **PyPI Account**: You must have an account on https://pypi.org.
2. **PyPI API Token**: Create a token at https://pypi.org/manage/account/token/.
3. **GitHub Secret**: Add the token to the repository secrets:
   - Name: `PYPI_API_TOKEN`
   - Value: your token (starts with `pypi-`)

## Versioning
The project follows [Semantic Versioning](https://semver.org). Keep the version consistent in:
- `pyproject.toml` (`project.version`)
- `pyeuclid/__init__.py` (`__version__`)

The PyPI package name is `pyeuclid` (lowercase); the display name is `PyEuclid`.

## Automatic Publishing (recommended)
Publishing is automated on pushed tags that start with `v` (e.g., `v1.0.0`):
1. Bump version in `pyproject.toml` and `pyeuclid/__init__.py`.
2. Commit changes.
3. Tag and push:
   ```bash
   git tag v1.0.0
   git push origin main
   git push origin v1.0.0
   ```
4. GitHub Actions (`.github/workflows/publish-to-pypi.yml`) will:
   - Verify the tag matches `pyproject.toml`
   - Build the package
   - Run `twine check`
   - Upload to PyPI using `PYPI_API_TOKEN`
   - Create a GitHub release with the built artifacts

## Manual Publishing (if needed)
```bash
python -m pip install --upgrade pip build twine
python -m build
twine check dist/*
TWINE_USERNAME=__token__ TWINE_PASSWORD=YOUR_PYPI_TOKEN twine upload dist/*
```

## Testing on TestPyPI
If you want to test the process without publishing to the main index:
```bash
python -m build
TWINE_USERNAME=__token__ TWINE_PASSWORD=YOUR_TESTPYPI_TOKEN \
  twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyeuclid
```

## Notes
- Large datasets (`data/`) and cached artifacts (`cache/`, `cache.tar.gz`) are **excluded** from the wheel/sdist; install from source if you need them for experiments.
- Use tags that match the version exactly (e.g., `v1.0.0`); reusing a version that was already published will fail.

