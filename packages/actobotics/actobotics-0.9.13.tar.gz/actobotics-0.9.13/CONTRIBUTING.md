# Contributing to ACTO

Thank you for your interest in contributing to ACTO! This document provides guidelines and instructions for contributing.

> **Note for SDK Users:** If you just want to use the SDK, install it from PyPI with `pip install actobotics`. This guide is for contributors who want to develop ACTO itself.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip
- git

### Installation (Full Repository)

1. Clone the repository:
```bash
git clone https://github.com/actobotics/ACTO.git
cd ACTO
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=acto --cov=acto_cli --cov=acto_server --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration    # Integration tests only
pytest -m property       # Property-based tests
pytest -m fuzz          # Fuzzing tests

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_proof_roundtrip.py
```

### Test Coverage

We aim for at least 80% code coverage. Check coverage reports:

```bash
pytest --cov=acto --cov=acto_cli --cov=acto_server --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Code Quality

### Linting

We use Ruff for linting and formatting:

```bash
# Check for issues
ruff check acto acto_cli acto_server tests

# Auto-fix issues
ruff check --fix acto acto_cli acto_server tests

# Format code
ruff format acto acto_cli acto_server tests
```

### Type Checking

We use MyPy for type checking:

```bash
mypy acto acto_cli acto_server --ignore-missing-imports
```

### Security Scanning

We use Bandit and Safety for security checks:

```bash
# Bandit (code security)
bandit -c .bandit -r acto acto_cli acto_server

# Safety (dependency vulnerabilities)
safety check
```

### Pre-commit Hooks

Pre-commit hooks run automatically on commit. To run manually:

```bash
pre-commit run --all-files
```

## Writing Tests

### Test Structure

- Unit tests: Test individual functions and classes in isolation
- Integration tests: Test complete workflows across multiple components
- Property-based tests: Use Hypothesis to test invariants
- Fuzzing tests: Test parsers and input handling with edge cases

### Test Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    ...

@pytest.mark.integration
def test_workflow():
    ...

@pytest.mark.slow
def test_long_running():
    ...
```

## Code Style

### General Guidelines

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Use meaningful variable and function names

### Formatting

Code is automatically formatted with Ruff. The configuration is in `pyproject.toml`.

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

3. **Ensure all tests pass**:
   ```bash
   pytest
   ruff check acto acto_cli acto_server tests
   mypy acto acto_cli acto_server
   ```

4. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

### PR Checklist

- [ ] All tests pass
- [ ] Code is properly formatted (Ruff)
- [ ] Type checking passes (MyPy)
- [ ] Security scans pass (Bandit, Safety)
- [ ] Test coverage is maintained or improved
- [ ] Documentation is updated if needed
- [ ] CHANGELOG is updated (if applicable)

## Load Testing

For performance-related changes, run load tests:

```bash
# Locust
locust -f tests/load/locustfile.py --host=http://localhost:8080 --headless -u 10 -r 2 -t 1m

# k6 (if installed)
k6 run tests/load/k6_load_test.js
```

## Documentation

- Update docstrings for any new or modified functions
- Update README.md if adding new features
- Update architecture docs if making structural changes

## Questions?

Feel free to open an issue or contact the maintainers if you have questions about contributing.

