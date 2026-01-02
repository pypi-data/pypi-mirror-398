# Changelog

## gsdesign-python 0.1.4

### Testing

- Refactored integration tests to use `pytest-r-snapshot` for R snapshot
  generation and management, replacing legacy fixture files with
  snapshot-based assertions (#16).

## gsdesign-python 0.1.3

### Maintenance

- Added GitHub Actions workflow to run `ruff check` for code linting (#13).
- Updated GitHub Actions workflows to use `actions/checkout@v6` (#13).
- Updated badges in `README.md` (#13).

## gsdesign-python 0.1.2

### Linting

- Added ruff linter configuration to `pyproject.toml` with popular rule sets
  including pycodestyle, Pyflakes, pyupgrade, flake8-bugbear, flake8-simplify,
  and isort (#10).
- Fixed `ruff check` linting issues such as PEP 585 (#10).

## gsdesign-python 0.1.1

### Maintenance

- Added Python 3.14 support and set as default development environment (#7).
- Updated GitHub Actions workflows to use the latest `checkout` and `setup-python` versions (#7).

## gsdesign-python 0.1.0

- Increment version number to 0.1.0 to follow semantic versioning
  best practices (#6).

## gsdesign-python 0.0.1

### New features

- Ported the canonical `gridpts`, `h1`, and `hupdate` numerical integration
  routines from gsDesign, complete with typed public exports (#1).

### Testing

- Added unit tests with high-precision reference fixtures and regeneration
  tooling to keep the Python implementation aligned with the R package
  gsDesign2 (#1).
