"""
SQLAlchemy model for quality_violations table.

Stores individual data quality violations detected during quality checks.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class QualityViolationModel(Base):
    """SQLAlchemy model for quality_violations table."""

    __tablename__ = "quality_violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Schema/Contract reference
    schema_id = Column(String(255), nullable=False, index=True)
    schema_version = Column(String(50), nullable=True)
    data_contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.data_contracts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Record information
    record_identifier = Column(String(255), nullable=True, index=True)  # Unique ID for the violating record
    record_data = Column(JSON, nullable=True)  # Snapshot of the violating record

    # Violation details
    field_name = Column(String(255), nullable=True, index=True)
    error_type = Column(String(100), nullable=False, index=True)
    error_message = Column(Text, nullable=False)

    # Violation metadata
    severity = Column(String(20), nullable=False, default="warning", index=True)  # critical, warning, info
    status = Column(String(20), nullable=False, default="open", index=True)  # open, resolved, ignored

    # Resolution tracking
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)

    # Additional metadata
    check_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    additional_metadata = Column(JSON, nullable=True)  # Additional context (renamed from 'metadata' to avoid SQLAlchemy conflict)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = ({"schema": "pycharter"},)

    # Relationships
    data_contract = relationship("DataContractModel", foreign_keys=[data_contract_id])

