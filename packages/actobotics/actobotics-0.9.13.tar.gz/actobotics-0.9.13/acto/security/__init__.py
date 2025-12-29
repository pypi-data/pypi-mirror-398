# Core security modules (always available)
from .api_keys import ApiKeyStore as LegacyApiKeyStore, generate_api_key, hash_api_key
from .api_key_store import ApiKeyStore
from .audit import AuditAction, AuditLogger, AuditResult
from .encryption import EncryptionManager, ProofEncryption
from .jwt import JWTManager, OAuth2TokenResponse
from .key_rotation import KeyRotationManager
from .rate_limit import TokenBucketRateLimiter
from .rbac import Permission, RBACManager, Role, extract_roles_from_token, extract_scopes_from_token
from .secrets import (
    AWSSecretsManager,
    EnvironmentSecretsManager,
    HashiCorpVaultSecretsManager,
    SecretsManager,
    get_secrets_manager,
)
from .tls import TLSManager

__all__ = [
    # API Key management
    "ApiKeyStore",
    "LegacyApiKeyStore",
    "generate_api_key",
    "hash_api_key",
    # Rate limiting
    "TokenBucketRateLimiter",
    # JWT/OAuth2
    "JWTManager",
    "OAuth2TokenResponse",
    # RBAC
    "RBACManager",
    "Permission",
    "Role",
    "extract_roles_from_token",
    "extract_scopes_from_token",
    # Audit
    "AuditLogger",
    "AuditAction",
    "AuditResult",
    # Key management
    "KeyRotationManager",
    # Encryption
    "EncryptionManager",
    "ProofEncryption",
    # TLS
    "TLSManager",
    # Secrets management
    "SecretsManager",
    "EnvironmentSecretsManager",
    "HashiCorpVaultSecretsManager",
    "AWSSecretsManager",
    "get_secrets_manager",
]

# FastAPI authentication dependencies (only available when fastapi is installed)
# These are server-specific and require: pip install acto[server]
try:
    from .auth import (
        create_jwt_dependency,
        create_jwt_dependency_optional,
        get_current_user,
        get_current_user_optional,
        require_api_key,
        require_api_key_and_token_balance,
        require_jwt,
        require_jwt_optional,
        require_jwt_or_api_key,
        require_permission,
        require_scope,
    )

    __all__.extend([
        "require_api_key",
        "require_api_key_and_token_balance",
        "require_jwt",
        "require_jwt_or_api_key",
        "create_jwt_dependency",
        "create_jwt_dependency_optional",
        "get_current_user",
        "get_current_user_optional",
        "require_jwt_optional",
        "require_permission",
        "require_scope",
    ])
except ImportError:
    # FastAPI not installed - server dependencies not available
    # Users need to install with: pip install acto[server]
    pass
