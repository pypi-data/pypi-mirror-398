"""
Violation tracking for data quality issues.
"""

import hashlib
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from pycharter.runtime_validator.validator_core import ValidationResult


def _serialize_for_json(obj: Any) -> Any:
    """
    Recursively serialize objects to be JSON-compatible.
    
    Converts datetime, date, and other non-serializable types to strings.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    elif isinstance(obj, UUID):
        return str(obj)
    else:
        # Try to serialize, fall back to string representation
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ViolationRecord:
    """Represents a single data quality violation."""

    def __init__(
        self,
        schema_id: str,
        record_id: Optional[str],
        record_data: Dict[str, Any],
        validation_result: ValidationResult,
        severity: str = "warning",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a violation record.

        Args:
            schema_id: Schema identifier
            record_id: Optional record identifier (if None, will be generated from data hash)
            record_data: The data record that violated the contract
            validation_result: ValidationResult with errors
            severity: Violation severity (critical, warning, info)
            metadata: Optional additional metadata
        """
        self.id = uuid4()
        self.schema_id = schema_id
        self.record_id = record_id or self._generate_record_id(record_data)
        self.record_data = record_data
        self.validation_result = validation_result
        self.severity = severity
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.status = "open"  # open, resolved, ignored
        self.resolved_at: Optional[datetime] = None
        self.resolved_by: Optional[str] = None

        # Extract field-level violations
        self.field_violations = self._extract_field_violations(validation_result)

    def _generate_record_id(self, record_data: Dict[str, Any]) -> str:
        """Generate a record ID from data hash."""
        data_str = json.dumps(record_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def _extract_field_violations(
        self, validation_result: ValidationResult
    ) -> List[Dict[str, Any]]:
        """Extract field-level violation details from validation result."""
        violations = []

        if not validation_result.is_valid:
            for error in validation_result.errors:
                violation = {
                    "field": self._extract_field_name(error),
                    "error_type": self._extract_error_type(error),
                    "error_message": str(error),
                }
                violations.append(violation)

        return violations

    def _extract_field_name(self, error: Any) -> str:
        """Extract field name from validation error."""
        if isinstance(error, dict):
            loc = error.get("loc", [])
            if loc:
                return str(loc[-1]) if isinstance(loc[-1], str) else "unknown"
        return "unknown"

    def _extract_error_type(self, error: Any) -> str:
        """Extract error type from validation error."""
        if isinstance(error, dict):
            return error.get("type", "validation_error")
        elif isinstance(error, str):
            error_lower = error.lower()
            if "missing" in error_lower:
                return "missing_field"
            elif "type" in error_lower:
                return "type_error"
            else:
                return "validation_error"
        return "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert violation record to dictionary."""
        return {
            "id": str(self.id),
            "schema_id": self.schema_id,
            "record_id": self.record_id,
            "record_data": self.record_data,
            "severity": self.severity,
            "status": self.status,
            "field_violations": self.field_violations,
            "error_count": len(self.field_violations),
            "timestamp": self.timestamp.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "metadata": self.metadata,
        }


class ViolationTracker:
    """Track and persist data quality violations."""

    def __init__(self, store=None, db_session: Optional["Session"] = None):
        """
        Initialize violation tracker.

        Args:
            store: Optional metadata store (for backward compatibility)
            db_session: Optional SQLAlchemy database session for persistence
        """
        self.store = store
        self.db_session = db_session
        self._in_memory_violations: List[ViolationRecord] = []

    def record_violation(
        self,
        schema_id: str,
        record_id: Optional[str],
        record_data: Dict[str, Any],
        validation_result: ValidationResult,
        severity: str = "warning",
        metadata: Optional[Dict[str, Any]] = None,
        deduplicate: bool = True,
    ) -> ViolationRecord:
        """
        Record a quality violation.

        Args:
            schema_id: Schema identifier
            record_id: Optional record identifier
            record_data: The data record that violated the contract
            validation_result: ValidationResult with errors
            severity: Violation severity (critical, warning, info)
            metadata: Optional additional metadata

        Returns:
            ViolationRecord object
        """
        violation = ViolationRecord(
            schema_id=schema_id,
            record_id=record_id,
            record_data=record_data,
            validation_result=validation_result,
            severity=severity,
            metadata=metadata,
        )

        # Store in memory
        self._in_memory_violations.append(violation)

        # Persist to database if session is available
        if self.db_session:
            self._persist_violation(violation, deduplicate=deduplicate)

        return violation

    def _persist_violation(self, violation: ViolationRecord, deduplicate: bool = True):
        """Persist violation to database with optional deduplication."""
        if not self.db_session:
            return

        try:
            from pycharter.db.models.quality_violation import QualityViolationModel
            from pycharter.db.models.schema import SchemaModel
            from sqlalchemy import and_

            # Look up schema information to get schema_version and data_contract_id
            schema_version = None
            data_contract_id = None
            try:
                # Try to parse schema_id as UUID
                from uuid import UUID as UUIDType
                schema_uuid = UUIDType(violation.schema_id)
                schema = self.db_session.query(SchemaModel).filter(
                    SchemaModel.id == schema_uuid
                ).first()
            except (ValueError, TypeError):
                # If schema_id is not a UUID, try as string
                schema = self.db_session.query(SchemaModel).filter(
                    SchemaModel.id == violation.schema_id
                ).first()
            
            if schema:
                schema_version = schema.version
                data_contract_id = schema.data_contract_id

            # Serialize record_data and metadata once before the loop to ensure JSON compatibility
            serialized_record_data = _serialize_for_json(violation.record_data) if violation.record_data else None
            serialized_metadata = _serialize_for_json(violation.metadata) if violation.metadata else None

            # Extract field-level violations from the validation result
            # Each field violation needs a unique ID, so we generate one for each
            for field_violation in violation.field_violations:
                field_name = field_violation.get("field")
                error_type = field_violation.get("error_type", "validation_error")
                
                # Generate a unique ID for this field-level violation
                # (Each field violation is a separate row in the database)
                violation_id = uuid4()
                
                # Check for existing violation if deduplication enabled
                # Use no_autoflush to prevent premature flushing of pending objects
                if deduplicate:
                    with self.db_session.no_autoflush:
                        existing = self.db_session.query(QualityViolationModel).filter(
                            and_(
                                QualityViolationModel.schema_id == violation.schema_id,
                                QualityViolationModel.record_identifier == violation.record_id,
                                QualityViolationModel.field_name == field_name,
                                QualityViolationModel.error_type == error_type,
                                QualityViolationModel.status == "open"  # Only deduplicate open violations
                            )
                        ).first()
                    
                    if existing:
                        # Update timestamp to show it was re-detected
                        existing.check_timestamp = violation.timestamp
                        # Update record_data if it has changed (already serialized)
                        if serialized_record_data:
                            existing.record_data = serialized_record_data
                        # Update schema_version and data_contract_id if they're missing
                        if schema_version and not existing.schema_version:
                            existing.schema_version = schema_version
                        if data_contract_id and not existing.data_contract_id:
                            existing.data_contract_id = data_contract_id
                        continue  # Skip creating duplicate
                
                # Create new violation (using pre-serialized data and unique ID)
                violation_model = QualityViolationModel(
                    id=violation_id,  # Use unique ID for each field-level violation
                    schema_id=violation.schema_id,
                    schema_version=schema_version,  # Set from schema lookup
                    data_contract_id=data_contract_id,  # Set from schema lookup
                    record_identifier=violation.record_id,
                    record_data=serialized_record_data,
                    field_name=field_name,
                    error_type=error_type,
                    error_message=field_violation.get("error_message", str(field_violation)),
                    severity=violation.severity,
                    status=violation.status,
                    check_timestamp=violation.timestamp,
                    additional_metadata=serialized_metadata,
                )
                self.db_session.add(violation_model)

            self.db_session.commit()
        except Exception as e:
            # Rollback on error and log (but don't fail the quality check)
            if self.db_session:
                self.db_session.rollback()
            # Log error but continue (violations are still in memory)
            import logging
            logging.warning(f"Failed to persist violation to database: {e}")

    def get_violations(
        self,
        schema_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ViolationRecord]:
        """
        Query violations.

        Args:
            schema_id: Filter by schema ID
            start_date: Filter violations after this date
            end_date: Filter violations before this date
            severity: Filter by severity (critical, warning, info)
            status: Filter by status (open, resolved, ignored)
            limit: Optional limit on number of violations to return

        Returns:
            List of ViolationRecord objects
        """
        # If database session is available, query from database
        if self.db_session:
            return self._get_violations_from_db(
                schema_id=schema_id,
                start_date=start_date,
                end_date=end_date,
                severity=severity,
                status=status,
                limit=limit,
            )

        # Otherwise, use in-memory violations
        violations = self._in_memory_violations.copy()

        # Apply filters
        if schema_id:
            violations = [v for v in violations if v.schema_id == schema_id]

        if start_date:
            violations = [v for v in violations if v.timestamp >= start_date]

        if end_date:
            violations = [v for v in violations if v.timestamp <= end_date]

        if severity:
            violations = [v for v in violations if v.severity == severity]

        if status:
            violations = [v for v in violations if v.status == status]

        # Apply limit if specified
        if limit is not None:
            violations = violations[:limit]

        return violations

    def _get_violations_from_db(
        self,
        schema_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ViolationRecord]:
        """Query violations from database."""
        from pycharter.db.models.quality_violation import QualityViolationModel
        from sqlalchemy import and_

        query = self.db_session.query(QualityViolationModel)

        # Apply filters
        filters = []
        if schema_id:
            filters.append(QualityViolationModel.schema_id == schema_id)
        if start_date:
            filters.append(QualityViolationModel.check_timestamp >= start_date)
        if end_date:
            filters.append(QualityViolationModel.check_timestamp <= end_date)
        if severity:
            filters.append(QualityViolationModel.severity == severity)
        if status:
            filters.append(QualityViolationModel.status == status)

        if filters:
            query = query.filter(and_(*filters))

        # Apply limit if specified
        if limit is not None:
            query = query.limit(limit)

        db_violations = query.all()

        # Convert database models to ViolationRecord objects
        # Group by record_identifier to reconstruct full ViolationRecord objects
        violation_groups: Dict[str, List[QualityViolationModel]] = {}
        for db_violation in db_violations:
            record_id = db_violation.record_identifier or "unknown"
            if record_id not in violation_groups:
                violation_groups[record_id] = []
            violation_groups[record_id].append(db_violation)

        violations = []
        for record_id, db_violations_group in violation_groups.items():
            # Use the first violation as the base
            base_violation = db_violations_group[0]

            # Reconstruct ValidationResult from error messages
            errors = []
            for db_violation in db_violations_group:
                errors.append({
                    "loc": (db_violation.field_name,) if db_violation.field_name else (),
                    "type": db_violation.error_type,
                    "msg": db_violation.error_message,
                })

            # Create a mock ValidationResult
            validation_result = ValidationResult(
                is_valid=False,
                errors=errors,
                data=None,
            )

            violation = ViolationRecord(
                schema_id=base_violation.schema_id,
                record_id=base_violation.record_identifier,
                record_data=base_violation.record_data or {},
                validation_result=validation_result,
                severity=base_violation.severity,
                metadata=base_violation.metadata or {},
            )
            violation.id = base_violation.id
            violation.timestamp = base_violation.check_timestamp
            violation.status = base_violation.status
            violation.resolved_at = base_violation.resolved_at
            violation.resolved_by = base_violation.resolved_by
            violation.metadata = base_violation.additional_metadata or {}

            violations.append(violation)

        return violations

    def resolve_violation(
        self, violation_id: UUID, resolved_by: str
    ) -> Optional[ViolationRecord]:
        """
        Mark a violation as resolved.

        Args:
            violation_id: Violation ID
            resolved_by: User/process that resolved the violation

        Returns:
            Updated ViolationRecord or None if not found
        """
        # If database session is available, update in database
        if self.db_session:
            from pycharter.db.models.quality_violation import QualityViolationModel

            db_violation = self.db_session.query(QualityViolationModel).filter(
                QualityViolationModel.id == violation_id
            ).first()

            if db_violation:
                db_violation.status = "resolved"
                db_violation.resolved_at = datetime.utcnow()
                db_violation.resolved_by = resolved_by
                self.db_session.commit()

                # Return updated violation (convert from DB model)
                violations = self.get_violations()
                for violation in violations:
                    if violation.id == violation_id:
                        return violation

        # Otherwise, update in-memory
        for violation in self._in_memory_violations:
            if violation.id == violation_id:
                violation.status = "resolved"
                violation.resolved_at = datetime.utcnow()
                violation.resolved_by = resolved_by
                return violation

        return None

    def get_violation_summary(
        self, schema_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for violations.

        Args:
            schema_id: Optional schema ID to filter by

        Returns:
            Dictionary with violation statistics
        """
        violations = self.get_violations(schema_id=schema_id)

        summary = {
            "total": len(violations),
            "open": sum(1 for v in violations if v.status == "open"),
            "resolved": sum(1 for v in violations if v.status == "resolved"),
            "ignored": sum(1 for v in violations if v.status == "ignored"),
            "by_severity": {
                "critical": sum(1 for v in violations if v.severity == "critical"),
                "warning": sum(1 for v in violations if v.severity == "warning"),
                "info": sum(1 for v in violations if v.severity == "info"),
            },
        }

        return summary

