"""
SQLAlchemy model for validation_rules table.

Based on template_validation_rules.yaml structure, stores validation rules
that define business logic validations applied after coercion.
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class ValidationRuleModel(Base):
    """SQLAlchemy model for validation_rules table."""

    __tablename__ = "validation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    title = Column(String(255), nullable=False)
    data_contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.data_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    description = Column(String(500), nullable=True)
    version = Column(String(50), nullable=False)

    # Validation Rules (field_name -> validation_config mapping)
    rules = Column(
        JSON, nullable=False
    )  # Dict mapping field names to validation configs

    # Optional: Link to schema if needed
    schema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.schemas.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "data_contract_id", "version", name="uq_validation_rules_contract_version"
        ),
        {"schema": "pycharter"},
    )

    # Relationships
    data_contract = relationship("DataContractModel", foreign_keys=[data_contract_id])
    schema = relationship("SchemaModel", back_populates="validation_rules")
