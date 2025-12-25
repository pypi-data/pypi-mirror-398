from __future__ import annotations

import base64
from typing import Any

from cryptography.fernet import Fernet  # type: ignore[import-untyped]
from cryptography.hazmat.primitives import hashes  # type: ignore[import-untyped]
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore[import-untyped]

from acto.errors import CryptoError


class EncryptionManager:
    """Manages encryption at rest for sensitive data."""

    def __init__(self, key: bytes | None = None, password: str | None = None, salt: bytes | None = None):
        """Initialize encryption manager.

        Args:
            key: Direct encryption key (32 bytes for Fernet)
            password: Password to derive key from (if key not provided)
            salt: Salt for key derivation (if using password)
        """
        if key:
            self.cipher = Fernet(key)
        elif password:
            if not salt:
                raise CryptoError("Salt required when using password-based encryption.")
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self.cipher = Fernet(key)
        else:
            raise CryptoError("Either key or password must be provided.")

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()

    @staticmethod
    def generate_salt() -> bytes:
        """Generate a random salt for key derivation."""
        import secrets

        return secrets.token_bytes(16)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        try:
            return self.cipher.encrypt(data)
        except Exception as e:
            raise CryptoError(f"Encryption failed: {str(e)}") from e

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data."""
        try:
            return self.cipher.decrypt(encrypted_data)
        except Exception as e:
            raise CryptoError(f"Decryption failed: {str(e)}") from e

    def encrypt_string(self, text: str) -> str:
        """Encrypt a string and return base64-encoded result."""
        encrypted = self.encrypt(text.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_string(self, encrypted_text: str) -> str:
        """Decrypt a base64-encoded encrypted string."""
        encrypted_bytes = base64.b64decode(encrypted_text.encode("utf-8"))
        decrypted = self.decrypt(encrypted_bytes)
        return decrypted.decode("utf-8")

    def encrypt_dict(self, data: dict[str, Any]) -> str:
        """Encrypt a dictionary (JSON-serialized)."""
        import json

        json_str = json.dumps(data)
        return self.encrypt_string(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict[str, Any]:
        """Decrypt and deserialize a dictionary."""
        import json

        json_str = self.decrypt_string(encrypted_data)
        return json.loads(json_str)


class ProofEncryption:
    """Specialized encryption for proof data at rest."""

    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager

    def encrypt_proof_envelope(self, envelope_json: str) -> str:
        """Encrypt a proof envelope JSON string."""
        return self.encryption_manager.encrypt_string(envelope_json)

    def decrypt_proof_envelope(self, encrypted_envelope: str) -> str:
        """Decrypt a proof envelope JSON string."""
        return self.encryption_manager.decrypt_string(encrypted_envelope)

