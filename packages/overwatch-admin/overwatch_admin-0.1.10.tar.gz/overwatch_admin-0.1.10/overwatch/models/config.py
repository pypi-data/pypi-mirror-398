"""
Overwatch Config models for dynamic configuration management.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from overwatch.core.database import Base


class Config(Base):
    """
    Overwatch Config model for dynamic configuration storage.

    This model stores dynamic configuration values that can be updated
    at runtime without requiring application restart.
    """

    __tablename__ = "overwatch_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    # Configuration metadata
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # Whether this config can be accessed by frontend
    category: Mapped[str | None] = mapped_column(
        String(50)
    )  # e.g., "ui", "security", "features"
    data_type: Mapped[str] = mapped_column(
        String(20), default="string"
    )  # string, integer, boolean, json

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[int | None] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"<Config(key='{self.key}', category='{self.category}')>"


# Event listeners for config model
@event.listens_for(Config, "before_update")
def update_config_timestamp(mapper, connection, target):
    """Update timestamp when config is modified."""
    target.updated_at = func.now()
