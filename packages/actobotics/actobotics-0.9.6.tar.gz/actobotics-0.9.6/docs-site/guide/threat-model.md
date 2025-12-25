# Threat Model

Understanding what ACTO proves and what it doesn't.

## What ACTO Proves

ACTO proofs verify:

| Property | Proof |
|----------|-------|
| **Data integrity** | Telemetry hasn't been modified |
| **Authenticity** | Signed by a specific key |
| **Timestamp** | When the proof was created |
| **Association** | Telemetry belongs to claimed task |

## What ACTO Doesn't Prove

ACTO does **not** prove:

| Non-Property | Explanation |
|--------------|-------------|
| **Physical reality** | Telemetry accurately reflects real events |
| **Task completion** | Robot actually completed the task |
| **Data accuracy** | Sensor readings are correct |
| **Time of execution** | Task happened at claimed time |

::: warning Important
ACTO proves the **integrity of records**, not the **truth of the underlying reality**.
:::

## Threat Analysis

### Threat 1: Fabricated Telemetry

**Risk**: Attacker creates fake telemetry data

**Mitigation**:
- ACTO doesn't prevent this
- Use hardware-backed sensors
- Cross-reference with external systems
- Implement physical attestation

### Threat 2: Key Compromise

**Risk**: Private key is stolen

**Mitigation**:
- Use hardware security modules (HSM)
- Implement key rotation
- Monitor for unauthorized signatures
- Revoke compromised keys

### Threat 3: Replay Attacks

**Risk**: Valid proof resubmitted for different context

**Mitigation**:
- Unique task_id and run_id
- Timestamp validation
- Nonce in metadata
- Proof chaining

### Threat 4: Man-in-the-Middle

**Risk**: API communication intercepted

**Mitigation**:
- HTTPS only
- Certificate validation
- Request signing (optional)

### Threat 5: Timestamp Manipulation

**Risk**: Proof created with false timestamp

**Mitigation**:
- Timestamp is in signed payload
- Server records submission time
- Solana anchoring for immutability
- Time window validation

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                  Defense in Depth                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Cryptographic Integrity                            │
│  ├── BLAKE3 hashing                                          │
│  └── Ed25519 signatures                                      │
│                                                              │
│  Layer 2: Access Control                                     │
│  ├── API key authentication                                  │
│  ├── Token gating (50,000 ACTO)                             │
│  └── Rate limiting                                           │
│                                                              │
│  Layer 3: Audit Trail                                        │
│  ├── All verifications logged                                │
│  ├── Submission timestamps                                   │
│  └── Wallet tracking                                         │
│                                                              │
│  Layer 4: Optional Anchoring                                 │
│  └── Solana blockchain immutability                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Hardening Options

### Hardware-Backed Keys

Use secure elements for key storage:

```python
# Example with HSM
from acto.crypto import KeyPair

# Generate key in HSM (implementation-dependent)
keypair = KeyPair.from_hsm(hsm_client, key_id="robot-001")
```

### Secure Telemetry Pipeline

```
Sensors → Secure MCU → Signed telemetry → ACTO proof
```

- Use trusted execution environments
- Sign telemetry at source
- Validate sensor calibration

### External Attestation

Combine ACTO with external verification:

- Camera footage
- Third-party observers
- IoT sensor networks
- GPS tracking

### Solana Anchoring

For maximum immutability:

```python
from acto.anchor import anchor_proof

tx_sig = anchor_proof(envelope, wallet)
# Proof hash now on Solana blockchain
```

## Risk Assessment Matrix

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Fabricated data | Medium | High | External attestation |
| Key compromise | Low | Critical | HSM, rotation |
| Replay attack | Low | Medium | Unique IDs, chaining |
| MITM | Very Low | Medium | TLS, cert pinning |
| Timestamp fraud | Medium | Low | Anchoring, validation |

## Recommendations by Use Case

### Low Risk (R&D, Testing)
- Basic ACTO proofs
- Standard key management
- API authentication

### Medium Risk (Production)
- Hardware key storage
- Audit logging
- Proof chaining
- Regular key rotation

### High Risk (Compliance, Legal)
- HSM for all keys
- Solana anchoring
- External attestation
- Comprehensive audit trail
- Regular security audits

