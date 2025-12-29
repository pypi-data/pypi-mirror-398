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
        """Ensure database tables exist and have all required columns."""
        from acto.registry.models import Base
        from sqlalchemy import inspect, text
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Add missing columns to existing tables (simple migration)
        inspector = inspect(self.engine)
        if "users" in inspector.get_table_names():
            existing_columns = {col["name"] for col in inspector.get_columns("users")}
            new_columns = {
                "contact_name": "VARCHAR(128)",
                "company_name": "VARCHAR(256)",
                "email": "VARCHAR(256)",
                "phone": "VARCHAR(64)",
                "website": "VARCHAR(512)",
                "location": "VARCHAR(256)",
                "industry": "VARCHAR(128)",
                "updated_at": "VARCHAR(64)",
            }
            
            with self.engine.connect() as conn:
                for col_name, col_type in new_columns.items():
                    if col_name not in existing_columns:
                        try:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            # Column might already exist or DB doesn't support ALTER
                            pass

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
                return self._user_to_dict(user)
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
                return self._user_to_dict(user)

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Get user by ID."""
        with self.Session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                return self._user_to_dict(user)
        return None

    def get_user_by_wallet(self, wallet_address: str) -> dict[str, Any] | None:
        """Get user by wallet address."""
        with self.Session() as session:
            user = session.query(User).filter(User.wallet_address == wallet_address).first()
            if user:
                return self._user_to_dict(user)
        return None

    def _user_to_dict(self, user: User) -> dict[str, Any]:
        """Convert User model to dictionary with all fields.
        
        Uses getattr with defaults to handle databases that don't have
        the new profile columns yet (backwards compatibility).
        """
        return {
            "user_id": user.user_id,
            "wallet_address": user.wallet_address,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "is_active": user.is_active,
            # Profile fields (with defaults for backwards compatibility)
            "contact_name": getattr(user, "contact_name", None),
            "company_name": getattr(user, "company_name", None),
            "email": getattr(user, "email", None),
            "phone": getattr(user, "phone", None),
            "website": getattr(user, "website", None),
            "location": getattr(user, "location", None),
            "industry": getattr(user, "industry", None),
            "updated_at": getattr(user, "updated_at", None),
        }

    def update_profile(
        self,
        user_id: str,
        contact_name: str | None = None,
        company_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        website: str | None = None,
        location: str | None = None,
        industry: str | None = None,
    ) -> dict[str, Any] | None:
        """Update user profile fields. Only provided fields are updated."""
        with self.Session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return None
            
            now = datetime.now(timezone.utc).isoformat()
            
            # Update only fields that are explicitly provided (not None)
            if contact_name is not None:
                user.contact_name = contact_name if contact_name else None
            if company_name is not None:
                user.company_name = company_name if company_name else None
            if email is not None:
                user.email = email if email else None
            if phone is not None:
                user.phone = phone if phone else None
            if website is not None:
                user.website = website if website else None
            if location is not None:
                user.location = location if location else None
            if industry is not None:
                user.industry = industry if industry else None
            
            user.updated_at = now
            session.commit()
            
            return self._user_to_dict(user)

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get user profile by user ID."""
        with self.Session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                return self._user_to_dict(user)
        return None

