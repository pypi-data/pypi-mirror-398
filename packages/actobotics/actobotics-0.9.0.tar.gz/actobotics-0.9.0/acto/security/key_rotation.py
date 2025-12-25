from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any

from nacl.signing import SigningKey, VerifyKey

from acto.errors import CryptoError
from acto.security.audit import AuditAction, AuditLogger


class KeyRotationManager:
    """Manages signing key rotation with support for multiple active keys."""

    def __init__(self, audit_logger: AuditLogger | None = None):
        self.active_keys: dict[str, KeyInfo] = {}
        self.retired_keys: dict[str, KeyInfo] = {}
        self.audit_logger = audit_logger

    def generate_new_key(self, key_id: str | None = None) -> tuple[str, str]:
        """Generate a new signing key pair."""
        if key_id is None:
            key_id = f"key_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        signing_key = SigningKey.generate()
        private_key_b64 = base64.b64encode(bytes(signing_key)).decode("utf-8")
        public_key_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode("utf-8")

        key_info = KeyInfo(
            key_id=key_id,
            private_key_b64=private_key_b64,
            public_key_b64=public_key_b64,
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )

        self.active_keys[key_id] = key_info

        if self.audit_logger:
            self.audit_logger.log_success(
                AuditAction.KEY_CREATE,
                resource_id=key_id,
                details={"public_key_id": key_id},
            )

        return key_id, private_key_b64

    def rotate_key(self, old_key_id: str, new_key_id: str | None = None) -> tuple[str, str]:
        """Rotate from an old key to a new key."""
        if old_key_id not in self.active_keys:
            raise CryptoError(f"Key not found: {old_key_id}")

        # Generate new key
        new_key_id, new_private_key = self.generate_new_key(new_key_id)

        # Retire old key
        old_key_info = self.active_keys.pop(old_key_id)
        old_key_info.is_active = False
        old_key_info.retired_at = datetime.now(timezone.utc)
        self.retired_keys[old_key_id] = old_key_info

        if self.audit_logger:
            self.audit_logger.log_success(
                AuditAction.KEY_ROTATE,
                resource_id=new_key_id,
                details={
                    "old_key_id": old_key_id,
                    "new_key_id": new_key_id,
                },
            )

        return new_key_id, new_private_key

    def get_active_key(self, key_id: str | None = None) -> KeyInfo:
        """Get an active key by ID, or return the most recent active key."""
        if key_id:
            if key_id not in self.active_keys:
                raise CryptoError(f"Active key not found: {key_id}")
            return self.active_keys[key_id]

        if not self.active_keys:
            raise CryptoError("No active keys available.")

        # Return the most recently created key
        return max(self.active_keys.values(), key=lambda k: k.created_at)

    def get_private_key(self, key_id: str | None = None) -> str:
        """Get the private key for signing."""
        key_info = self.get_active_key(key_id)
        return key_info.private_key_b64

    def get_public_key(self, key_id: str | None = None) -> str:
        """Get the public key for verification."""
        key_info = self.get_active_key(key_id)
        return key_info.public_key_b64

    def verify_with_key(self, public_key_b64: str, payload: bytes, signature_b64: str) -> bool:
        """Verify a signature, checking both active and retired keys."""
        try:
            vk = VerifyKey(base64.b64decode(public_key_b64))
            vk.verify(payload, base64.b64decode(signature_b64))
            return True
        except Exception:
            return False

    def verify_with_any_key(self, payload: bytes, signature_b64: str) -> tuple[bool, str | None]:
        """Verify a signature against all known keys (active and retired)."""
        all_keys = {**self.active_keys, **self.retired_keys}
        for key_id, key_info in all_keys.items():
            if self.verify_with_key(key_info.public_key_b64, payload, signature_b64):
                return True, key_id
        return False, None

    def retire_key(self, key_id: str) -> None:
        """Manually retire a key."""
        if key_id not in self.active_keys:
            raise CryptoError(f"Key not found or already retired: {key_id}")

        key_info = self.active_keys.pop(key_id)
        key_info.is_active = False
        key_info.retired_at = datetime.now(timezone.utc)
        self.retired_keys[key_id] = key_info

        if self.audit_logger:
            self.audit_logger.log_success(
                AuditAction.KEY_DELETE,
                resource_id=key_id,
                details={"reason": "manual_retirement"},
            )

    def list_keys(self) -> dict[str, Any]:
        """List all keys (active and retired)."""
        return {
            "active": {k: v.to_dict() for k, v in self.active_keys.items()},
            "retired": {k: v.to_dict() for k, v in self.retired_keys.items()},
        }


class KeyInfo:
    """Information about a signing key."""

    def __init__(
        self,
        key_id: str,
        private_key_b64: str,
        public_key_b64: str,
        created_at: datetime,
        is_active: bool = True,
        retired_at: datetime | None = None,
    ):
        self.key_id = key_id
        self.private_key_b64 = private_key_b64
        self.public_key_b64 = public_key_b64
        self.created_at = created_at
        self.is_active = is_active
        self.retired_at = retired_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding private key)."""
        return {
            "key_id": self.key_id,
            "public_key_b64": self.public_key_b64,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "retired_at": self.retired_at.isoformat() if self.retired_at else None,
        }

