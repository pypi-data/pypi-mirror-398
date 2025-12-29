"""
SQLAlchemy model for quality_metrics table.

Stores quality check results and metrics for data quality assurance.
"""

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class QualityMetricModel(Base):
    """SQLAlchemy model for quality_metrics table."""

    __tablename__ = "quality_metrics"

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

    # Quality scores
    overall_score = Column(Float, nullable=False)  # 0-100
    violation_rate = Column(Float, nullable=False)  # 0-1
    completeness = Column(Float, nullable=False)  # 0-1
    accuracy = Column(Float, nullable=False)  # 0-1

    # Record counts
    record_count = Column(Integer, nullable=False, default=0)
    valid_count = Column(Integer, nullable=False, default=0)
    invalid_count = Column(Integer, nullable=False, default=0)
    violation_count = Column(Integer, nullable=False, default=0)

    # Field-level scores (stored as JSON)
    field_scores = Column(JSON, nullable=True)  # Dict[str, float]

    # Threshold check results
    threshold_breaches = Column(JSON, nullable=True)  # List[str]
    passed = Column(String(10), nullable=False, default="true")  # "true" or "false"

    # Data version tracking
    data_version = Column(String(255), nullable=True, index=True)  # Version/hash of the dataset
    data_source = Column(String(500), nullable=True)  # Source identifier (file path, table name, etc.)
    data_fingerprint = Column(String(64), nullable=True, index=True)  # Hash fingerprint of data for deduplication

    # Additional metadata
    check_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    additional_metadata = Column(JSON, nullable=True)  # Additional context (renamed from 'metadata' to avoid SQLAlchemy conflict)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(String(255), nullable=True)

    __table_args__ = ({"schema": "pycharter"},)

    # Relationships
    data_contract = relationship("DataContractModel", foreign_keys=[data_contract_id])

