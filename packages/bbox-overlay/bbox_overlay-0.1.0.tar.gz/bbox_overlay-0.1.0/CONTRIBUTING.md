# Contributing

Thanks for helping improve bbox-overlay!

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
```

## Quality checks

```bash
ruff check .
ruff format .
mypy bbox_overlay
pytest
```

## Guidelines

- Keep CLI behavior backwards compatible.
- Add tests for new parsing or validation logic.
- Document user-facing changes in `CHANGELOG.md`.
