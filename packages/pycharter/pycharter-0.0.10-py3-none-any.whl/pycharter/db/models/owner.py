"""
SQLAlchemy model for owners table.

This is a lookup table of owners (people/teams) that can be referenced by metadata_records.
Ownership relationships are stored in join tables linking metadata_records to owners.

Note: This table stores owner entities. Ownership relationships are stored in join tables:
- metadata_record_business_owners
- metadata_record_bu_sme
- metadata_record_it_application_owners
- metadata_record_it_sme
- metadata_record_support_lead
"""

from sqlalchemy import JSON, Column, DateTime, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pycharter.db.models.base import Base


class OwnerModel(Base):
    """SQLAlchemy model for owners table - a lookup table of owner entities."""

    __tablename__ = "owners"

    id = Column(
        String(255), primary_key=True
    )  # Owner identifier (e.g., "lincoln_mak", "operations-team")

    # Owner Information
    name = Column(
        String(255), nullable=True
    )  # Display name (optional, defaults to id if not provided)
    email = Column(String(255), nullable=True)  # Owner email address
    team = Column(String(255), nullable=True)  # Team name (e.g., "data-engineering")

    # Additional Information
    additional_info = Column(JSON, nullable=True)  # Any additional owner metadata

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "email", name="uq_owners_email"
        ),  # Email should be unique if provided
        {"schema": "pycharter"},
    )

    # Relationships to metadata_records (via join tables)
    business_owner_metadata_records = relationship(
        "MetadataRecordBusinessOwner",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    bu_sme_metadata_records = relationship(
        "MetadataRecordBUSME", back_populates="owner", cascade="all, delete-orphan"
    )
    it_application_owner_metadata_records = relationship(
        "MetadataRecordITApplicationOwner",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    it_sme_metadata_records = relationship(
        "MetadataRecordITSME", back_populates="owner", cascade="all, delete-orphan"
    )
    support_lead_metadata_records = relationship(
        "MetadataRecordSupportLead",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
