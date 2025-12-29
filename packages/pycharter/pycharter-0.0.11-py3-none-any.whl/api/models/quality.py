"""
Pydantic models for quality assurance API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QualityCheckRequest(BaseModel):
    """Request model for quality check."""

    schema_id: Optional[str] = Field(None, description="Schema ID (for store-based validation)")
    contract: Optional[Dict[str, Any]] = Field(None, description="Contract dictionary (for contract-based validation)")
    data: List[Dict[str, Any]] = Field(..., description="Data records to validate")
    record_violations: bool = Field(True, description="Record violations")
    calculate_metrics: bool = Field(True, description="Calculate quality metrics")
    check_thresholds: bool = Field(False, description="Check quality thresholds")
    thresholds: Optional[Dict[str, Any]] = Field(None, description="Quality thresholds")
    include_field_metrics: bool = Field(True, description="Include field-level metrics")
    sample_size: Optional[int] = Field(None, description="Sample size for large datasets")
    data_source: Optional[str] = Field(None, description="Data source identifier (e.g., file name, table name)")
    data_version: Optional[str] = Field(None, description="Data version identifier for tracking")


class QualityScoreResponse(BaseModel):
    """Quality score response model."""

    overall_score: float
    violation_rate: float
    completeness: float
    accuracy: float
    field_scores: Dict[str, float] = Field(default_factory=dict)
    record_count: int
    valid_count: int
    invalid_count: int


class FieldQualityMetricsResponse(BaseModel):
    """Field quality metrics response model."""

    field_name: str
    null_count: int
    violation_count: int
    total_count: int
    violation_rate: float
    completeness: float
    error_types: Dict[str, int] = Field(default_factory=dict)


class QualityReportResponse(BaseModel):
    """Quality report response model."""

    schema_id: str
    schema_version: Optional[str] = None
    check_timestamp: datetime
    quality_score: Optional[QualityScoreResponse] = None
    field_metrics: Dict[str, FieldQualityMetricsResponse] = Field(default_factory=dict)
    violation_count: int
    record_count: int
    valid_count: int
    invalid_count: int
    threshold_breaches: List[str] = Field(default_factory=list)
    passed: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ViolationQueryRequest(BaseModel):
    """Request model for querying violations."""

    schema_id: Optional[str] = Field(None, description="Filter by schema ID")
    status: Optional[str] = Field(None, description="Filter by status (open, resolved, ignored)")
    severity: Optional[str] = Field(None, description="Filter by severity (critical, warning, info)")
    start_date: Optional[datetime] = Field(None, description="Filter violations after this date")
    end_date: Optional[datetime] = Field(None, description="Filter violations before this date")


class ViolationRecordResponse(BaseModel):
    """Violation record response model."""

    id: str
    schema_id: str
    record_id: str
    severity: str
    status: str
    field_violations: List[Dict[str, Any]] = Field(default_factory=list)
    error_count: int
    timestamp: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ViolationsResponse(BaseModel):
    """Violations query response model."""

    violations: List[ViolationRecordResponse]
    total: int
    summary: Dict[str, Any] = Field(default_factory=dict)

