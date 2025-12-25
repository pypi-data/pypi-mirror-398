"""
ACTO: Robotics Proof-of-Execution Toolkit.

Public API entrypoints:
- acto.proof (create/verify)
- acto.crypto (keys/signatures/hashes)
- acto.telemetry (parsers/normalizers)
- acto.registry (SQLite-backed proof registry)
"""
from .version import __version__

__all__ = ["__version__"]

# Expanded modules: security, pipeline, reputation, metrics, plugins, anchor
