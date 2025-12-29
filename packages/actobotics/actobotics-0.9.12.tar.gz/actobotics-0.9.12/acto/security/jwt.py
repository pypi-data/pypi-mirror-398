from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from acto.errors import AccessError


class JWTManager:
    """JWT token manager for OAuth2-style authentication."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        subject: str,
        roles: list[str] | None = None,
        scopes: list[str] | None = None,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a JWT access token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)

        payload: dict[str, Any] = {
            "sub": subject,
            "exp": expire,
            "iat": now,
            "type": "access",
        }

        if roles:
            payload["roles"] = roles
        if scopes:
            payload["scopes"] = scopes
        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, subject: str) -> str:
        """Create a JWT refresh token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": subject,
            "exp": expire,
            "iat": now,
            "type": "refresh",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except ExpiredSignatureError as e:
            raise AccessError("Token has expired.") from e
        except DecodeError as e:
            raise AccessError("Invalid token format.") from e
        except InvalidTokenError as e:
            raise AccessError(f"Invalid token: {str(e)}") from e

    def verify_token(self, token: str, required_type: str | None = None) -> dict[str, Any]:
        """Verify a token and optionally check its type."""
        payload = self.decode_token(token)
        if required_type and payload.get("type") != required_type:
            raise AccessError(f"Token type mismatch. Expected {required_type}.")
        return payload

    def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from a refresh token."""
        payload = self.verify_token(refresh_token, required_type="refresh")
        subject = payload.get("sub")
        if not subject:
            raise AccessError("Invalid refresh token: missing subject.")

        roles = payload.get("roles", [])
        scopes = payload.get("scopes", [])

        return self.create_access_token(subject=subject, roles=roles, scopes=scopes)


class OAuth2TokenResponse:
    """OAuth2 token response model."""

    def __init__(
        self,
        access_token: str,
        token_type: str = "Bearer",
        expires_in: int | None = None,
        refresh_token: str | None = None,
        scope: str | None = None,
    ):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.refresh_token = refresh_token
        self.scope = scope

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result: dict[str, Any] = {
            "access_token": self.access_token,
            "token_type": self.token_type,
        }
        if self.expires_in:
            result["expires_in"] = self.expires_in
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
        if self.scope:
            result["scope"] = self.scope
        return result

