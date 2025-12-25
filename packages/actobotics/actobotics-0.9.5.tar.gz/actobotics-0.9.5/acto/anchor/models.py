from __future__ import annotations

from pydantic import BaseModel


class AnchorRequest(BaseModel):
    payload_hash: str
    memo: str | None = None
