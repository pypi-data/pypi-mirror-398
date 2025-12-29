"""
Pydantic models for validation jobs and results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationJobRequest(BaseModel):
    """Request to submit a validation job."""

    schema_id: str = Field(..., description="Schema ID from metadata store")
    data_source: str = Field(
        ..., description="Data source (S3 path, file path, table name)"
    )
    options: Optional[Dict[str, Any]] = Field(
        None, description="Validation options"
    )


class ValidationJobResponse(BaseModel):
    """Response after submitting a validation job."""

    job_id: str
    status: str
    message: str
    created_at: str


class ValidationJobStatus(BaseModel):
    """Job status response."""

    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ValidationResult(BaseModel):
    """Validation result from worker."""

    total_count: int
    valid_count: int
    invalid_count: int
    violations: List[str]
    quality_score: float = Field(..., ge=0.0, le=1.0)
    data_source: str
    field_scores: Optional[Dict[str, float]] = None

