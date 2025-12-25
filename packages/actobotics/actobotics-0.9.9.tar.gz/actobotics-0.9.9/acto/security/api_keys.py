from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from acto.errors import AccessError


def generate_api_key(prefix: str = "acto") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


@dataclass
class ApiKeyStore:
    """In-memory API key store.

    For production, replace with persistent storage.
    """

    hashed_keys: dict[str, str]

    @staticmethod
    def from_plaintext(keys: list[str]) -> ApiKeyStore:
        return ApiKeyStore(hashed_keys={hash_api_key(k): "active" for k in keys})

    def is_valid(self, key: str) -> bool:
        return hash_api_key(key) in self.hashed_keys

    def require(self, key: str | None) -> None:
        if not key or not self.is_valid(key):
            raise AccessError("Invalid or missing API key.")
