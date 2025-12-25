from __future__ import annotations

from dataclasses import dataclass

from acto.cache import CacheBackend, get_cache_backend
from acto.config.settings import Settings
from acto.proof.models import ProofEnvelope


@dataclass
class ScoreResult:
    score: float
    reasons: dict[str, float]


def _cache_key_score(payload_hash: str) -> str:
    """Generate cache key for a reputation score."""
    return f"score:{payload_hash}"


class ReputationScorer:
    """Explainable reputation score derived from proof payload with optional caching."""

    def __init__(self, weights: dict[str, float] | None = None, settings: Settings | None = None, cache: CacheBackend | None = None):
        self.weights = weights or {"events_count": 0.4, "safety_ok_ratio": 0.4, "freshness": 0.2}
        self.settings = settings or Settings()
        self.cache = cache or get_cache_backend(self.settings)

    def score(self, env: ProofEnvelope) -> ScoreResult:
        # Try cache first (score is deterministic based on payload_hash)
        cache_key = _cache_key_score(env.payload.payload_hash)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return ScoreResult(score=cached["score"], reasons=cached["reasons"])

        # Cache miss, compute score
        reasons: dict[str, float] = {}
        events = env.payload.telemetry_normalized.get("events", [])
        events_count = float(len(events))
        reasons["events_count"] = min(1.0, events_count / 100.0)

        ok_vals = []
        for e in events:
            data = e.get("data", {})
            if isinstance(data, dict) and "ok" in data:
                ok_vals.append(bool(data["ok"]))
        ok_ratio = (
            sum(1 for v in ok_vals if v) / float(len(ok_vals))
            if ok_vals
            else 0.5
        )

        reasons["safety_ok_ratio"] = float(ok_ratio)

        freshness = 0.5
        try:
            import datetime as _dt
            dt = _dt.datetime.fromisoformat(env.payload.created_at)
            now = _dt.datetime.now(dt.tzinfo)
            age_seconds = max(0.0, (now - dt).total_seconds())
            freshness = max(0.0, min(1.0, 1.0 - (age_seconds / (7 * 24 * 3600))))
        except Exception:
            freshness = 0.5
        reasons["freshness"] = float(freshness)

        score = 0.0
        for k, wgt in self.weights.items():
            score += wgt * reasons.get(k, 0.0)

        result = ScoreResult(score=float(round(score, 6)), reasons=reasons)

        # Store in cache (with longer TTL since scores don't change for a given proof)
        if self.cache:
            cache_ttl = self.settings.cache_ttl * 24  # 24 hours for scores
            self.cache.set(cache_key, {"score": result.score, "reasons": result.reasons}, ttl=cache_ttl)

        return result
