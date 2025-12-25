from __future__ import annotations

from enum import Enum
from typing import Any

from acto.errors import AccessError


class Permission(Enum):
    """Permission types for RBAC."""

    PROOF_READ = "proof:read"
    PROOF_WRITE = "proof:write"
    PROOF_DELETE = "proof:delete"
    REGISTRY_READ = "registry:read"
    REGISTRY_WRITE = "registry:write"
    REGISTRY_DELETE = "registry:delete"
    ADMIN = "admin"
    AUDIT_READ = "audit:read"
    USER_MANAGE = "user:manage"
    KEY_ROTATE = "key:rotate"


class Role(Enum):
    """Predefined roles with associated permissions."""

    VIEWER = "viewer"
    USER = "user"
    ADMIN = "admin"
    AUDITOR = "auditor"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.VIEWER: [Permission.PROOF_READ, Permission.REGISTRY_READ],
    Role.USER: [
        Permission.PROOF_READ,
        Permission.PROOF_WRITE,
        Permission.REGISTRY_READ,
        Permission.REGISTRY_WRITE,
    ],
    Role.ADMIN: [
        Permission.PROOF_READ,
        Permission.PROOF_WRITE,
        Permission.PROOF_DELETE,
        Permission.REGISTRY_READ,
        Permission.REGISTRY_WRITE,
        Permission.REGISTRY_DELETE,
        Permission.ADMIN,
        Permission.AUDIT_READ,
        Permission.USER_MANAGE,
        Permission.KEY_ROTATE,
    ],
    Role.AUDITOR: [Permission.PROOF_READ, Permission.REGISTRY_READ, Permission.AUDIT_READ],
}


class RBACManager:
    """Role-Based Access Control manager."""

    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS.copy()
        self.custom_roles: dict[str, list[Permission]] = {}

    def add_custom_role(self, role_name: str, permissions: list[Permission]) -> None:
        """Add a custom role with specific permissions."""
        self.custom_roles[role_name] = permissions

    def get_permissions_for_roles(self, roles: list[str]) -> set[Permission]:
        """Get all permissions for a list of roles."""
        permissions: set[Permission] = set()

        for role_str in roles:
            # Try to match enum role
            try:
                role = Role(role_str)
                if role in self.role_permissions:
                    permissions.update(self.role_permissions[role])
            except ValueError:
                # Check custom roles
                if role_str in self.custom_roles:
                    permissions.update(self.custom_roles[role_str])

        return permissions

    def has_permission(self, user_roles: list[str], required_permission: Permission) -> bool:
        """Check if user has the required permission."""
        user_permissions = self.get_permissions_for_roles(user_roles)
        return required_permission in user_permissions

    def require_permission(
        self, user_roles: list[str], required_permission: Permission, resource: str | None = None
    ) -> None:
        """Require a specific permission, raise AccessError if not granted."""
        if not self.has_permission(user_roles, required_permission):
            resource_msg = f" on {resource}" if resource else ""
            raise AccessError(
                f"Permission denied: {required_permission.value} required{resource_msg}."
            )

    def check_scopes(self, user_scopes: list[str], required_scope: str) -> bool:
        """Check if user has the required OAuth2 scope."""
        return required_scope in user_scopes

    def require_scope(self, user_scopes: list[str], required_scope: str) -> None:
        """Require a specific OAuth2 scope, raise AccessError if not granted."""
        if not self.check_scopes(user_scopes, required_scope):
            raise AccessError(f"Scope required: {required_scope}.")


def extract_roles_from_token(token_payload: dict[str, Any]) -> list[str]:
    """Extract roles from JWT token payload."""
    roles = token_payload.get("roles", [])
    if isinstance(roles, list):
        return [str(r) for r in roles]
    return []


def extract_scopes_from_token(token_payload: dict[str, Any]) -> list[str]:
    """Extract scopes from JWT token payload."""
    scopes = token_payload.get("scopes", [])
    if isinstance(scopes, list):
        return [str(s) for s in scopes]
    return []

