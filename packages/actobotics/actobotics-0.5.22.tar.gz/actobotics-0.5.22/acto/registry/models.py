from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProofRecord(Base):
    __tablename__ = "proofs"

    proof_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(256), index=True)
    robot_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[str] = mapped_column(String(64), index=True)
    payload_hash: Mapped[str] = mapped_column(String(128), index=True, unique=True)
    signer_public_key_b64: Mapped[str] = mapped_column(Text)
    signature_b64: Mapped[str] = mapped_column(Text)
    envelope_json: Mapped[str] = mapped_column(Text)
    anchor_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Multi-Tenant-Support
    tenant_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)

    # Volltextsuche: Indizierte Metadaten für Suche
    metadata_search: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for queries by robot_id and created_at (e.g., get all proofs for a robot, sorted by time)
        Index("idx_robot_created", "robot_id", "created_at"),
        # Index for queries by task_id and created_at
        Index("idx_task_created", "task_id", "created_at"),
        # Index for queries filtering by robot_id and task_id
        Index("idx_robot_task", "robot_id", "task_id"),
        # Index for queries by signer (to find all proofs signed by a specific key)
        Index("idx_signer_created", "signer_public_key_b64", "created_at"),
        # Index for tenant queries
        Index("idx_tenant_created", "tenant_id", "created_at"),
        # Index for fulltext search (SQLite FTS5 würde hier verwendet werden)
    )
