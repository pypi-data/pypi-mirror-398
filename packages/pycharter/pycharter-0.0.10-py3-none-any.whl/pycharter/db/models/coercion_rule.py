"""
SQLAlchemy model for coercion_rules table.

Based on template_coercion_rules.yaml structure, stores coercion rules
that define how to transform data types before validation.
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class CoercionRuleModel(Base):
    """SQLAlchemy model for coercion_rules table."""

    __tablename__ = "coercion_rules"

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

    # Coercion Rules (field_name -> coercion_function mapping)
    rules = Column(
        JSON, nullable=False
    )  # Dict mapping field names to coercion functions

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
            "data_contract_id", "version", name="uq_coercion_rules_contract_version"
        ),
        {"schema": "pycharter"},
    )

    # Relationships
    data_contract = relationship("DataContractModel", foreign_keys=[data_contract_id])
    schema = relationship("SchemaModel", back_populates="coercion_rules")
