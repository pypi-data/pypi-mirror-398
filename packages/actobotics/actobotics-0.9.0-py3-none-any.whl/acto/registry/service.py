from __future__ import annotations

import hashlib
from pathlib import Path

import orjson
from sqlalchemy import select

from acto.cache import get_cache_backend
from acto.config.settings import Settings
from acto.errors import RegistryError
from acto.proof.models import ProofEnvelope
from acto.registry.db import make_engine, make_session_factory
from acto.registry.models import Base, ProofRecord
from acto.registry.search import (
    SearchFilter,
    SortField,
    SortOrder,
    apply_sorting,
    extract_searchable_metadata,
)


def _proof_id_from_hash(payload_hash: str) -> str:
    return hashlib.sha256(payload_hash.encode("utf-8")).hexdigest()[:32]


def _cache_key_proof(proof_id: str) -> str:
    """Generate cache key for a proof."""
    return f"proof:{proof_id}"


def _cache_key_list(limit: int, offset: int = 0) -> str:
    """Generate cache key for proof list."""
    return f"proofs:list:{limit}:{offset}"


class ProofRegistry:
    """
    Database-backed registry for proofs with optional caching.

    Can be used as a context manager for automatic resource cleanup.

    Example:
        ```python
        from acto.registry import ProofRegistry
        from acto.proof import ProofEnvelope

        # Regular usage
        registry = ProofRegistry()
        proof_id = registry.upsert(envelope)

        # Context manager usage
        with ProofRegistry() as registry:
            proof_id = registry.upsert(envelope)
            proof = registry.get(proof_id)
        ```
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.engine = make_engine(self.settings)
        self.SessionLocal = make_session_factory(self.engine)
        self.cache = get_cache_backend(self.settings)
        Base.metadata.create_all(self.engine)

    def __enter__(self) -> ProofRegistry:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and cleanup resources."""
        if self.engine:
            self.engine.dispose()

    def upsert(self, envelope: ProofEnvelope, tenant_id: str | None = None) -> str:
        """
        Upsert a proof envelope into the registry.

        Args:
            envelope: Proof envelope to store or update
            tenant_id: Optional tenant ID for multi-tenant scenarios

        Returns:
            str: Proof ID (derived from payload hash)

        Example:
            ```python
            from acto.registry import ProofRegistry
            from acto.proof import ProofEnvelope

            registry = ProofRegistry()
            proof_id = registry.upsert(envelope)
            print(f"Stored proof: {proof_id}")
            ```
        """
        proof_id = _proof_id_from_hash(envelope.payload.payload_hash)
        cache_key = _cache_key_proof(proof_id)
        try:
            envelope_json_str = orjson.dumps(envelope.model_dump()).decode("utf-8")
            metadata_search = extract_searchable_metadata(envelope_json_str)

            with self.SessionLocal() as session:
                existing = session.get(ProofRecord, proof_id)
                if existing:
                    existing.envelope_json = envelope_json_str
                    existing.anchor_ref = envelope.anchor_ref
                    existing.metadata_search = metadata_search
                    if tenant_id:
                        existing.tenant_id = tenant_id
                else:
                    rec = ProofRecord(
                        proof_id=proof_id,
                        task_id=envelope.payload.subject.task_id,
                        robot_id=envelope.payload.subject.robot_id,
                        run_id=envelope.payload.subject.run_id,
                        created_at=envelope.payload.created_at,
                        payload_hash=envelope.payload.payload_hash,
                        signer_public_key_b64=envelope.signer_public_key_b64,
                        signature_b64=envelope.signature_b64,
                        envelope_json=envelope_json_str,
                        anchor_ref=envelope.anchor_ref,
                        tenant_id=tenant_id,
                        metadata_search=metadata_search,
                    )
                    session.add(rec)
                session.commit()

            # Invalidate cache for this proof and list caches
            if self.cache:
                self.cache.set(cache_key, envelope.model_dump(), ttl=self.settings.cache_ttl)
                # Invalidate list caches (we use a simple approach: clear all list caches)
                # In production, you might want a more sophisticated cache invalidation strategy

            return proof_id
        except Exception as e:
            raise RegistryError(str(e)) from e

    def get(self, proof_id: str) -> ProofEnvelope:
        """
        Get a proof by ID from the registry.

        Args:
            proof_id: Proof ID to retrieve

        Returns:
            ProofEnvelope: Retrieved proof envelope

        Raises:
            RegistryError: If proof not found

        Example:
            ```python
            from acto.registry import ProofRegistry

            registry = ProofRegistry()
            try:
                proof = registry.get("abc123...")
                print(f"Found proof: {proof.payload.subject.task_id}")
            except RegistryError as e:
                print(f"Proof not found: {e}")
            ```
        """
        # Try cache first
        cache_key = _cache_key_proof(proof_id)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return ProofEnvelope.model_validate(cached)

        # Cache miss, fetch from database
        with self.SessionLocal() as session:
            rec = session.get(ProofRecord, proof_id)
            if not rec:
                raise RegistryError("Proof not found.")
            envelope = ProofEnvelope.model_validate(orjson.loads(rec.envelope_json))

        # Store in cache
        if self.cache:
            self.cache.set(cache_key, envelope.model_dump(), ttl=self.settings.cache_ttl)

        return envelope

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        search_filter: SearchFilter | None = None,
        sort_field: str = SortField.CREATED_AT,
        sort_order: str = SortOrder.DESC,
    ) -> list[dict]:
        with self.SessionLocal() as session:
            stmt = select(ProofRecord)

            # Wende Filter an
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())

            # Wende Sortierung an
            stmt = apply_sorting(stmt, sort_field, sort_order)

            # Wende Pagination an
            stmt = stmt.limit(limit).offset(offset)

            rows = session.execute(stmt).scalars().all()
            return [
                {
                    "proof_id": r.proof_id,
                    "task_id": r.task_id,
                    "robot_id": r.robot_id,
                    "run_id": r.run_id,
                    "created_at": r.created_at,
                    "payload_hash": r.payload_hash,
                    "anchor_ref": r.anchor_ref,
                    "tenant_id": r.tenant_id,
                }
                for r in rows
            ]

    def search(
        self,
        search_text: str,
        limit: int = 50,
        offset: int = 0,
        tenant_id: str | None = None,
    ) -> list[dict]:
        """Full-text search in proofs."""
        filter_obj = SearchFilter()
        filter_obj.search_text = search_text
        filter_obj.tenant_id = tenant_id
        return self.list(limit=limit, offset=offset, search_filter=filter_obj)

    def get_by_hash(self, payload_hash: str) -> ProofEnvelope:
        """Get a proof by payload hash."""
        proof_id = _proof_id_from_hash(payload_hash)
        return self.get(proof_id)

    def export_json(self, output_path: str, search_filter: SearchFilter | None = None) -> None:
        """Export proofs as JSON."""
        proofs = self.list(limit=10000, search_filter=search_filter)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(orjson.dumps(proofs, option=orjson.OPT_INDENT_2).decode("utf-8"), encoding="utf-8")

    def export_csv(self, output_path: str, search_filter: SearchFilter | None = None) -> None:
        """Export proofs as CSV."""
        import csv

        proofs = self.list(limit=10000, search_filter=search_filter)
        if not proofs:
            return

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=proofs[0].keys())
            writer.writeheader()
            writer.writerows(proofs)

    def export_parquet(self, output_path: str, search_filter: SearchFilter | None = None) -> None:
        """Export proofs as Parquet."""
        try:
            import pandas as pd  # type: ignore[import-untyped]
        except ImportError:
            raise RegistryError("pandas not installed. Install with: pip install 'acto[parquet]'") from None

        proofs = self.list(limit=10000, search_filter=search_filter)
        if not proofs:
            return

        df = pd.DataFrame(proofs)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output, index=False)

    def backup(self, backup_path: str) -> None:
        """Create a backup of the registry."""
        import shutil
        from pathlib import Path

        # For SQLite: copy the database file
        db_path = Path(self.settings.db_url.replace("sqlite:///", ""))
        if db_path.exists():
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db_path, backup_file)
        else:
            raise RegistryError(f"Database file not found: {db_path}")

    def restore(self, backup_path: str) -> None:
        """Restore a backup."""
        import shutil
        from pathlib import Path

        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise RegistryError(f"Backup file not found: {backup_path}")

        db_path = Path(self.settings.db_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, db_path)

        # Reload the database
        Base.metadata.create_all(self.engine)
