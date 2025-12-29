from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_config_files() -> list[str]:
    """Get list of config files to load."""
    files = [".env"]
    home = Path.home()
    config_file = home / ".acto" / "config.toml"
    if config_file.exists():
        files.append(str(config_file))
    return files


class Settings(BaseSettings):
    """Central configuration for ACTO."""

    model_config = SettingsConfigDict(
        env_prefix="ACTO_",
        env_file=_get_config_files(),
        extra="ignore",
    )

    # Storage
    db_url: str = "sqlite:///./data/acto.sqlite"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Logging
    log_level: str = "INFO"
    json_logs: bool = False

    # Proof defaults
    proof_version: str = "1"
    proof_hash_alg: str = "blake3"
    proof_signature_alg: str = "ed25519"

    # Server
    host: str = "127.0.0.1"
    port: int = 8080

    # API security
    api_auth_enabled: bool = False

    # JWT/OAuth2
    jwt_enabled: bool = False
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # RBAC
    rbac_enabled: bool = False

    # Audit logging
    audit_log_enabled: bool = False
    audit_log_backend: str = "memory"  # "memory", "file", or "database"
    audit_log_file: str = "./data/audit.log"

    # Encryption at rest
    encryption_enabled: bool = False
    encryption_key: str | None = None
    encryption_password: str | None = None
    encryption_salt: str | None = None

    # TLS/SSL
    tls_enabled: bool = False
    tls_cert_file: str | None = None
    tls_key_file: str | None = None
    tls_ca_cert_file: str | None = None

    # Secrets management
    secrets_backend: str = "env"  # "env", "vault", or "aws"
    vault_url: str = "http://localhost:8200"
    vault_token: str | None = None
    vault_path: str = "secret"
    aws_secrets_region: str = "us-east-1"
    aws_secrets_profile: str | None = None

    # PII detection and masking
    pii_detection_enabled: bool = False
    pii_masking_enabled: bool = False
    pii_mask_char: str = "*"
    pii_preserve_length: bool = True

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_rps: float = 5.0
    rate_limit_burst: int = 20
    rate_limit_bucket_ttl: float = 3600.0  # Bucket expiry in seconds (default: 1 hour)
    rate_limit_cleanup_interval: int = 1000  # Cleanup stale buckets every N requests

    # Upload limits
    max_telemetry_bytes: int = 8_000_000

    # Caching
    cache_enabled: bool = False
    cache_backend: str = "memory"  # "memory" or "redis"
    cache_ttl: int = 3600  # Time-to-live in seconds
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None

    # Token Gating
    token_gating_enabled: bool = True
    token_gating_mint: str = "9wpLm21ab8ZMVJWH3pHeqgqNJqWos73G8qDRfaEwtray"
    token_gating_minimum: float = 50000.0
    
    # Solana RPC - Helius recommended for production
    # If helius_api_key is set, it will be used automatically
    helius_api_key: str = ""
    solana_rpc_url: str = ""  # Custom RPC URL (overrides Helius if set)
    
    def get_solana_rpc_url(self) -> str:
        """Get the Solana RPC URL, preferring Helius if API key is set."""
        # Custom URL takes priority
        if self.solana_rpc_url:
            return self.solana_rpc_url
        # Use Helius if API key is provided
        if self.helius_api_key:
            return f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}"
        # Fallback to public RPC (has strict rate limits)
        return "https://api.mainnet-beta.solana.com"