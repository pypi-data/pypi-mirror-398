from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from acto.registry.models import Base


class User(Base):
    """User model for wallet-based authentication."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[str] = mapped_column(String(64), index=True)
    last_login_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    
    # Profile fields (all optional)
    contact_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

