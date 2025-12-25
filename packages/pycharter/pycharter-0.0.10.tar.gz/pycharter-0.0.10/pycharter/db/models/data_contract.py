"""
SQLAlchemy model for data_contracts table.

Based on template_contract.yaml structure, this is the central table that
links all components of a data contract together:
- Schema
- Coercion Rules
- Validation Rules
- Metadata Records

Note: Ownership and governance rules are stored within metadata_records,
not as separate foreign keys in data_contracts.

Each data contract represents a versioned contract for a specific dataset.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class DataContractModel(Base):
    """SQLAlchemy model for data_contracts table."""

    __tablename__ = "data_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core identifiers
    name = Column(
        String(255), nullable=False
    )  # Contract name (e.g., "template_contract")
    version = Column(String(50), nullable=False)  # Contract version (e.g., "1.0.0")
    status = Column(String(50), nullable=True)  # e.g., "active", "deprecated", "draft"
    description = Column(Text, nullable=True)

    # Foreign keys to component tables
    # Note: schema_id is nullable to allow creating data_contract first, then schema
    schema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.schemas.id", ondelete="CASCADE"),
        nullable=True,
    )
    coercion_rules_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.coercion_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    validation_rules_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.validation_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Note: owner and governance_rules are stored in metadata_records, not as separate foreign keys

    # Version tracking (from template_contract.yaml versions section)
    schema_version = Column(String(50), nullable=True)
    coercion_rules_version = Column(String(50), nullable=True)
    validation_rules_version = Column(String(50), nullable=True)
    metadata_version = Column(String(50), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_data_contracts_name_version"),
        {"schema": "pycharter"},
    )

    # Relationships to component tables
    schema = relationship("SchemaModel", foreign_keys=[schema_id])
    coercion_rules = relationship("CoercionRuleModel", foreign_keys=[coercion_rules_id])
    validation_rules = relationship(
        "ValidationRuleModel", foreign_keys=[validation_rules_id]
    )
    metadata_record = relationship(
        "MetadataRecordModel", foreign_keys=[metadata_record_id]
    )
    # Note: Access ownership and governance_rules via metadata_record relationship:
    #   data_contract.metadata_record.business_owners
    #   data_contract.metadata_record.governance_rules
