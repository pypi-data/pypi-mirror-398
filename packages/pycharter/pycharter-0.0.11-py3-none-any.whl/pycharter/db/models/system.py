"""
SQLAlchemy model for systems table.

Stores system information that can be referenced by metadata_records
for pulls_from, pushes_to, and system_sources relationships.
"""

import uuid

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class SystemModel(Base):
    """SQLAlchemy model for systems table."""

    __tablename__ = "systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # System identifier
    name = Column(
        String(255), nullable=False, unique=True
    )  # System name (e.g., "1811", "ICC", "1846")
    app_id = Column(String(255), nullable=True)  # Application ID for the system
    description = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_systems_name"),
        {"schema": "pycharter"},
    )

    # Relationships
    metadata_pulls = relationship(
        "MetadataRecordSystemPull",
        back_populates="system",
        cascade="all, delete-orphan",
    )
    metadata_pushes = relationship(
        "MetadataRecordSystemPush",
        back_populates="system",
        cascade="all, delete-orphan",
    )
    metadata_sources = relationship(
        "MetadataRecordSystemSource",
        back_populates="system",
        cascade="all, delete-orphan",
    )
