from __future__ import annotations

import base64

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from acto.errors import CryptoError


def sign_bytes(private_key_b64: str, payload: bytes) -> str:
    sk = SigningKey(base64.b64decode(private_key_b64))
    sig = sk.sign(payload).signature
    return base64.b64encode(sig).decode("utf-8")


def verify_bytes(public_key_b64: str, payload: bytes, signature_b64: str) -> bool:
    vk = VerifyKey(base64.b64decode(public_key_b64))
    try:
        vk.verify(payload, base64.b64decode(signature_b64))
        return True
    except BadSignatureError:
        return False
    except Exception as e:
        raise CryptoError(str(e)) from e
