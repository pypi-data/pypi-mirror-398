# Contributing to Structure Viewer

Thank you for your interest in contributing to Structure Viewer! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/crrrowz/structure-viewer.git
   cd structure-viewer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation**
   ```bash
   structure --version
   pytest
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=structure_viewer --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Use fixtures from `conftest.py` for common setups
- Aim for good coverage of edge cases

## 📝 Code Style

### Linting

We use `ruff` for linting:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### Type Checking

We use `mypy` for type checking:

```bash
mypy src/
```

### Formatting Guidelines

- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep lines under 100 characters
- Use meaningful variable names

## 🔄 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Run checks locally**
   ```bash
   ruff check src/ tests/
   mypy src/
   pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   
   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a Pull Request on GitHub.

## 📋 Issue Guidelines

### Reporting Bugs

Please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

### Feature Requests

Please include:
- Clear description of the feature
- Use cases and examples
- Any implementation ideas (optional)

## 📁 Project Structure

```
structure-viewer/
├── src/
│   └── structure_viewer/
│       ├── __init__.py      # Package exports
│       ├── __main__.py      # Entry point
│       ├── cli.py           # CLI implementation
│       ├── core.py          # Core logic
│       ├── config.py        # Configuration
│       ├── formatters.py    # Output formatters
│       └── colors.py        # Terminal colors
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_core.py
│   ├── test_cli.py
│   └── test_formatters.py
├── .github/
│   └── workflows/
│       └── ci.yml           # CI configuration
├── pyproject.toml           # Build configuration
├── README.md
├── CONTRIBUTING.md          # This file
├── CHANGELOG.md
└── LICENSE
```

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 💬 Questions?

Feel free to open an issue for any questions or discussions!
