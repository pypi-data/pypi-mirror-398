# Installation

Install the ACTO SDK from PyPI.

## Requirements

- Python 3.9 or higher
- pip (Python package manager)

## Basic Installation

```bash
pip install actobotics
```

This installs the core SDK with:
- Proof creation and verification
- API client (`ACTOClient`, `AsyncACTOClient`)
- Cryptographic utilities
- CLI tools

## Optional Dependencies

### Solana Integration

For Solana-specific features (anchoring, token checks):

```bash
pip install actobotics[solana]
```

### Full Installation

Install all optional dependencies:

```bash
pip install actobotics[full]
```

This includes:
- Solana SDK
- Redis caching
- ROS integration
- Additional telemetry parsers

## Verify Installation

```python
import acto
print(acto.__version__)
```

Or via CLI:

```bash
acto --version
```

## Development Installation

For contributors who want to modify the SDK:

```bash
# Clone the repository
git clone https://github.com/actobotics/ACTO.git
cd ACTO

# Install in development mode
pip install -e ".[dev]"
```

This includes:
- pytest for testing
- black/ruff for formatting
- mypy for type checking

## Virtual Environment

We recommend using a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install ACTO
pip install actobotics
```

## Docker

Run ACTO in a Docker container:

```bash
docker run -it python:3.11-slim bash -c "pip install actobotics && acto --version"
```

## Troubleshooting

### ImportError: No module named 'acto'

Make sure you installed the package:
```bash
pip install actobotics
```

Note: The PyPI package is `actobotics`, but you import it as `acto`.

### SSL Certificate Errors

If you encounter SSL errors:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org actobotics
```

### Version Conflicts

Use a fresh virtual environment to avoid conflicts:
```bash
python -m venv clean_env
source clean_env/bin/activate
pip install actobotics
```

