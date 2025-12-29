"""
Quality metrics calculation.
"""

from typing import Any, Dict, List, Optional

from pycharter.runtime_validator.validator_core import ValidationResult

from pycharter.quality.models import FieldQualityMetrics, QualityScore


class QualityMetrics:
    """Calculate quality metrics from validation results."""

    def calculate_quality_score(
        self,
        validation_results: List[ValidationResult],
        weights: Optional[Dict[str, float]] = None,
    ) -> QualityScore:
        """
        Calculate overall quality score from validation results.

        Args:
            validation_results: List of ValidationResult objects
            weights: Optional weights for different metrics
                     (default: equal weights for accuracy, completeness)

        Returns:
            QualityScore with overall score and metrics
        """
        if not validation_results:
            return QualityScore(
                overall_score=0.0,
                violation_rate=1.0,
                completeness=0.0,
                accuracy=0.0,
                record_count=0,
                valid_count=0,
                invalid_count=0,
            )

        # Default weights
        if weights is None:
            weights = {"accuracy": 0.5, "completeness": 0.5}

        # Calculate basic counts
        record_count = len(validation_results)
        valid_count = sum(1 for r in validation_results if r.is_valid)
        invalid_count = record_count - valid_count

        # Calculate accuracy (percentage of valid records)
        accuracy = valid_count / record_count if record_count > 0 else 0.0

        # Calculate violation rate (same as 1 - accuracy)
        violation_rate = invalid_count / record_count if record_count > 0 else 0.0

        # Calculate completeness (percentage of records with all required fields)
        # This is approximated by checking if errors are mostly "missing field" errors
        completeness = self._calculate_completeness(validation_results)

        # Calculate overall score (weighted average)
        overall_score = (
            weights.get("accuracy", 0.5) * accuracy * 100
            + weights.get("completeness", 0.5) * completeness * 100
        )

        # Calculate field-level scores
        field_scores = self._calculate_field_scores(validation_results)

        return QualityScore(
            overall_score=overall_score,
            violation_rate=violation_rate,
            completeness=completeness,
            accuracy=accuracy,
            field_scores=field_scores,
            record_count=record_count,
            valid_count=valid_count,
            invalid_count=invalid_count,
        )

    def _calculate_completeness(
        self, validation_results: List[ValidationResult]
    ) -> float:
        """
        Calculate completeness based on validation errors.

        Completeness = 1 - (records with missing required fields / total records)
        """
        if not validation_results:
            return 0.0

        missing_field_count = 0
        for result in validation_results:
            if not result.is_valid:
                # Check if errors are primarily "missing field" errors
                for error in result.errors:
                    error_str = str(error).lower()
                    if "missing" in error_str or "required" in error_str:
                        missing_field_count += 1
                        break  # Count each record only once

        total_records = len(validation_results)
        completeness = 1.0 - (missing_field_count / total_records)
        return max(0.0, min(1.0, completeness))

    def _calculate_field_scores(
        self, validation_results: List[ValidationResult]
    ) -> Dict[str, float]:
        """
        Calculate quality scores per field.

        Returns:
            Dictionary mapping field names to quality scores (0-100)
        """
        field_metrics = self.calculate_field_metrics(validation_results)
        field_scores = {}

        for field_name, metrics in field_metrics.items():
            # Score based on violation rate and completeness
            # Score = (1 - violation_rate) * completeness * 100
            score = (1.0 - metrics.violation_rate) * metrics.completeness * 100
            field_scores[field_name] = max(0.0, min(100.0, score))

        return field_scores

    def calculate_field_metrics(
        self, validation_results: List[ValidationResult]
    ) -> Dict[str, FieldQualityMetrics]:
        """
        Calculate quality metrics for each field.

        Args:
            validation_results: List of ValidationResult objects

        Returns:
            Dictionary mapping field names to FieldQualityMetrics
        """
        field_metrics: Dict[str, FieldQualityMetrics] = {}
        total_records = len(validation_results)

        # First, initialize all fields that appear in any record
        for result in validation_results:
            if result.data:
                for field_name in result.data.model_dump().keys():
                    if field_name not in field_metrics:
                        field_metrics[field_name] = FieldQualityMetrics(
                            field_name=field_name, total_count=total_records
                        )

        # Now process errors and null values
        for result in validation_results:
            # Process errors to extract field-level information
            if not result.is_valid:
                for error in result.errors:
                    field_name = self._extract_field_name(error)
                    if not field_name:
                        continue

                    if field_name not in field_metrics:
                        field_metrics[field_name] = FieldQualityMetrics(
                            field_name=field_name, total_count=total_records
                        )

                    metrics = field_metrics[field_name]
                    metrics.violation_count += 1

                    # Track error types
                    error_type = self._extract_error_type(error)
                    if error_type:
                        metrics.error_types[error_type] = (
                            metrics.error_types.get(error_type, 0) + 1
                        )

            # Check for null/missing values in validated data
            if result.data:
                for field_name, value in result.data.model_dump().items():
                    if field_name not in field_metrics:
                        field_metrics[field_name] = FieldQualityMetrics(
                            field_name=field_name, total_count=total_records
                        )

                    if value is None:
                        field_metrics[field_name].null_count += 1

        # Calculate derived metrics for each field
        for metrics in field_metrics.values():
            metrics.calculate_metrics()

        return field_metrics

    def _extract_field_name(self, error: Any) -> Optional[str]:
        """Extract field name from validation error."""
        if isinstance(error, dict):
            # Pydantic error format
            loc = error.get("loc", [])
            if loc:
                # Get the last location (field name)
                return str(loc[-1]) if isinstance(loc[-1], str) else None
        elif isinstance(error, str):
            # Try to extract field name from error message
            # Common patterns: "Field 'field_name'", "field_name:", etc.
            import re

            patterns = [
                r"Field ['\"]?(\w+)['\"]?",
                r"(\w+):",
                r"['\"](\w+)['\"]",
            ]
            for pattern in patterns:
                match = re.search(pattern, error)
                if match:
                    return match.group(1)

        return None

    def _extract_error_type(self, error: Any) -> Optional[str]:
        """Extract error type from validation error."""
        if isinstance(error, dict):
            return error.get("type", "unknown")
        elif isinstance(error, str):
            # Extract common error types
            error_lower = error.lower()
            if "missing" in error_lower or "required" in error_lower:
                return "missing"
            elif "type" in error_lower:
                return "type_error"
            elif "length" in error_lower:
                return "length_error"
            elif "pattern" in error_lower or "regex" in error_lower:
                return "pattern_error"
            elif "enum" in error_lower:
                return "enum_error"
            else:
                return "validation_error"

        return "unknown"

