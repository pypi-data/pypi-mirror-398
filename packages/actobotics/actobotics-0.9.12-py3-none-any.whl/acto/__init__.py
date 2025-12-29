"""
ACTO: Robotics Proof-of-Execution Toolkit.

Public API entrypoints:
- acto.client (API client for hosted service)
- acto.proof (create/verify proofs locally)
- acto.crypto (keys/signatures/hashes)
- acto.telemetry (parsers/normalizers)
- acto.registry (SQLite-backed local proof registry)

Quick Start with Hosted API:
    >>> from acto.client import ACTOClient
    >>> from acto.proof import create_proof
    >>> from acto.crypto import KeyPair
    >>> from acto.telemetry import TelemetryBundle, TelemetryEvent
    >>> 
    >>> # Create proof locally
    >>> keypair = KeyPair.generate()
    >>> bundle = TelemetryBundle(
    ...     task_id="task-001",
    ...     robot_id="robot-001",
    ...     events=[TelemetryEvent(ts="2025-01-01T00:00:00Z", topic="sensor", data={"value": 42})]
    ... )
    >>> envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
    >>> 
    >>> # Submit to hosted API
    >>> client = ACTOClient(api_key="...", wallet_address="...")
    >>> proof_id = client.submit_proof(envelope)
"""
from .version import __version__

__all__ = ["__version__"]
