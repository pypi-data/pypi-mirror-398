from __future__ import annotations

from typing import Any

import orjson
from sqlalchemy import and_, or_

from acto.registry.models import ProofRecord


class SearchFilter:
    """Filter for proof search."""

    def __init__(self):
        self.task_id: str | None = None
        self.robot_id: str | None = None
        self.run_id: str | None = None
        self.tenant_id: str | None = None
        self.signer_public_key_b64: str | None = None
        self.search_text: str | None = None
        self.created_after: str | None = None
        self.created_before: str | None = None

    def to_sqlalchemy_filter(self) -> Any:
        """Convert to SQLAlchemy filter."""
        conditions = []

        if self.task_id:
            conditions.append(ProofRecord.task_id == self.task_id)
        if self.robot_id:
            conditions.append(ProofRecord.robot_id == self.robot_id)
        if self.run_id:
            conditions.append(ProofRecord.run_id == self.run_id)
        if self.tenant_id:
            conditions.append(ProofRecord.tenant_id == self.tenant_id)
        if self.signer_public_key_b64:
            conditions.append(ProofRecord.signer_public_key_b64 == self.signer_public_key_b64)
        if self.created_after:
            conditions.append(ProofRecord.created_at >= self.created_after)
        if self.created_before:
            conditions.append(ProofRecord.created_at <= self.created_before)

        # Full-text search
        if self.search_text:
            # Simple LIKE search (for SQLite)
            # In a full implementation, one would use FTS5
            search_pattern = f"%{self.search_text}%"
            conditions.append(
                or_(
                    ProofRecord.task_id.like(search_pattern),
                    ProofRecord.robot_id.like(search_pattern),
                    ProofRecord.run_id.like(search_pattern),
                    ProofRecord.metadata_search.like(search_pattern),
                )
            )

        return and_(*conditions) if conditions else True


class SortOrder:
    """Sort order."""

    ASC = "asc"
    DESC = "desc"


class SortField:
    """Sort fields."""

    CREATED_AT = "created_at"
    TASK_ID = "task_id"
    ROBOT_ID = "robot_id"
    PAYLOAD_HASH = "payload_hash"


def apply_sorting(stmt: Any, sort_field: str = SortField.CREATED_AT, sort_order: str = SortOrder.DESC) -> Any:
    """Apply sorting to a SQLAlchemy query."""
    field_map = {
        SortField.CREATED_AT: ProofRecord.created_at,
        SortField.TASK_ID: ProofRecord.task_id,
        SortField.ROBOT_ID: ProofRecord.robot_id,
        SortField.PAYLOAD_HASH: ProofRecord.payload_hash,
    }

    field = field_map.get(sort_field, ProofRecord.created_at)
    if sort_order == SortOrder.ASC:
        return stmt.order_by(field.asc())
    return stmt.order_by(field.desc())


def extract_searchable_metadata(envelope_json: str) -> str:
    """Extract searchable metadata from a proof envelope."""
    try:
        envelope_dict = orjson.loads(envelope_json)
        meta = envelope_dict.get("payload", {}).get("meta", {})
        task_id = envelope_dict.get("payload", {}).get("subject", {}).get("task_id", "")
        robot_id = envelope_dict.get("payload", {}).get("subject", {}).get("robot_id", "")

        # Create a searchable string
        searchable_parts = [task_id, robot_id]
        if isinstance(meta, dict):
            for _key, value in meta.items():
                if isinstance(value, (str, int, float)):
                    searchable_parts.append(str(value))

        return " ".join(searchable_parts)
    except Exception:
        return ""

