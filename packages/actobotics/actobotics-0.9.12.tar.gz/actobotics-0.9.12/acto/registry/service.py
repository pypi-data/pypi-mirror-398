from __future__ import annotations

import hashlib
from pathlib import Path

import orjson
from sqlalchemy import func, select

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

    # =========================================================================
    # Optimized Aggregation Methods (SQL-level, no full data loading)
    # =========================================================================

    def count(self, search_filter: SearchFilter | None = None) -> int:
        """
        Count proofs matching the filter using SQL COUNT.
        
        Much more efficient than len(list()) for large datasets.
        
        Args:
            search_filter: Optional filter to apply
            
        Returns:
            int: Number of matching proofs
        """
        with self.SessionLocal() as session:
            stmt = select(func.count()).select_from(ProofRecord)
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())
            result = session.execute(stmt).scalar()
            return result or 0

    def count_by_robot(self, search_filter: SearchFilter | None = None) -> dict[str, int]:
        """
        Count proofs grouped by robot_id using SQL GROUP BY.
        
        Args:
            search_filter: Optional filter to apply
            
        Returns:
            dict: Mapping of robot_id to proof count
        """
        with self.SessionLocal() as session:
            stmt = select(
                ProofRecord.robot_id,
                func.count().label("count")
            ).group_by(ProofRecord.robot_id)
            
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())
            
            rows = session.execute(stmt).all()
            return {
                (row.robot_id or "unknown"): row.count
                for row in rows
            }

    def count_by_task(self, search_filter: SearchFilter | None = None) -> dict[str, int]:
        """
        Count proofs grouped by task_id using SQL GROUP BY.
        
        Args:
            search_filter: Optional filter to apply
            
        Returns:
            dict: Mapping of task_id to proof count
        """
        with self.SessionLocal() as session:
            stmt = select(
                ProofRecord.task_id,
                func.count().label("count")
            ).group_by(ProofRecord.task_id)
            
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())
            
            rows = session.execute(stmt).all()
            return {
                (row.task_id or "unknown"): row.count
                for row in rows
            }

    def count_by_date(
        self,
        days: int = 30,
        search_filter: SearchFilter | None = None,
    ) -> list[dict[str, str | int]]:
        """
        Count proofs grouped by date for the last N days.
        
        Args:
            days: Number of days to include (default: 30)
            search_filter: Optional filter to apply
            
        Returns:
            list: List of {"date": "YYYY-MM-DD", "count": N} dicts
        """
        from datetime import datetime, timedelta, timezone
        
        # Calculate date range
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with self.SessionLocal() as session:
            # SQLite uses substr for date extraction
            # PostgreSQL would use DATE() or date_trunc()
            stmt = select(
                func.substr(ProofRecord.created_at, 1, 10).label("date"),
                func.count().label("count")
            ).where(
                ProofRecord.created_at >= start_date
            ).group_by(
                func.substr(ProofRecord.created_at, 1, 10)
            ).order_by(
                func.substr(ProofRecord.created_at, 1, 10)
            )
            
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())
            
            rows = session.execute(stmt).all()
            result_dict = {row.date: row.count for row in rows}
            
            # Fill in missing dates with 0
            timeline = []
            for i in range(days):
                date = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
                timeline.append({
                    "date": date,
                    "proof_count": result_dict.get(date, 0),
                })
            
            return timeline

    def get_activity_range(
        self,
        search_filter: SearchFilter | None = None,
    ) -> tuple[str | None, str | None]:
        """
        Get first and last activity timestamps using SQL MIN/MAX.
        
        Args:
            search_filter: Optional filter to apply
            
        Returns:
            tuple: (first_activity, last_activity) ISO timestamps or (None, None)
        """
        with self.SessionLocal() as session:
            stmt = select(
                func.min(ProofRecord.created_at).label("first"),
                func.max(ProofRecord.created_at).label("last")
            )
            
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())
            
            row = session.execute(stmt).one()
            return (row.first, row.last)

    def exists_by_robot(self, robot_id: str) -> bool:
        """
        Check if any proofs exist for a robot_id.
        
        More efficient than loading all proofs just to check existence.
        
        Args:
            robot_id: Robot ID to check
            
        Returns:
            bool: True if proofs exist for this robot
        """
        with self.SessionLocal() as session:
            stmt = select(func.count()).select_from(ProofRecord).where(
                ProofRecord.robot_id == robot_id
            ).limit(1)
            result = session.execute(stmt).scalar()
            return (result or 0) > 0

    def get_unique_robot_ids(self, search_filter: SearchFilter | None = None) -> list[str]:
        """
        Get list of unique robot IDs.
        
        Args:
            search_filter: Optional filter to apply
            
        Returns:
            list: Unique robot IDs
        """
        with self.SessionLocal() as session:
            stmt = select(ProofRecord.robot_id).distinct()
            
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())
            
            rows = session.execute(stmt).scalars().all()
            return [r for r in rows if r is not None]

    def get_unique_task_ids(
        self,
        robot_id: str | None = None,
        search_filter: SearchFilter | None = None,
    ) -> list[str]:
        """
        Get list of unique task IDs, optionally filtered by robot.
        
        Args:
            robot_id: Optional robot ID to filter by
            search_filter: Optional additional filter
            
        Returns:
            list: Unique task IDs
        """
        with self.SessionLocal() as session:
            stmt = select(ProofRecord.task_id).distinct()
            
            if robot_id:
                stmt = stmt.where(ProofRecord.robot_id == robot_id)
            
            if search_filter:
                stmt = stmt.where(search_filter.to_sqlalchemy_filter())
            
            rows = session.execute(stmt).scalars().all()
            return [r for r in rows if r is not None]

    def get_device_stats(self, robot_id: str) -> dict:
        """
        Get aggregated statistics for a specific device/robot.
        
        Args:
            robot_id: Robot ID to get stats for
            
        Returns:
            dict: Device statistics including counts and activity range
        """
        with self.SessionLocal() as session:
            # Single query for count, first/last activity, and unique tasks
            stmt = select(
                func.count().label("proof_count"),
                func.min(ProofRecord.created_at).label("first_activity"),
                func.max(ProofRecord.created_at).label("last_activity"),
                func.count(func.distinct(ProofRecord.task_id)).label("task_count"),
            ).where(ProofRecord.robot_id == robot_id)
            
            row = session.execute(stmt).one()
            
            # Get unique task IDs (separate query for the actual values)
            task_stmt = select(ProofRecord.task_id).distinct().where(
                ProofRecord.robot_id == robot_id
            )
            task_ids = [r for r in session.execute(task_stmt).scalars().all() if r]
            
            return {
                "proof_count": row.proof_count or 0,
                "task_count": row.task_count or 0,
                "first_activity": row.first_activity,
                "last_activity": row.last_activity,
                "task_ids": task_ids,
            }
