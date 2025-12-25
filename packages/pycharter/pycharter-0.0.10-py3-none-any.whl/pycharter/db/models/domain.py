"""
SQLAlchemy model for domains table.

Stores domain information that can be referenced by metadata_records.
"""

import uuid

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class DomainModel(Base):
    """SQLAlchemy model for domains table."""

    __tablename__ = "domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Domain identifier
    name = Column(String(255), nullable=False, unique=True)  # Domain name (e.g., "IOC")
    description = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_domains_name"),
        {"schema": "pycharter"},
    )

    # Relationships
    metadata_records = relationship(
        "MetadataRecordDomain", back_populates="domain", cascade="all, delete-orphan"
    )
