from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path

from nacl.signing import SigningKey

from acto.errors import CryptoError


@dataclass(frozen=True)
class KeyPair:
    """Ed25519 keypair wrapper."""

    public_key_b64: str
    private_key_b64: str

    @staticmethod
    def generate() -> KeyPair:
        sk = SigningKey.generate()
        pk = sk.verify_key
        return KeyPair(
            public_key_b64=base64.b64encode(bytes(pk)).decode("utf-8"),
            private_key_b64=base64.b64encode(bytes(sk)).decode("utf-8"),
        )


def save_keypair(path: str | Path, kp: KeyPair) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"public_key_b64": kp.public_key_b64, "private_key_b64": kp.private_key_b64}, indent=2),
        encoding="utf-8",
    )


def load_keypair(path: str | Path) -> KeyPair:
    p = Path(path)
    if not p.exists():
        raise CryptoError(f"Keypair not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if "public_key_b64" not in data or "private_key_b64" not in data:
        raise CryptoError("Invalid keypair file format.")
    return KeyPair(public_key_b64=data["public_key_b64"], private_key_b64=data["private_key_b64"])
