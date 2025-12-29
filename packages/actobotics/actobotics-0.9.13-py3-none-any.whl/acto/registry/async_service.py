"""
Async versions of registry operations.

Example:
    ```python
    import asyncio
    from acto.registry.async_service import AsyncProofRegistry
    from acto.proof import ProofEnvelope

    async def main():
        async with AsyncProofRegistry() as registry:
            proof_id = await registry.upsert(envelope)
            proof = await registry.get(proof_id)
    ```
"""
from __future__ import annotations

import asyncio
from typing import Any

from acto.config.settings import Settings
from acto.proof.models import ProofEnvelope
from acto.registry.search import SearchFilter, SortField, SortOrder
from acto.registry.service import ProofRegistry


class AsyncProofRegistry:
    """
    Async wrapper for ProofRegistry operations.

    Can be used as an async context manager.

    Example:
        ```python
        import asyncio
        from acto.registry.async_service import AsyncProofRegistry
        from acto.proof import ProofEnvelope

        async def main():
            async with AsyncProofRegistry() as registry:
                proof_id = await registry.upsert(envelope)
                proof = await registry.get(proof_id)
                proofs = await registry.list(limit=10)
        ```
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self._registry: ProofRegistry | None = None

    async def __aenter__(self) -> AsyncProofRegistry:
        """Enter async context manager."""
        loop = asyncio.get_event_loop()
        self._registry = await loop.run_in_executor(None, ProofRegistry, self.settings)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and cleanup resources."""
        if self._registry:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._registry.__exit__, exc_type, exc_val, exc_tb)

    async def upsert(self, envelope: ProofEnvelope, tenant_id: str | None = None) -> str:
        """
        Upsert a proof envelope asynchronously.

        Args:
            envelope: Proof envelope to store
            tenant_id: Optional tenant ID

        Returns:
            str: Proof ID

        Example:
            ```python
            async with AsyncProofRegistry() as registry:
                proof_id = await registry.upsert(envelope)
            ```
        """
        if not self._registry:
            raise RuntimeError("Registry not initialized. Use async context manager.")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._registry.upsert, envelope, tenant_id)

    async def get(self, proof_id: str) -> ProofEnvelope:
        """
        Get a proof by ID asynchronously.

        Args:
            proof_id: Proof ID

        Returns:
            ProofEnvelope: Proof envelope

        Raises:
            RegistryError: If proof not found

        Example:
            ```python
            async with AsyncProofRegistry() as registry:
                proof = await registry.get(proof_id)
            ```
        """
        if not self._registry:
            raise RuntimeError("Registry not initialized. Use async context manager.")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._registry.get, proof_id)

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        search_filter: SearchFilter | None = None,
        sort_field: str = SortField.CREATED_AT,
        sort_order: str = SortOrder.DESC,
    ) -> list[dict[str, Any]]:
        """
        List proofs asynchronously.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            search_filter: Optional search filter
            sort_field: Field to sort by
            sort_order: Sort order (ASC or DESC)

        Returns:
            list[dict]: List of proof records

        Example:
            ```python
            async with AsyncProofRegistry() as registry:
                proofs = await registry.list(limit=10, offset=0)
            ```
        """
        if not self._registry:
            raise RuntimeError("Registry not initialized. Use async context manager.")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._registry.list, limit, offset, search_filter, sort_field, sort_order
        )

    async def search(
        self,
        search_text: str,
        limit: int = 50,
        offset: int = 0,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search proofs asynchronously.

        Args:
            search_text: Text to search for
            limit: Maximum number of results
            offset: Offset for pagination
            tenant_id: Optional tenant ID

        Returns:
            list[dict]: List of matching proof records

        Example:
            ```python
            async with AsyncProofRegistry() as registry:
                results = await registry.search("task-001", limit=10)
            ```
        """
        if not self._registry:
            raise RuntimeError("Registry not initialized. Use async context manager.")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._registry.search, search_text, limit, offset, tenant_id)

