# UNICEF-Security

[![Coverage Development](https://codecov.io/gh/unicef/unicef-security/branch/develop/graph/badge.svg?token=sytM1cd8Zj)](https://codecov.io/gh/unicef/unicef-security)
[![Coverage Stable](https://codecov.io/gh/unicef/unicef-security/branch/master/graph/badge.svg?token=sytM1cd8Zj)](https://codecov.io/gh/unicef/unicef-security)
[![Issue tracker](https://img.shields.io/github/issues/unicef/unicef-security.svg)](https://github.com/unicef/unicef-security/issues)

## Installation

```bash
pip install unicef-security
```

## Setup

Add `unicef_security` to `INSTALLED_APPS` in settings:

```python
INSTALLED_APPS = [
    'admin_extra_urls',
    'unicef_security',
]
```

## Contributing

### Environment Setup

To configure the development environment:

```bash
$ python manage.py upgrade --all
```

### Coding Standards

To run checks on the code to ensure code is in compliance:

```bash
$ ruff check
$ ruff format
```

### Testing

Testing is important and tests are located in `tests/` directory and can be run with:

```bash
$ uv run pytest test
```

Coverage report is viewable in `build/coverage` directory, and can be generated with:

```bash
$ pytest --cov=unicef_security --cov-report=html
```
