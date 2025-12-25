from __future__ import annotations

import hashlib

from blake3 import blake3


def blake3_hash(data: bytes) -> str:
    return blake3(data).hexdigest()


def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
