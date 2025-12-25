# Self-Hosting

Run your own ACTO server for development or private deployments.

::: warning For Contributors
Self-hosting is primarily for contributors and special use cases. For most users, we recommend the hosted API at `api.actobotics.net`.
:::

## Requirements

- Python 3.9+
- PostgreSQL (recommended) or SQLite
- Redis (optional, for caching)

## Installation

```bash
# Clone the repository
git clone https://github.com/actobotics/ACTO.git
cd ACTO

# Install with server dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Run with default settings (SQLite)
acto server run

# Or with uvicorn directly
uvicorn acto_server.app:app --reload --port 8080
```

Server runs at `http://localhost:8080`

## Configuration

Create a configuration file:

```toml
# config.toml

# Server settings
host = "0.0.0.0"
port = 8080
workers = 4

# Database
db_url = "postgresql://user:pass@localhost/acto"
# Or SQLite: db_url = "sqlite:///./data/acto.sqlite"

# JWT
jwt_secret_key = "your-secret-key-here"
jwt_algorithm = "HS256"

# Token gating (optional)
token_gating_enabled = true
acto_token_mint = "your-token-mint"
minimum_balance = 50000

# Helius RPC (optional)
helius_api_key = "your-helius-key"
```

Run with config:

```bash
acto server run --config config.toml
```

## Docker

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  acto:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ACTO_DB_URL=postgresql://postgres:postgres@db/acto
      - ACTO_JWT_SECRET_KEY=your-secret
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=acto
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run:

```bash
docker-compose up -d
```

### Using Dockerfile

```bash
docker build -t acto .
docker run -p 8080:8080 -e ACTO_JWT_SECRET_KEY=secret acto
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACTO_DB_URL` | Database connection URL | SQLite in ./data |
| `ACTO_JWT_SECRET_KEY` | JWT signing key | Random (dev only) |
| `ACTO_LOG_LEVEL` | Logging level | INFO |
| `ACTO_TOKEN_GATING_ENABLED` | Enable token gating | true |
| `ACTO_HELIUS_API_KEY` | Helius RPC API key | - |

## Database Setup

### PostgreSQL

```bash
# Create database
createdb acto

# Run migrations
alembic upgrade head
```

### SQLite

SQLite works out of the box - database is created automatically.

## Production Deployment

### With Gunicorn

```bash
gunicorn acto_server.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080
```

### With Nginx

```nginx
upstream acto {
    server 127.0.0.1:8080;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    location / {
        proxy_pass http://acto;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Testing

```bash
# Run test suite
pytest

# With coverage
pytest --cov=acto --cov-report=html

# Load tests
locust -f tests/load/locustfile.py
```

## Limitations

Self-hosted servers:
- Don't have official token verification
- Require your own RPC for token gating
- Need manual security configuration
- Are not supported by the ACTO team

For production use, we recommend the hosted API.

