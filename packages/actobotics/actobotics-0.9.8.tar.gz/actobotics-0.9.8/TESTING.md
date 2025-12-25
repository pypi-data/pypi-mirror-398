# Testing Guide

This document provides comprehensive information about testing in ACTO.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_api.py              # API endpoint tests
├── test_integration.py      # Integration tests for complete workflows
├── test_property_based.py   # Property-based tests using Hypothesis
├── test_fuzzing.py          # Fuzzing tests for parsers
├── test_pipeline.py         # Pipeline tests
├── test_proof_roundtrip.py  # Proof creation/verification tests
├── test_registry.py         # Registry tests
├── test_reputation.py       # Reputation scoring tests
└── load/                    # Load testing configurations
    ├── locustfile.py        # Locust load testing
    ├── k6_load_test.js      # k6 load testing
    └── k6_stress_test.js    # k6 stress testing
```

## Test Categories

### Unit Tests

Unit tests test individual functions and classes in isolation.

```bash
pytest -m unit
```

### Integration Tests

Integration tests verify complete workflows across multiple components.

```bash
pytest -m integration
```

Example scenarios:
- Parse telemetry → Create proof → Store in registry → Retrieve → Verify
- API submit → Registry storage → API retrieval → Verification
- Concurrent operations on registry

### Property-Based Tests

Property-based tests use Hypothesis to test invariants and edge cases.

```bash
pytest -m property
```

Properties tested:
- Any valid proof created should always be verifiable
- Different bundles produce different hashes
- Proof creation is deterministic for same input

### Fuzzing Tests

Fuzzing tests use various malformed and edge case inputs to find vulnerabilities.

```bash
pytest -m fuzz
```

Fuzzing scenarios:
- Malformed JSON/CSV inputs
- Large inputs
- Special characters and Unicode
- Deeply nested structures
- Invalid data types

## Test Coverage

### Running Coverage

```bash
# Generate coverage report
pytest --cov=acto --cov=acto_cli --cov=acto_server --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Coverage Targets

- **Overall**: Minimum 80% coverage
- **Critical paths**: 90%+ coverage
- **New code**: 100% coverage requirement

### Coverage Reports

Coverage reports are generated in multiple formats:
- **HTML**: `htmlcov/index.html` - Interactive HTML report
- **XML**: `coverage.xml` - For CI/CD integration
- **JSON**: `coverage.json` - For programmatic analysis
- **Terminal**: Inline coverage in test output

## Load Testing

### Locust

Locust is a Python-based load testing tool.

```bash
# Install
pip install locust

# Run with web UI
locust -f tests/load/locustfile.py --host=http://localhost:8080

# Run headless
locust -f tests/load/locustfile.py --host=http://localhost:8080 --headless -u 10 -r 2 -t 1m
```

### k6

k6 is a modern load testing tool.

```bash
# Install (macOS)
brew install k6

# Run load test
k6 run tests/load/k6_load_test.js

# Run stress test
k6 run tests/load/k6_stress_test.js

# Custom configuration
k6 run --vus 50 --duration 5m tests/load/k6_load_test.js
```

### Load Test Scenarios

1. **Balanced Workload**: Mix of read and write operations
2. **High Load Submission**: Focus on proof submissions
3. **Read Heavy**: Mostly read operations
4. **Stress Test**: Gradually increase load until system limits

## Security Testing

### Bandit

Bandit scans Python code for security vulnerabilities.

```bash
bandit -c .bandit -r acto acto_cli acto_server
```

### Safety

Safety checks dependencies for known vulnerabilities.

```bash
safety check
```

## Continuous Integration

All tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests

CI pipeline includes:
1. Unit tests (multiple Python versions)
2. Integration tests
3. Property-based tests
4. Fuzzing tests
5. Linting (Ruff)
6. Type checking (MyPy)
7. Security scanning (Bandit, Safety)
8. Coverage reporting
9. Load testing (on main branch)

## Writing Tests

### Test Naming

- Files: `test_*.py`
- Classes: `Test*`
- Functions: `test_*`

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_function():
    ...

@pytest.mark.integration
def test_workflow():
    ...

@pytest.mark.slow
def test_long_running():
    ...
```

### Fixtures

Shared fixtures are in `tests/conftest.py`:

- `temp_db_path`: Temporary database path
- `test_settings`: Test settings with temporary database
- `sample_telemetry_bundle`: Sample telemetry data

### Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures for setup/teardown
3. **Assertions**: Use descriptive assertion messages
4. **Coverage**: Aim for high coverage of critical paths
5. **Performance**: Keep unit tests fast (< 1s each)
6. **Documentation**: Document complex test scenarios

## Debugging Tests

### Verbose Output

```bash
pytest -v              # Verbose output
pytest -vv             # Very verbose
pytest -s              # Show print statements
```

### Running Specific Tests

```bash
# Run specific file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_api_submit_and_get

# Run tests matching pattern
pytest -k "test_api"
```

### Debugging Failed Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l
```

## Performance Testing

### Benchmarking

For performance-critical code, use pytest-benchmark:

```bash
pip install pytest-benchmark
pytest --benchmark-only
```

### Profiling

Profile slow tests:

```bash
pytest --profile
```

## Test Data

Test data should be:
- Minimal: Only include necessary data
- Realistic: Use realistic values
- Isolated: Don't depend on external services
- Deterministic: Same input should produce same output

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure package is installed in development mode
2. **Database Locked**: Use separate database files for each test
3. **Flaky Tests**: Ensure tests are properly isolated
4. **Slow Tests**: Mark slow tests with `@pytest.mark.slow`

### Getting Help

- Check test output for error messages
- Review `CONTRIBUTING.md` for development guidelines
- Open an issue for persistent problems

