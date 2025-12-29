from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuditAction(Enum):
    """Types of audit actions."""

    PROOF_CREATE = "proof:create"
    PROOF_READ = "proof:read"
    PROOF_UPDATE = "proof:update"
    PROOF_DELETE = "proof:delete"
    PROOF_VERIFY = "proof:verify"
    REGISTRY_READ = "registry:read"
    REGISTRY_WRITE = "registry:write"
    REGISTRY_DELETE = "registry:delete"
    REGISTRY_SEARCH = "registry:search"
    USER_LOGIN = "user:login"
    USER_LOGOUT = "user:logout"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    KEY_ROTATE = "key:rotate"
    KEY_CREATE = "key:create"
    KEY_DELETE = "key:delete"
    ACCESS_CHECK = "access:check"
    CONFIG_CHANGE = "config:change"
    ADMIN_ACTION = "admin:action"


class AuditResult(Enum):
    """Result of an audit action."""

    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"


class AuditLogEntry(BaseModel):
    """Audit log entry model."""

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: AuditAction
    result: AuditResult
    user_id: str | None = None
    user_email: str | None = None
    user_roles: list[str] = Field(default_factory=list)
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class AuditLogger:
    """Audit logging service."""

    def __init__(self, backend: AuditBackend | None = None):
        self.backend = backend or MemoryAuditBackend()

    def log(
        self,
        action: AuditAction,
        result: AuditResult,
        user_id: str | None = None,
        user_email: str | None = None,
        user_roles: list[str] | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Log an audit event."""
        entry = AuditLogEntry(
            action=action,
            result=result,
            user_id=user_id,
            user_email=user_email,
            user_roles=user_roles or [],
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details or {},
            error_message=error_message,
        )
        self.backend.write(entry)

    def log_success(
        self,
        action: AuditAction,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log a successful action."""
        self.log(action=action, result=AuditResult.SUCCESS, user_id=user_id, **kwargs)

    def log_failure(
        self,
        action: AuditAction,
        error_message: str,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log a failed action."""
        self.log(
            action=action, result=AuditResult.FAILURE, user_id=user_id, error_message=error_message, **kwargs
        )

    def log_denied(
        self,
        action: AuditAction,
        user_id: str | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log a denied action."""
        self.log(
            action=action,
            result=AuditResult.DENIED,
            user_id=user_id,
            error_message=reason,
            **kwargs,
        )


class AuditBackend:
    """Base class for audit log backends."""

    def write(self, entry: AuditLogEntry) -> None:
        """Write an audit log entry."""
        raise NotImplementedError


class MemoryAuditBackend(AuditBackend):
    """In-memory audit log backend (for testing/development)."""

    def __init__(self):
        self.entries: list[AuditLogEntry] = []

    def write(self, entry: AuditLogEntry) -> None:
        """Write an audit log entry to memory."""
        self.entries.append(entry)

    def get_entries(
        self,
        action: AuditAction | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Get audit log entries with optional filtering."""
        results = self.entries
        if action:
            results = [e for e in results if e.action == action]
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        return results[-limit:]


class FileAuditBackend(AuditBackend):
    """File-based audit log backend."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def write(self, entry: AuditLogEntry) -> None:
        """Write an audit log entry to file (JSONL format)."""
        from pathlib import Path

        log_file = Path(self.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.model_dump(), default=str) + "\n")


class DatabaseAuditBackend(AuditBackend):
    """Database-backed audit log backend."""

    def __init__(self, session_factory: Any):
        self.session_factory = session_factory

    def write(self, entry: AuditLogEntry) -> None:
        """Write an audit log entry to database."""
        # This would require a database model for audit logs
        # Implementation depends on the ORM being used
        pass

