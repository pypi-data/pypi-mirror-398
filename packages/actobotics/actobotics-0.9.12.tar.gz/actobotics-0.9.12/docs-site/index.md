---
layout: home

hero:
  text: Robotics-first proof-of-execution toolkit
  tagline: Generate deterministic, signed execution proofs from robot telemetry. Verify via API. Fast, gas-free verification.
  image:
    src: /logo.svg
    alt: ACTO Logo
  actions:
    - theme: brand
      text: Get Started
      link: /guide/quickstart
    - theme: alt
      text: View on GitHub
      link: https://github.com/actobotics/ACTO
    - theme: alt
      text: API Reference
      link: /api/overview

features:
  - icon: 🔐
    title: Cryptographic Proofs
    details: Ed25519 signatures over deterministic hashes ensure tamper-proof execution records.
  - icon: ⚡
    title: Gas-Free Verification
    details: Fast off-chain verification without blockchain transaction fees. Optional Solana anchoring.
  - icon: 🐍
    title: Python SDK
    details: Simple SDK for proof creation and API integration. Available on PyPI as `actobotics`.
  - icon: 🤖
    title: Fleet Management
    details: Monitor and organize your robot fleet with drag-and-drop, health metrics, device groups, and activity tracking.
  - icon: 🔑
    title: Token Gating
    details: SPL token-based access control. Verify wallet balances via Helius RPC.
  - icon: 🛡️
    title: Enterprise Security
    details: JWT authentication, RBAC, audit logging, encryption at rest, and PII masking.
---

## Quick Example

```python
from acto.client import ACTOClient
from acto.proof import create_proof
from acto.crypto import KeyPair
from acto.telemetry.models import TelemetryBundle, TelemetryEvent

# Generate keypair
keypair = KeyPair.generate()

# Create telemetry bundle
bundle = TelemetryBundle(
    task_id="pick-and-place-001",
    robot_id="robot-alpha-01",
    events=[
        TelemetryEvent(
            ts="2025-01-15T10:30:00Z",
            topic="sensor",
            data={"value": 42}
        )
    ]
)

# Create proof locally
envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)

# Connect to API and verify
client = ACTOClient(
    api_key="acto_xxx...",
    wallet_address="YOUR_WALLET"
)

result = client.verify(envelope)
print(f"Valid: {result.valid}")
```

## Links

<div class="link-cards">
  <a href="https://api.actobotics.net/dashboard" class="link-card">
    <span class="title">Dashboard</span>
    <span class="desc">Manage API keys and view statistics</span>
  </a>
  <a href="https://pypi.org/project/actobotics/" class="link-card">
    <span class="title">PyPI</span>
    <span class="desc">pip install actobotics</span>
  </a>
  <a href="https://github.com/actobotics/ACTO" class="link-card">
    <span class="title">GitHub</span>
    <span class="desc">Source code and issues</span>
  </a>
  <a href="https://x.com/actoboticsnet" class="link-card">
    <span class="title">X (Twitter)</span>
    <span class="desc">@actoboticsnet</span>
  </a>
</div>

<style>
.link-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 24px;
}

.link-card {
  display: flex;
  flex-direction: column;
  padding: 20px;
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  text-decoration: none;
  transition: all 0.2s ease;
}

.link-card:hover {
  border-color: var(--vp-c-text-1);
  background: var(--vp-c-text-1);
  transform: translateY(-2px);
}

.link-card:hover .title,
.link-card:hover .desc {
  color: #ffffff;
}

.link-card .icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.link-card .title {
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin-bottom: 4px;
}

.link-card .desc {
  font-size: 13px;
  color: var(--vp-c-text-2);
}
</style>

