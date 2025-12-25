# Architecture

ACTO's architecture consists of three main layers.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Applications                        │
│  (Python scripts, ROS nodes, automation systems)                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SDK Layer (acto package)                      │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Proof     │  │    Crypto    │  │  Telemetry   │          │
│  │   Engine     │  │    Module    │  │   Parsers    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  API Client  │  │   Registry   │  │   Security   │          │
│  │ (sync/async) │  │    Store     │  │    Layer     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer (acto_server)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Proofs    │  │    Auth     │  │    Fleet    │            │
│  │   Router    │  │   Router    │  │   Router    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               Database (SQLite/PostgreSQL)               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Details

### 1. SDK Layer (`acto/`)

The SDK is published to PyPI as `actobotics` and provides:

| Module | Purpose |
|--------|---------|
| `acto/proof/` | Proof creation, verification, chaining |
| `acto/crypto/` | Keys, signing, hashing (BLAKE3, Ed25519) |
| `acto/telemetry/` | Parsing, normalization, validation |
| `acto/client/` | API client (sync and async) |
| `acto/registry/` | Local proof storage |
| `acto/security/` | JWT, RBAC, encryption, audit |
| `acto/fleet/` | Fleet management models |

### 2. CLI Layer (`acto_cli/`)

Command-line interface built with Typer:

```
acto_cli/
├── main.py           # Entry point
└── commands/
    ├── keys.py       # Key management
    ├── proof.py      # Proof operations
    ├── registry.py   # Registry commands
    ├── access.py     # Token gating
    ├── server.py     # Server management
    └── interactive.py # Interactive mode
```

### 3. API Layer (`acto_server/`)

FastAPI server deployed to Vercel:

```
acto_server/
├── app.py            # FastAPI application
├── schemas.py        # Pydantic schemas
├── routers/
│   ├── auth.py       # Wallet authentication
│   ├── proofs.py     # Proof endpoints
│   ├── keys.py       # API key management
│   ├── fleet.py      # Fleet management
│   ├── access.py     # Token gating
│   └── stats.py      # Statistics
└── static/           # Dashboard assets
```

## Data Flow

### Proof Creation Flow

```
1. Collect telemetry events
        │
        ▼
2. Create TelemetryBundle
        │
        ▼
3. Normalize telemetry (canonical JSON)
        │
        ▼
4. Hash telemetry (BLAKE3) → telemetry_hash
        │
        ▼
5. Create ProofPayload
        │
        ▼
6. Hash payload (BLAKE3) → payload_hash
        │
        ▼
7. Sign payload_hash (Ed25519) → signature
        │
        ▼
8. Create ProofEnvelope
```

### Verification Flow

```
1. Receive ProofEnvelope
        │
        ▼
2. Extract payload_hash
        │
        ▼
3. Canonicalize and hash payload
        │
        ▼
4. Compare hashes (integrity check)
        │
        ▼
5. Verify Ed25519 signature
        │
        ▼
6. Return valid/invalid
```

## Security Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Request Flow                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Client Request                                             │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────┐                                       │
│  │   Rate Limiter  │ ─── 5 req/s, burst 20                │
│  └─────────────────┘                                       │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────┐                                       │
│  │  Auth Middleware │ ─── API Key / JWT validation         │
│  └─────────────────┘                                       │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────┐                                       │
│  │  Token Gating   │ ─── Check 50,000 ACTO balance        │
│  └─────────────────┘                                       │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────┐                                       │
│  │  Route Handler  │ ─── Process request                   │
│  └─────────────────┘                                       │
│       │                                                     │
│       ▼                                                     │
│  Response                                                   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

## Database Schema

### Proofs Table

```sql
CREATE TABLE proofs (
    id TEXT PRIMARY KEY,           -- payload_hash
    task_id TEXT NOT NULL,
    robot_id TEXT,
    run_id TEXT,
    signer_public_key TEXT NOT NULL,
    envelope_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wallet_address TEXT NOT NULL
);
```

### Fleet Tables

```sql
CREATE TABLE fleet_devices (
    id TEXT PRIMARY KEY,           -- robot_id
    wallet_address TEXT NOT NULL,
    custom_name TEXT,
    group_id TEXT REFERENCES fleet_groups(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fleet_groups (
    id TEXT PRIMARY KEY,
    wallet_address TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fleet_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Design Principles

### Fast, Gas-Free Verification

All verification happens off-chain with cryptographic primitives:
- No blockchain transactions for verification
- Sub-millisecond verification time
- Optional Solana anchoring for immutability

### Deterministic Hashing

Same input always produces the same proof:
- Canonical JSON serialization
- BLAKE3 hashing
- Reproducible across systems

### Security First

Defense in depth:
- API key authentication
- JWT for session management
- Token gating for access control
- Rate limiting
- Audit logging

### Modular Design

Clean separation of concerns:
- SDK is independent of server
- CLI uses SDK
- Server uses SDK
- Components are testable in isolation

