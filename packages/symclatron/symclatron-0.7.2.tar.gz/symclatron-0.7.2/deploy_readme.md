# Release guide (symclatron)

This doc summarizes the release flow for PyPI + prefix.dev (pixi) and the GitHub push/tag steps.

## Requirements

- `flit` and `twine` available in the Python environment used by `pixi run`
- `rattler-build` available on PATH
- Environment variables:
  - `PYPI_API_TOKEN`
  - `PREFIX_API_KEY`

## Standard release (recommended)

```bash
VERSION="0.7.2"
pixi run ./scripts/deploy.sh "$VERSION" --push --tag
```

What it does:
- Updates `__version__` in `symclatron/__init__.py` and `symclatron/symclatron.py`
- Updates `context.version` and `sha256` in `recipe.yaml`
- Builds sdist/wheel and uploads to PyPI
- Builds conda package and uploads to prefix.dev channel `astrogenomics`
- Commits release changes, tags `v<version>`, and pushes to GitHub

## If you already ran deploy without pushing

```bash
VERSION="<version>"
git add .
git commit -m "Release $VERSION"
git push origin main
git tag "v$VERSION"
git push origin "v$VERSION"
```

## Notes

- `flit build` fails if there are untracked files in the repo; either add them or remove them before running the deploy script.
- PyPI propagation can take a few minutes. The deploy script waits by default; adjust with:
  - `PYPI_WAIT_TIMEOUT` (seconds, default 600, set to 0 to skip)
  - `PYPI_WAIT_INTERVAL` (seconds, default 10)
