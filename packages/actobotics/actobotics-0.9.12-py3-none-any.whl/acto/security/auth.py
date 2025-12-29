from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer

from acto.access.solana_gate import SolanaTokenGate
from acto.config.settings import Settings
from acto.errors import AccessError
from acto.security.api_key_store import ApiKeyStore
from acto.security.jwt import JWTManager
from acto.security.rbac import RBACManager, extract_roles_from_token, extract_scopes_from_token

security = HTTPBearer(auto_error=False)


def require_api_key(store: ApiKeyStore):
    """Dependency for API key authentication via Bearer token."""

    async def _dep(request: Request) -> None:
        # Get Bearer token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header. Please provide a Bearer token.",
            )

        token = auth_header.replace("Bearer ", "").strip()
        try:
            store.require(token)
            # Record usage statistics
            endpoint = f"{request.method} {request.url.path}"
            store.record_usage(token, endpoint)
        except AccessError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}") from e

    return _dep


def require_jwt(jwt_manager: JWTManager):
    """Dependency for JWT/OAuth2 authentication."""

    async def _dep(request: Request) -> dict:
        # Get credentials from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing authorization header.")

        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt_manager.verify_token(token, required_type="access")
            request.state.user_id = payload.get("sub")
            request.state.user_roles = extract_roles_from_token(payload)
            request.state.user_scopes = extract_scopes_from_token(payload)
            request.state.token_payload = payload
            return payload
        except AccessError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e

    return _dep


def require_jwt_optional(jwt_manager: JWTManager):
    """Optional JWT dependency that sets request.state but doesn't raise errors if missing."""

    async def _dep(request: Request) -> dict | None:
        # Get credentials from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt_manager.verify_token(token, required_type="access")
            request.state.user_id = payload.get("sub")
            request.state.user_roles = extract_roles_from_token(payload)
            request.state.user_scopes = extract_scopes_from_token(payload)
            request.state.token_payload = payload
            return payload
        except AccessError:
            return None

    return _dep


def create_jwt_dependency(jwt_manager: JWTManager | None):
    """Create JWT dependency if JWT is enabled."""
    if jwt_manager:
        return Depends(require_jwt(jwt_manager))
    return None


def create_jwt_dependency_optional(jwt_manager: JWTManager | None):
    """Create optional JWT dependency if JWT is enabled (doesn't raise errors if missing)."""
    if jwt_manager:
        return Depends(require_jwt_optional(jwt_manager))
    return None


def require_permission(permission, rbac_manager: RBACManager, jwt_manager: JWTManager):
    """Dependency factory for requiring specific RBAC permissions."""

    def _dep(request: Request) -> dict:
        # Get token payload from request state (set by JWT middleware)
        if not hasattr(request.state, "token_payload"):
            raise HTTPException(status_code=401, detail="Not authenticated.")
        token_payload = request.state.token_payload
        user_roles = extract_roles_from_token(token_payload)
        rbac_manager.require_permission(user_roles, permission)
        return token_payload

    return _dep


def require_scope(scope: str, jwt_manager: JWTManager):
    """Dependency factory for requiring specific OAuth2 scopes."""

    def _dep(request: Request) -> dict:
        # Get token payload from request state (set by JWT middleware)
        if not hasattr(request.state, "token_payload"):
            raise HTTPException(status_code=401, detail="Not authenticated.")
        token_payload = request.state.token_payload
        user_scopes = extract_scopes_from_token(token_payload)
        rbac_manager = RBACManager()
        rbac_manager.require_scope(user_scopes, scope)
        return token_payload

    return _dep


def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return {
        "user_id": request.state.user_id,
        "roles": getattr(request.state, "user_roles", []),
        "scopes": getattr(request.state, "user_scopes", []),
    }


def get_current_user_optional(request: Request) -> dict | None:
    """Get current authenticated user from request state, returns None if not authenticated."""
    if not hasattr(request.state, "user_id"):
        return None
    return {
        "user_id": request.state.user_id,
        "roles": getattr(request.state, "user_roles", []),
        "scopes": getattr(request.state, "user_scopes", []),
    }


def require_api_key_and_token_balance(
    store: ApiKeyStore,
    settings: Settings,
):
    """Dependency for API key authentication via Bearer token AND Solana token balance check."""

    async def _dep(
        request: Request,
        x_wallet_address: str | None = Header(None, description="Solana wallet address (required if token gating is enabled)"),
    ) -> None:
        # Get Bearer token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header. Please provide a Bearer token.",
            )

        token = auth_header.replace("Bearer ", "").strip()
        try:
            # First verify API key
            store.require(token)
            # Record usage statistics
            endpoint = f"{request.method} {request.url.path}"
            store.record_usage(token, endpoint)
        except AccessError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}") from e

        # Check token gating if enabled
        if settings.token_gating_enabled:
            if not x_wallet_address:
                raise HTTPException(
                    status_code=400,
                    detail="X-Wallet-Address header is required when token gating is enabled.",
                )
            try:
                gate = SolanaTokenGate(rpc_url=settings.get_solana_rpc_url())
                decision = gate.decide(
                    owner=x_wallet_address,
                    mint=settings.token_gating_mint,
                    minimum=settings.token_gating_minimum,
                )
                if not decision.allowed:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Insufficient token balance. Required: {settings.token_gating_minimum}, "
                        f"Your balance: {decision.balance or 0.0}",
                    )
            except AccessError as e:
                raise HTTPException(status_code=403, detail=f"Token balance check failed: {str(e)}") from e
            except Exception as e:
                import traceback
                error_details = str(e)
                # Log full traceback for debugging (in production, use proper logging)
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Token balance verification error: {error_details}\n{traceback.format_exc()}")
                # Return 403 instead of 500 for token balance issues - this is a client-side issue
                raise HTTPException(
                    status_code=403, detail=f"Token balance verification failed: {error_details}. "
                    f"Make sure you have at least {settings.token_gating_minimum} ACTO tokens."
                ) from e

    return _dep
