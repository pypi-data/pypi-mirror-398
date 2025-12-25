"""
Data models for quality assurance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class QualityScore(BaseModel):
    """Quality score metrics for a dataset."""

    overall_score: float = Field(ge=0.0, le=100.0)  # 0-100
    violation_rate: float = Field(ge=0.0, le=1.0)  # 0-1 (percentage of records with violations)
    completeness: float = Field(ge=0.0, le=1.0)  # 0-1 (percentage of required fields present)
    accuracy: float = Field(ge=0.0, le=1.0)  # 0-1 (percentage of valid records)
    field_scores: Dict[str, float] = Field(default_factory=dict)  # Per-field scores
    record_count: int = 0
    valid_count: int = 0
    invalid_count: int = 0


class FieldQualityMetrics(BaseModel):
    """Quality metrics for a specific field."""

    field_name: str
    null_count: int = 0
    violation_count: int = 0
    total_count: int = 0
    violation_rate: float = 0.0
    completeness: float = 1.0
    error_types: Dict[str, int] = Field(default_factory=dict)  # Error type -> count

    def calculate_metrics(self):
        """Calculate derived metrics."""
        if self.total_count > 0:
            self.violation_rate = self.violation_count / self.total_count
            self.completeness = 1.0 - (self.null_count / self.total_count)
        else:
            self.violation_rate = 0.0
            self.completeness = 0.0


class QualityThresholds(BaseModel):
    """Quality thresholds for alerting."""

    min_overall_score: float = 95.0
    max_violation_rate: float = 0.05  # 5%
    min_completeness: float = 0.95  # 95%
    min_accuracy: float = 0.95  # 95%
    field_thresholds: Dict[str, Dict[str, float]] = {}  # field_name -> {metric: threshold}

    def check(self, quality_score: QualityScore) -> List[str]:
        """
        Check if quality score breaches any thresholds.

        Returns:
            List of threshold breach messages (empty if all pass)
        """
        breaches = []

        if quality_score.overall_score < self.min_overall_score:
            breaches.append(
                f"Overall score {quality_score.overall_score:.2f} "
                f"below threshold {self.min_overall_score:.2f}"
            )

        if quality_score.violation_rate > self.max_violation_rate:
            breaches.append(
                f"Violation rate {quality_score.violation_rate:.2%} "
                f"exceeds threshold {self.max_violation_rate:.2%}"
            )

        if quality_score.completeness < self.min_completeness:
            breaches.append(
                f"Completeness {quality_score.completeness:.2%} "
                f"below threshold {self.min_completeness:.2%}"
            )

        if quality_score.accuracy < self.min_accuracy:
            breaches.append(
                f"Accuracy {quality_score.accuracy:.2%} "
                f"below threshold {self.min_accuracy:.2%}"
            )

        # Check field-specific thresholds
        for field_name, thresholds in self.field_thresholds.items():
            if field_name in quality_score.field_scores:
                field_score = quality_score.field_scores[field_name]
                if "min_score" in thresholds and field_score < thresholds["min_score"]:
                    breaches.append(
                        f"Field '{field_name}' score {field_score:.2f} "
                        f"below threshold {thresholds['min_score']:.2f}"
                    )

        return breaches


class QualityCheckOptions(BaseModel):
    """Options for quality checks."""

    record_violations: bool = True
    calculate_metrics: bool = True
    check_thresholds: bool = False
    thresholds: Optional[QualityThresholds] = None
    include_field_metrics: bool = True
    include_profiling: bool = False  # Include data profiling in report
    sample_size: Optional[int] = None  # If set, only check a sample of records
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)  # Additional metadata
    
    # Data version tracking and deduplication
    data_version: Optional[str] = None  # Version identifier for the dataset
    data_source: Optional[str] = None  # Source identifier (file path, table name, etc.)
    skip_if_unchanged: bool = False  # Skip check if data hasn't changed (requires data_fingerprint)
    deduplicate_violations: bool = True  # Deduplicate violations for same record+field+error


class QualityReport(BaseModel):
    """Complete quality check report."""

    schema_id: str
    schema_version: Optional[str] = None
    check_timestamp: datetime = Field(default_factory=datetime.utcnow)
    quality_score: Optional[QualityScore] = None
    field_metrics: Dict[str, FieldQualityMetrics] = Field(default_factory=dict)
    violation_count: int = 0
    record_count: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    threshold_breaches: List[str] = Field(default_factory=list)
    passed: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context):
        """Calculate passed status after initialization."""
        # Calculate passed status based on threshold breaches
        if self.threshold_breaches:
            self.passed = False
        elif self.quality_score:
            # If no thresholds set, pass if accuracy > 0
            self.passed = self.quality_score.accuracy > 0

