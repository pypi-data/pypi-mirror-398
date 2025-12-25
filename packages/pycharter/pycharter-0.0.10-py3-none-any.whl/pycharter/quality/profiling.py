"""
Data profiling capabilities for quality assurance.

Provides statistical analysis of data to understand data characteristics,
distributions, and patterns.
"""

import json
from typing import Any, Dict, List, Optional
from collections import Counter
import statistics


class DataProfiler:
    """Profile data to understand its characteristics and quality."""

    def profile(
        self, data: List[Dict[str, Any]], fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Profile a dataset to understand its characteristics.

        Args:
            data: List of data records (dictionaries)
            fields: Optional list of field names to profile (if None, profiles all fields)

        Returns:
            Dictionary with profiling results including:
            - record_count: Total number of records
            - field_profiles: Per-field statistics
            - overall_stats: Overall dataset statistics
        """
        if not data:
            return {
                "record_count": 0,
                "field_profiles": {},
                "overall_stats": {},
            }

        # Determine fields to profile
        if fields is None:
            # Get all unique field names from all records
            fields = set()
            for record in data:
                fields.update(record.keys())
            fields = sorted(list(fields))

        field_profiles = {}
        for field in fields:
            field_profiles[field] = self._profile_field(data, field)

        overall_stats = self._calculate_overall_stats(data, field_profiles)

        return {
            "record_count": len(data),
            "field_profiles": field_profiles,
            "overall_stats": overall_stats,
        }

    def _profile_field(
        self, data: List[Dict[str, Any]], field_name: str
    ) -> Dict[str, Any]:
        """Profile a single field."""
        values = [record.get(field_name) for record in data]

        # Count nulls
        null_count = sum(1 for v in values if v is None)
        non_null_count = len(values) - null_count
        null_percentage = (null_count / len(values)) * 100 if values else 0

        # Filter out None values for statistics
        non_null_values = [v for v in values if v is not None]

        profile = {
            "field_name": field_name,
            "null_count": null_count,
            "non_null_count": non_null_count,
            "null_percentage": null_percentage,
            "completeness": 1.0 - (null_count / len(values)) if values else 0.0,
        }

        if not non_null_values:
            profile["type"] = "empty"
            return profile

        # Determine data type
        sample_value = non_null_values[0]
        value_type = type(sample_value).__name__

        profile["type"] = value_type
        
        # Calculate unique count - handle unhashable types (lists, dicts)
        # Check type first to avoid exception handling overhead
        if value_type in ["list", "dict"]:
            # For lists and dicts, count unique by converting to JSON string
            try:
                unique_strings = set(
                    json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else str(v)
                    for v in non_null_values
                )
                unique_count = len(unique_strings)
            except (TypeError, ValueError):
                # Fallback: just use length (all considered unique if can't compare)
                unique_count = len(non_null_values)
        else:
            # For hashable types, try direct set creation
            try:
                unique_values = set(non_null_values)
                unique_count = len(unique_values)
            except TypeError:
                # For other unhashable types, use string representation
                unique_strings = set(str(v) for v in non_null_values)
                unique_count = len(unique_strings)
        
        profile["unique_count"] = unique_count
        profile["unique_percentage"] = (unique_count / len(non_null_values)) * 100 if non_null_values else 0

        # Type-specific statistics
        if value_type in ["int", "float"]:
            profile.update(self._profile_numeric(non_null_values))
        elif value_type == "str":
            profile.update(self._profile_string(non_null_values))
        elif value_type == "bool":
            profile.update(self._profile_boolean(non_null_values))
        elif value_type == "list":
            profile.update(self._profile_list(non_null_values))
        elif value_type == "dict":
            profile.update(self._profile_dict(non_null_values))

        # Most common values - handle unhashable types
        if len(non_null_values) > 0:
            try:
                value_counts = Counter(non_null_values)
                profile["most_common"] = [
                    {"value": str(val), "count": count, "percentage": (count / len(non_null_values)) * 100}
                    for val, count in value_counts.most_common(5)
                ]
            except TypeError:
                # For unhashable types, convert to string representation
                try:
                    # Convert unhashable values to JSON strings for counting
                    string_values = [
                        json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else str(v)
                        for v in non_null_values
                    ]
                    value_counts = Counter(string_values)
                    profile["most_common"] = [
                        {"value": val, "count": count, "percentage": (count / len(non_null_values)) * 100}
                        for val, count in value_counts.most_common(5)
                    ]
                except (TypeError, ValueError):
                    # If still can't hash, skip most_common
                    profile["most_common"] = []

        return profile

    def _profile_numeric(self, values: List[Any]) -> Dict[str, Any]:
        """Profile numeric values."""
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                continue

        if not numeric_values:
            return {}

        return {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": statistics.mean(numeric_values),
            "median": statistics.median(numeric_values),
            "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0.0,
            "variance": statistics.variance(numeric_values) if len(numeric_values) > 1 else 0.0,
        }

    def _profile_string(self, values: List[Any]) -> Dict[str, Any]:
        """Profile string values."""
        string_values = [str(v) for v in values]

        lengths = [len(s) for s in string_values]
        if not lengths:
            return {}

        return {
            "min_length": min(lengths),
            "max_length": max(lengths),
            "mean_length": statistics.mean(lengths),
            "median_length": statistics.median(lengths),
            "empty_count": sum(1 for s in string_values if not s.strip()),
        }

    def _profile_boolean(self, values: List[Any]) -> Dict[str, Any]:
        """Profile boolean values."""
        bool_values = [bool(v) for v in values]
        true_count = sum(1 for v in bool_values if v)
        false_count = len(bool_values) - true_count

        return {
            "true_count": true_count,
            "false_count": false_count,
            "true_percentage": (true_count / len(bool_values)) * 100 if bool_values else 0,
            "false_percentage": (false_count / len(bool_values)) * 100 if bool_values else 0,
        }

    def _profile_list(self, values: List[Any]) -> Dict[str, Any]:
        """Profile list values."""
        lengths = [len(v) if isinstance(v, list) else 0 for v in values]
        if not lengths:
            return {}

        return {
            "min_length": min(lengths),
            "max_length": max(lengths),
            "mean_length": statistics.mean(lengths),
            "median_length": statistics.median(lengths),
            "empty_count": sum(1 for l in lengths if l == 0),
        }

    def _profile_dict(self, values: List[Any]) -> Dict[str, Any]:
        """Profile dict values."""
        if not values:
            return {}

        # Get all keys across all dicts
        all_keys = set()
        for v in values:
            if isinstance(v, dict):
                all_keys.update(v.keys())

        return {
            "unique_keys": sorted(list(all_keys)),
            "key_count": len(all_keys),
        }

    def _calculate_overall_stats(
        self, data: List[Dict[str, Any]], field_profiles: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall dataset statistics."""
        if not data:
            return {}

        # Calculate average completeness across all fields
        completeness_scores = [
            profile.get("completeness", 0.0)
            for profile in field_profiles.values()
        ]
        avg_completeness = (
            statistics.mean(completeness_scores) if completeness_scores else 0.0
        )

        # Count fields with high null rates
        high_null_fields = [
            field
            for field, profile in field_profiles.items()
            if profile.get("null_percentage", 0) > 50
        ]

        return {
            "average_completeness": avg_completeness,
            "fields_with_high_null_rate": high_null_fields,
            "total_fields": len(field_profiles),
        }

