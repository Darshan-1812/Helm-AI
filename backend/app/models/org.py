"""
Organization model — multi-tenant root entity.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organization(Base):
    """Represents a tenant/workspace in the platform."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    # Relationships
    runs = relationship("Run", back_populates="organization", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
