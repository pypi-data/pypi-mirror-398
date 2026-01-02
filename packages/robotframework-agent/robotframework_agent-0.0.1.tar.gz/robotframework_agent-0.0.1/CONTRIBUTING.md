## Contributing

Thanks for your interest in improving Robot Framework Agent.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/utest -v
```

### Code style

```bash
make format
make lint
```

### Pull requests

- Keep changes small and focused
- Add/update unit tests when relevant
- Avoid committing large generated artifacts (screenshots, reports)
