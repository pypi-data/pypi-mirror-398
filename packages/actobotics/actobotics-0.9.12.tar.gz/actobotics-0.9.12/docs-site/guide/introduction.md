# What is ACTO?

ACTO is a **robotics-first proof-of-execution toolkit** that enables you to generate deterministic, cryptographically signed proofs from robot telemetry and execution logs.

## The Problem

In robotics and automation, there's often no way to prove that a robot actually performed a task correctly. Traditional logging lacks:

- **Integrity** - Logs can be modified after the fact
- **Authentication** - No way to verify who/what generated the data
- **Portability** - Logs are often in proprietary formats
- **Verifiability** - No cryptographic guarantees

## The Solution

ACTO provides a standardized protocol for creating **execution proofs** that are:

| Property | Description |
|----------|-------------|
| **Deterministic** | Same input always produces the same proof |
| **Signed** | Ed25519 signatures prove authenticity |
| **Portable** | JSON envelope format works everywhere |
| **Verifiable** | Verify proofs via the ACTO API |

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Robot/Device   │     │   ACTO SDK      │     │   ACTO API      │
│                 │     │                 │     │                 │
│  Telemetry      │────▶│  Create Proof   │────▶│  Verify &       │
│  Sensor Data    │     │  Sign Envelope  │     │  Store Proof    │
│  Logs           │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Collect telemetry** from your robot during task execution
2. **Create a proof** using the SDK - this hashes and signs the data
3. **Verify via API** to ensure integrity and register in the fleet

## Key Components

### SDK (`pip install actobotics`)

The Python SDK provides:

- Proof creation with Ed25519 signatures
- BLAKE3 hashing for deterministic digests
- Telemetry normalization and validation
- API client for verification and fleet management

### API (`api.actobotics.net`)

The hosted API provides:

- Proof verification (required)
- Proof registry and search
- Fleet management
- Wallet statistics
- Token-gated access

### Dashboard

Web-based interface for:

- API key management
- Fleet monitoring
- Statistics and analytics
- API playground

## Use Cases

- **Proof of Work** - Prove robots completed assigned tasks
- **Compliance** - Audit trails for regulated industries
- **Quality Assurance** - Verify manufacturing processes
- **Fleet Tracking** - Monitor robot fleet health and activity
- **Insurance** - Provide evidence of proper operation

## Token Gating

Access to the ACTO API requires holding **50,000 ACTO tokens** in your Solana wallet. This ensures:

- Network sustainability
- Spam prevention
- Community alignment

::: tip Getting Started
Ready to create your first proof? Head to the [Quick Start](/guide/quickstart) guide.
:::

