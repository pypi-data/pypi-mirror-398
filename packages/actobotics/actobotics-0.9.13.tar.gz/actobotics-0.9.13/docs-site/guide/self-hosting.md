# Development Setup

::: danger Not for End Users
This page is **only for ACTO contributors** working on the codebase itself.

**Regular users should NOT self-host.** Use the hosted platform:
- **Dashboard:** [api.actobotics.net/dashboard](https://api.actobotics.net/dashboard)
- **API:** `https://api.actobotics.net`

The ACTO team handles all hosting, scaling, and infrastructure.
:::

## For Contributors Only

If you're contributing to the ACTO project and need to run the server locally for development:

### Prerequisites

- Python 3.10+
- Git

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/actobotics/ACTO.git
cd ACTO

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# Install dev dependencies
pip install -e ".[dev]"

# Run the server locally
uvicorn acto_server.app:app --reload --port 8080
```

### Running Tests

```bash
# Run test suite
pytest

# With coverage
pytest --cov=acto --cov-report=html

# Type checking
mypy acto

# Linting
ruff check acto
```

### Environment Variables (Development)

For local development, you can use a `.env` file:

```bash
# .env (development only)
ACTO_LOG_LEVEL=DEBUG
ACTO_DB_URL=sqlite:///./data/acto.sqlite
ACTO_JWT_SECRET_KEY=dev-secret-not-for-production
```

## Production Infrastructure

The production ACTO infrastructure is managed by the ACTO team and includes:

- Vercel deployment with edge functions
- PostgreSQL database (managed)
- Helius RPC for Solana token verification
- Automatic scaling and monitoring
- SSL/TLS encryption
- DDoS protection

**Contributors do not need to worry about production deployment** - just submit your PR and the team handles the rest.

## Questions?

- **Contributing:** See [CONTRIBUTING.md](https://github.com/actobotics/ACTO/blob/main/CONTRIBUTING.md)
- **Issues:** Open an issue on GitHub
- **API Questions:** Use the hosted dashboard at `api.actobotics.net`
