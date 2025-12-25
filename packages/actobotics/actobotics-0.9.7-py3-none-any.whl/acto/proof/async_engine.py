"""
Async versions of proof creation functions.

Example:
    ```python
    import asyncio
    from acto.proof.async_engine import create_proof_async
    from acto.client import AsyncACTOClient
    from acto.telemetry.models import TelemetryBundle

    async def main():
        bundle = TelemetryBundle(...)
        envelope = await create_proof_async(
            bundle,
            private_key_b64="...",
            public_key_b64="..."
        )
        
        # Verify via API
        client = AsyncACTOClient(api_key="...", wallet_address="...")
        result = await client.verify(envelope)
    ```
"""
from __future__ import annotations

from typing import Any

from acto.config.settings import Settings
from acto.errors import ProofError
from acto.proof.engine import (
    create_proof as create_proof_sync,
)
from acto.proof.models import ProofEnvelope
from acto.telemetry.models import TelemetryBundle


async def create_proof_async(
    bundle: TelemetryBundle,
    signer_private_key_b64: str,
    signer_public_key_b64: str,
    settings: Settings | None = None,
    meta: dict[str, Any] | None = None,
) -> ProofEnvelope:
    """
    Create a proof envelope asynchronously.

    Args:
        bundle: Telemetry bundle to create proof from
        signer_private_key_b64: Base64-encoded private key for signing
        signer_public_key_b64: Base64-encoded public key
        settings: Optional settings override
        meta: Optional metadata dictionary

    Returns:
        ProofEnvelope: Created and signed proof envelope

    Example:
        ```python
        import asyncio
        from acto.proof.async_engine import create_proof_async
        from acto.telemetry.models import TelemetryBundle

        async def main():
            bundle = TelemetryBundle(
                task_id="task-001",
                robot_id="robot-001",
                telemetry=[...]
            )
            envelope = await create_proof_async(
                bundle,
                private_key_b64="...",
                public_key_b64="..."
            )
        ```
    """
    import asyncio

    settings = settings or Settings()
    meta = meta or {}

    # Run CPU-intensive operations in thread pool
    loop = asyncio.get_event_loop()

    def _create() -> ProofEnvelope:
        return create_proof_sync(
            bundle, signer_private_key_b64, signer_public_key_b64, settings, meta
        )

    return await loop.run_in_executor(None, _create)


async def verify_proof_async(envelope: ProofEnvelope) -> bool:
    """
    Verify a proof envelope via the ACTO API.

    .. deprecated::
        Local verification has been removed. Use AsyncACTOClient.verify() instead.

    Args:
        envelope: Proof envelope to verify

    Raises:
        ProofError: Always raises - use AsyncACTOClient.verify() instead

    Example:
        ```python
        from acto.client import AsyncACTOClient

        async def main():
            client = AsyncACTOClient(
                api_key="your-api-key",
                wallet_address="your-wallet-address"
            )
            result = await client.verify(envelope)
            print(f"Proof valid: {result.valid}")
        ```
    """
    raise ProofError(
        "Local verification has been removed. "
        "Please use the ACTO API for verification:\n\n"
        "  from acto.client import AsyncACTOClient\n"
        "  client = AsyncACTOClient(api_key='...', wallet_address='...')\n"
        "  result = await client.verify(envelope)\n\n"
        "Get your API key at: https://api.actobotics.net/dashboard"
    )

