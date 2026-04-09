# Contributing to Vibing Linux

Thanks for your interest in contributing! Here's how to get started.

## Development setup

```bash
git clone https://github.com/VibeVoice/vibing-linux.git
cd vibing-linux
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest                        # all tests
pytest tests/unit/            # unit tests only
pytest tests/integration/     # integration tests only
pytest --cov=vibing           # with coverage
```

## Linting

```bash
ruff check vibing/ tests/     # lint
ruff check --fix vibing/      # auto-fix
ruff format vibing/ tests/    # format
```

## Code style

- **Python 3.10+** — use modern type hints (`dict[str, Any]`, `X | None`)
- **All imports must be at the top level** — no imports inside functions, methods, classes, `if` blocks, or `try` blocks
- **Ruff** is the linter and formatter — run it before committing
- Keep functions focused and avoid over-engineering

## Project structure

- `vibing/` — main application source
- `vibing/providers/` — pluggable ASR and LLM backends
- `tests/unit/` — unit tests (mocked dependencies)
- `tests/integration/` — integration tests (end-to-end with mocks)
- `packaging/` — `.deb` packaging configuration

## Pull requests

1. Fork the repo and create a feature branch from `main`
2. Make your changes with tests where appropriate
3. Ensure `ruff check` and `pytest` pass
4. Submit a PR with a clear description of the change

## Reporting bugs

Open an issue on GitHub with:
- Steps to reproduce
- Expected vs actual behavior
- System info (distro, Python version, GPU if relevant)

## Security

See [SECURITY.md](SECURITY.md) for reporting security vulnerabilities.
