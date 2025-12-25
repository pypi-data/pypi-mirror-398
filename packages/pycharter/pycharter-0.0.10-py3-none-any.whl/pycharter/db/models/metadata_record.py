"""
SQLAlchemy model for metadata_records table.

Based on template_metadata.yaml structure, stores comprehensive metadata
including audit information, data lineage, governance rules, and ownership.

Relationships:
- pulls_from: Many-to-many with systems (via MetadataRecordSystemPull)
- pushes_to: Many-to-many with systems (via MetadataRecordSystemPush)
- system_sources: Many-to-many with systems (via MetadataRecordSystemSource)
- domains: Many-to-many with domains (via MetadataRecordDomain)
"""

import uuid

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class MetadataRecordModel(Base):
    """SQLAlchemy model for metadata_records table."""

    __tablename__ = "metadata_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    title = Column(String(255), nullable=False)
    data_contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.data_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    version = Column(String(50), nullable=False)
    status = Column(String(50), nullable=True)  # e.g., "active", "deprecated", "draft"
    type = Column(String(50), nullable=True)  # e.g., "object"
    description = Column(Text, nullable=True)

    # Audit Information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    # Governance Rules (stored as JSON)
    governance_rules = Column(JSON, nullable=True)  # Full governance rules object

    __table_args__ = (
        UniqueConstraint(
            "data_contract_id", "version", name="uq_metadata_records_contract_version"
        ),
        {"schema": "pycharter"},
    )

    # Relationships
    data_contract = relationship("DataContractModel", foreign_keys=[data_contract_id])

    # Relationships to systems (via join tables)
    system_pulls = relationship(
        "MetadataRecordSystemPull",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )
    system_pushes = relationship(
        "MetadataRecordSystemPush",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )
    system_sources_rel = relationship(
        "MetadataRecordSystemSource",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )

    # Relationships to domains (via join table)
    domains_rel = relationship(
        "MetadataRecordDomain",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )

    # Relationships to owners (via join tables)
    business_owners_rel = relationship(
        "MetadataRecordBusinessOwner",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )
    bu_sme_rel = relationship(
        "MetadataRecordBUSME",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )
    it_application_owners_rel = relationship(
        "MetadataRecordITApplicationOwner",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )
    it_sme_rel = relationship(
        "MetadataRecordITSME",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )
    support_lead_rel = relationship(
        "MetadataRecordSupportLead",
        back_populates="metadata_record",
        cascade="all, delete-orphan",
    )


# Join tables for many-to-many relationships


class MetadataRecordSystemPull(Base):
    """Join table for metadata_records and systems (pulls_from relationship)."""

    __tablename__ = "metadata_record_system_pulls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.systems.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "system_id", name="uq_mr_system_pull"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship("MetadataRecordModel", back_populates="system_pulls")
    system = relationship("SystemModel", back_populates="metadata_pulls")


class MetadataRecordSystemPush(Base):
    """Join table for metadata_records and systems (pushes_to relationship)."""

    __tablename__ = "metadata_record_system_pushes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.systems.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "system_id", name="uq_mr_system_push"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship(
        "MetadataRecordModel", back_populates="system_pushes"
    )
    system = relationship("SystemModel", back_populates="metadata_pushes")


class MetadataRecordSystemSource(Base):
    """Join table for metadata_records and systems (system_sources relationship)."""

    __tablename__ = "metadata_record_system_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.systems.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "system_id", name="uq_mr_system_source"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship(
        "MetadataRecordModel", back_populates="system_sources_rel"
    )
    system = relationship("SystemModel", back_populates="metadata_sources")


class MetadataRecordDomain(Base):
    """Join table for metadata_records and domains."""

    __tablename__ = "metadata_record_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.domains.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "domain_id", name="uq_mr_domain"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship("MetadataRecordModel", back_populates="domains_rel")
    domain = relationship("DomainModel", back_populates="metadata_records")


# Join tables for ownership relationships (many-to-many with owners)


class MetadataRecordBusinessOwner(Base):
    """Join table for metadata_records and owners (business_owners relationship)."""

    __tablename__ = "metadata_record_business_owners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(
        String(255),
        ForeignKey("pycharter.owners.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "owner_id", name="uq_mr_business_owner"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship(
        "MetadataRecordModel", back_populates="business_owners_rel"
    )
    owner = relationship("OwnerModel", back_populates="business_owner_metadata_records")


class MetadataRecordBUSME(Base):
    """Join table for metadata_records and owners (bu_sme relationship)."""

    __tablename__ = "metadata_record_bu_sme"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(
        String(255),
        ForeignKey("pycharter.owners.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "owner_id", name="uq_mr_bu_sme"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship("MetadataRecordModel", back_populates="bu_sme_rel")
    owner = relationship("OwnerModel", back_populates="bu_sme_metadata_records")


class MetadataRecordITApplicationOwner(Base):
    """Join table for metadata_records and owners (it_application_owners relationship)."""

    __tablename__ = "metadata_record_it_application_owners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(
        String(255),
        ForeignKey("pycharter.owners.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "metadata_record_id", "owner_id", name="uq_mr_it_application_owner"
        ),
        {"schema": "pycharter"},
    )

    metadata_record = relationship(
        "MetadataRecordModel", back_populates="it_application_owners_rel"
    )
    owner = relationship(
        "OwnerModel", back_populates="it_application_owner_metadata_records"
    )


class MetadataRecordITSME(Base):
    """Join table for metadata_records and owners (it_sme relationship)."""

    __tablename__ = "metadata_record_it_sme"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(
        String(255),
        ForeignKey("pycharter.owners.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "owner_id", name="uq_mr_it_sme"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship("MetadataRecordModel", back_populates="it_sme_rel")
    owner = relationship("OwnerModel", back_populates="it_sme_metadata_records")


class MetadataRecordSupportLead(Base):
    """Join table for metadata_records and owners (support_lead relationship)."""

    __tablename__ = "metadata_record_support_lead"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metadata_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pycharter.metadata_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(
        String(255),
        ForeignKey("pycharter.owners.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("metadata_record_id", "owner_id", name="uq_mr_support_lead"),
        {"schema": "pycharter"},
    )

    metadata_record = relationship(
        "MetadataRecordModel", back_populates="support_lead_rel"
    )
    owner = relationship("OwnerModel", back_populates="support_lead_metadata_records")
