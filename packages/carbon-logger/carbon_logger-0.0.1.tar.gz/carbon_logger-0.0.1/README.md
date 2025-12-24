# carbon-logger (Digital Carbon Labels placeholder)

This directory contains the placeholder Python distribution that reserves the `carbon-logger` name on PyPI.
The legacy `carbon_logger` module is still exported for compatibility, but APIs may change without
notice once the full Digital Carbon Labels SDK ships.

## Layout
```
python/
├── pyproject.toml
├── README.md
├── src/carbon_logger/
└── tests/
```

## Local development
1. Create a Python 3.11 virtual environment.
2. Install dev tooling: `pip install -e ".[dev]"` (after we reintroduce extras).
3. Run `pytest` to execute smoke tests.

## Publishing
1. Copy `.env.example` to `.env` and supply `PYPI_API_TOKEN`.
2. `python -m pip install --upgrade build twine`
3. `python -m build`
4. `python -m twine upload dist/*`

The GitHub publish workflow performs the same steps automatically on release.
