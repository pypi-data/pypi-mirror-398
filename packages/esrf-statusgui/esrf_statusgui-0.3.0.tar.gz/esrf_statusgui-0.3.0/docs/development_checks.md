# Code Quality Checks

This project ships a `.[dev]` extra that bundles the full tooling stack
(`black`, `ruff`, `flake8`, `mypy`, `bandit`, `pytest`, etc.). Install it once
inside your virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Pre-commit hooks

The repository contains a pre-commit configuration (`.pre-commit-config.yaml`)
that runs the core checks on every commit.

```bash
pre-commit install                 # run hooks automatically on commit
pre-commit run --all-files         # manually lint/format the whole tree
```

Hooks executed:

- `black` – formats Python files using the project settings in `pyproject.toml`.
- `ruff` – fixes import order and catches pycodestyle/pyflakes/bugbear issues.
- `flake8` – runs additional style checks with the `flake8-pep585` plugin.
- `mypy` – type-checks using the `[tool.mypy]` section in `pyproject.toml`.
- `bandit` – performs a security scan over `src/`.
- Utility hooks – verify whitespace, TOML syntax, and prevent stray large files.

If any hook rewrites files, re-stage them (`git add -u`) and rerun
`pre-commit` until everything passes.

## Manual safety net

For larger changes, or when CI is unavailable, run the core commands directly:

```bash
black src tests
ruff check src tests
flake8 src tests
mypy src tests
bandit -r src
pytest --cov=esrf_statusgui
```

Each tool reads its configuration from `pyproject.toml`, so no extra flags are
required beyond the command above. Running the suite before opening a merge
request keeps the main branch green and avoids churn in GitLab CI pipelines.
