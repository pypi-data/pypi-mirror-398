from __future__ import annotations

import datetime as _dt


def now_utc_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def parse_iso(value: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(value)
