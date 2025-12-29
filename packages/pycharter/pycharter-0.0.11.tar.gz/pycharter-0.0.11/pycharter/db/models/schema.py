"""
SQLAlchemy model for schemas table.

Based on template_schema.yaml structure, stores JSON Schema definitions
that define the structure and validation rules for data.
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class SchemaModel(Base):
    """SQLAlchemy model for schemas table."""

    __tablename__ = "schemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    title = Column(String(255), nullable=False)
    data_contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.data_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    version = Column(String(50), nullable=False)

    # JSON Schema Data (full schema definition)
    schema_data = Column(JSON, nullable=False)  # Complete JSON Schema object

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "data_contract_id", "version", name="uq_schemas_contract_version"
        ),
        {"schema": "pycharter"},
    )

    # Relationships
    data_contract = relationship("DataContractModel", foreign_keys=[data_contract_id])
    coercion_rules = relationship(
        "CoercionRuleModel", back_populates="schema", cascade="all, delete-orphan"
    )
    validation_rules = relationship(
        "ValidationRuleModel", back_populates="schema", cascade="all, delete-orphan"
    )
    # Note: governance_rules are stored as JSON in metadata_records, not as a separate table
