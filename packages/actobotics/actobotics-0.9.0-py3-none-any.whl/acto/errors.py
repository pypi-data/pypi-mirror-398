class ActoError(Exception):
    """Base exception for ACTO."""


class TelemetryError(ActoError):
    """Raised for telemetry parsing/normalization problems."""


class ProofError(ActoError):
    """Raised for proof creation/verification problems."""


class RegistryError(ActoError):
    """Raised for database registry problems."""


class AccessError(ActoError):
    """Raised when access checks fail."""


class CryptoError(ActoError):
    """Raised for key/signature issues."""
