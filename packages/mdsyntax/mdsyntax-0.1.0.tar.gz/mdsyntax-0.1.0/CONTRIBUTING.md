# Contributing to mdsyntax

Thanks for your interest in contributing!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Azaias/mdsyntax.git
   cd mdsyntax
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

3. Install in editable mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

This project uses [ruff](https://github.com/astral-sh/ruff) for linting:

```bash
pip install ruff
ruff check src/
ruff format src/
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with a descriptive message
6. Push to your fork
7. Open a Pull Request

## Reporting Issues

Please include:
- Python version
- OS and terminal
- Minimal code to reproduce
- Expected vs actual behavior
