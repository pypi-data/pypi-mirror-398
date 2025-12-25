from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from acto.registry.user_models import User
from acto.registry.db import make_engine, make_session_factory
from acto.config.settings import Settings


class UserStore:
    """Database-backed user store for wallet-based authentication."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = make_engine(settings)
        self.Session = make_session_factory(self.engine)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure database tables exist."""
        from acto.registry.models import Base
        Base.metadata.create_all(self.engine)

    def get_or_create_user(self, wallet_address: str) -> dict[str, Any]:
        """Get existing user or create a new one."""
        with self.Session() as session:
            # Check if user exists
            user = session.query(User).filter(User.wallet_address == wallet_address).first()
            
            now = datetime.now(timezone.utc).isoformat()
            
            if user:
                # Update last login
                user.last_login_at = now
                session.commit()
                return {
                    "user_id": user.user_id,
                    "wallet_address": user.wallet_address,
                    "created_at": user.created_at,
                    "last_login_at": user.last_login_at,
                    "is_active": user.is_active,
                }
            else:
                # Create new user
                user_id = secrets.token_urlsafe(16)
                user = User(
                    user_id=user_id,
                    wallet_address=wallet_address,
                    created_at=now,
                    last_login_at=now,
                    is_active=True,
                )
                session.add(user)
                session.commit()
                return {
                    "user_id": user_id,
                    "wallet_address": wallet_address,
                    "created_at": now,
                    "last_login_at": now,
                    "is_active": True,
                }

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Get user by ID."""
        with self.Session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                return {
                    "user_id": user.user_id,
                    "wallet_address": user.wallet_address,
                    "created_at": user.created_at,
                    "last_login_at": user.last_login_at,
                    "is_active": user.is_active,
                }
        return None

    def get_user_by_wallet(self, wallet_address: str) -> dict[str, Any] | None:
        """Get user by wallet address."""
        with self.Session() as session:
            user = session.query(User).filter(User.wallet_address == wallet_address).first()
            if user:
                return {
                    "user_id": user.user_id,
                    "wallet_address": user.wallet_address,
                    "created_at": user.created_at,
                    "last_login_at": user.last_login_at,
                    "is_active": user.is_active,
                }
        return None

