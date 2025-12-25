from __future__ import annotations

from pydantic import BaseModel


class AccessDecision(BaseModel):
    allowed: bool
    reason: str
    balance: float | None = None
