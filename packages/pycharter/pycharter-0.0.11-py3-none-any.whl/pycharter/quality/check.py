"""
Core quality check functionality.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING

from pycharter.metadata_store import MetadataStoreClient
from pycharter.runtime_validator.wrappers import (
    validate_batch_with_contract,
    validate_batch_with_store,
)

from pycharter.quality.metrics import QualityMetrics
from pycharter.quality.models import (
    QualityCheckOptions,
    QualityReport,
    QualityThresholds,
)
from pycharter.quality.profiling import DataProfiler
from pycharter.quality.violations import ViolationTracker

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class QualityCheck:
    """
    Core quality check functionality - orchestrator-agnostic.

    This class can be used:
    - Standalone (CLI, API, Python scripts)
    - Within orchestrators (Airflow, Prefect, Dagster)
    - Via API calls
    """

    def __init__(
        self,
        store: Optional[MetadataStoreClient] = None,
        db_session: Optional["Session"] = None,
    ):
        """
        Initialize quality check.

        Args:
            store: Optional metadata store for retrieving contracts and storing violations
            db_session: Optional SQLAlchemy database session for persisting metrics and violations
        """
        self.store = store
        self.db_session = db_session
        self.metrics = QualityMetrics()
        self.violation_tracker = ViolationTracker(store=store, db_session=db_session)
        self.profiler = DataProfiler()

    def run(
        self,
        schema_id: Optional[str] = None,
        contract: Optional[Union[Dict[str, Any], str]] = None,
        data: Union[List[Dict[str, Any]], str, Callable] = None,
        options: Optional[QualityCheckOptions] = None,
    ) -> QualityReport:
        """
        Run a quality check against a data contract.

        Args:
            schema_id: Schema ID (if using store-based validation)
            contract: Contract dictionary or file path (if using contract-based validation)
            data: Data to validate. Can be:
                - List of dictionaries
                - File path (JSON, CSV, etc.)
                - Callable that returns data
            options: Quality check options

        Returns:
            QualityReport with results

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if options is None:
            options = QualityCheckOptions()

        # Load data
        data_list = self._load_data(data)
        
        # Calculate data fingerprint for deduplication
        data_fingerprint = self._calculate_data_fingerprint(data_list)
        data_source = options.data_source or self._get_data_source(data)

        # Apply sampling if requested
        if options.sample_size and options.sample_size < len(data_list):
            import random

            data_list = random.sample(data_list, options.sample_size)
        
        # Check if data has changed (if skip_if_unchanged is enabled)
        if options.skip_if_unchanged and self.db_session and data_fingerprint:
            existing_metric = self._get_existing_metric(
                schema_id=schema_id,
                data_fingerprint=data_fingerprint,
                data_version=options.data_version
            )
            if existing_metric:
                # Data hasn't changed, return cached result
                import logging
                logging.info(f"Skipping quality check - data unchanged (fingerprint: {data_fingerprint[:16]}...)")
                # Return a report based on existing metric (would need to reconstruct from DB)
                # For now, we'll still run the check but won't create duplicate metrics
                pass

        # Profile data (optional, for understanding data characteristics)
        profile_data = None
        if options.include_profiling:
            profile_data = self.profiler.profile(data_list)

        # Validate data
        validation_results = self._validate_data(
            schema_id=schema_id, contract=contract, data_list=data_list
        )

        # Calculate metrics
        quality_score = None
        field_metrics = {}
        if options.calculate_metrics:
            quality_score = self.metrics.calculate_quality_score(validation_results)
            if options.include_field_metrics:
                field_metrics = self.metrics.calculate_field_metrics(validation_results)

        # Record violations
        violation_count = 0
        if options.record_violations:
            violation_count = self._record_violations(
                schema_id=schema_id,
                contract=contract,
                data_list=data_list,
                validation_results=validation_results,
                options=options,
            )

        # Check thresholds
        threshold_breaches = []
        if options.check_thresholds and options.thresholds and quality_score:
            threshold_breaches = options.thresholds.check(quality_score)

        # Build report
        valid_count = sum(1 for r in validation_results if r.is_valid)
        invalid_count = len(validation_results) - valid_count

        # Get schema version if available
        schema_version = None
        if schema_id and self.store:
            try:
                full_schema = self.store.get_complete_schema(schema_id)
                schema_version = full_schema.get("version") if full_schema else None
            except Exception:
                pass

        report_metadata = {
            "sample_size": options.sample_size,
            "contract_based": contract is not None,
            "data_fingerprint": data_fingerprint,
            "data_source": data_source,
        }
        if options.data_version:
            report_metadata["data_version"] = options.data_version
        if profile_data:
            report_metadata["profiling"] = profile_data
        if options.metadata:
            report_metadata.update(options.metadata)

        report = QualityReport(
            schema_id=schema_id or "unknown",
            schema_version=schema_version,
            quality_score=quality_score,
            field_metrics=field_metrics,
            violation_count=violation_count,
            record_count=len(data_list),
            valid_count=valid_count,
            invalid_count=invalid_count,
            threshold_breaches=threshold_breaches,
            metadata=report_metadata,
        )

        # Persist quality metrics to database if session is available
        if self.db_session and quality_score:
            self._persist_quality_metrics(
                report, 
                schema_id, 
                schema_version,
                data_fingerprint=data_fingerprint,
                data_version=options.data_version,
                data_source=data_source,
                skip_if_unchanged=options.skip_if_unchanged
            )

        return report

    def _load_data(
        self, data: Union[List[Dict[str, Any]], str, Callable]
    ) -> List[Dict[str, Any]]:
        """
        Load data from various sources.

        Args:
            data: Data source (list, file path, or callable)

        Returns:
            List of data dictionaries
        """
        if data is None:
            raise ValueError("Data source is required")

        # If it's already a list, return it
        if isinstance(data, list):
            return data

        # If it's a callable, call it
        if callable(data):
            result = data()
            if isinstance(result, list):
                return result
            else:
                raise ValueError("Callable must return a list of dictionaries")

        # If it's a string, treat as file path
        if isinstance(data, str):
            file_path = Path(data)
            if not file_path.exists():
                raise FileNotFoundError(f"Data file not found: {data}")

            # Load based on file extension
            if file_path.suffix == ".json":
                with open(file_path, "r") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        return loaded
                    elif isinstance(loaded, dict):
                        return [loaded]
                    else:
                        raise ValueError("JSON file must contain a list or dict")
            elif file_path.suffix == ".csv":
                import pandas as pd

                df = pd.read_csv(file_path)
                return df.to_dict("records")
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        raise ValueError(f"Unsupported data type: {type(data)}")

    def _calculate_data_fingerprint(self, data_list: List[Dict[str, Any]]) -> str:
        """
        Calculate a fingerprint (hash) of the data for deduplication.
        
        Args:
            data_list: List of data records
            
        Returns:
            MD5 hash string of the data
        """
        if not data_list:
            return ""
        
        # Create a stable representation of the data
        # Sort by a stable key if available, otherwise use first few records
        try:
            # Try to create a stable hash by sorting records
            if isinstance(data_list[0], dict):
                # Use first record's keys as sort key
                sample_keys = list(data_list[0].keys())[:5]  # Use first 5 keys
                sorted_data = sorted(
                    data_list,
                    key=lambda x: tuple(str(x.get(k, "")) for k in sample_keys)
                )
            else:
                sorted_data = sorted(data_list)
            
            # Create hash from sorted data
            data_str = json.dumps(sorted_data, sort_keys=True, default=str)
        except Exception:
            # Fallback: hash unsorted data
            data_str = json.dumps(data_list, sort_keys=True, default=str)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_data_source(self, data: Union[List[Dict[str, Any]], str, Callable]) -> Optional[str]:
        """
        Get data source identifier.
        
        Args:
            data: Data source
            
        Returns:
            Source identifier string or None
        """
        if isinstance(data, str):
            # File path
            return str(data)
        elif isinstance(data, list):
            return "in-memory"
        elif callable(data):
            return f"callable:{data.__name__ if hasattr(data, '__name__') else 'unknown'}"
        return None
    
    def _get_existing_metric(
        self,
        schema_id: Optional[str],
        data_fingerprint: Optional[str],
        data_version: Optional[str] = None
    ) -> Optional[Any]:
        """
        Check if a quality metric already exists for this data.
        
        Args:
            schema_id: Schema ID
            data_fingerprint: Data fingerprint
            data_version: Optional data version
            
        Returns:
            Existing QualityMetricModel or None
        """
        if not self.db_session or not data_fingerprint:
            return None
        
        try:
            from pycharter.db.models.quality_metric import QualityMetricModel
            from sqlalchemy import and_
            
            filters = [
                QualityMetricModel.schema_id == (schema_id or "unknown"),
                QualityMetricModel.data_fingerprint == data_fingerprint
            ]
            
            if data_version:
                filters.append(QualityMetricModel.data_version == data_version)
            
            existing = self.db_session.query(QualityMetricModel).filter(
                and_(*filters)
            ).order_by(QualityMetricModel.check_timestamp.desc()).first()
            
            return existing
        except Exception:
            return None

    def _validate_data(
        self,
        schema_id: Optional[str],
        contract: Optional[Union[Dict[str, Any], str]],
        data_list: List[Dict[str, Any]],
    ) -> List:
        """
        Validate data against contract.

        Args:
            schema_id: Schema ID (for store-based validation)
            contract: Contract (for contract-based validation)
            data_list: List of data records

        Returns:
            List of ValidationResult objects
        """
        if schema_id:
            if not self.store:
                raise ValueError("Store is required for schema_id-based validation")
            return validate_batch_with_store(
                store=self.store, schema_id=schema_id, data_list=data_list
            )
        elif contract:
            return validate_batch_with_contract(contract=contract, data_list=data_list)
        else:
            raise ValueError("Either schema_id or contract must be provided")

    def _record_violations(
        self,
        schema_id: Optional[str],
        contract: Optional[Union[Dict[str, Any], str]],
        data_list: List[Dict[str, Any]],
        validation_results: List,
        options: Optional[QualityCheckOptions] = None,
    ) -> int:
        """
        Record violations for invalid records.

        Args:
            schema_id: Schema ID
            contract: Contract
            data_list: List of data records
            validation_results: List of ValidationResult objects
            options: Quality check options (for deduplicate_violations setting)

        Returns:
            Number of violations recorded
        """
        violation_count = 0
        schema_id_str = schema_id or "unknown"

        for i, (record_data, result) in enumerate(zip(data_list, validation_results)):
            if not result.is_valid:
                # Generate record ID (use index if no natural ID exists)
                record_id = None
                if isinstance(record_data, dict):
                    # Try to find an ID field
                    for id_field in ["id", "_id", "record_id", "uuid"]:
                        if id_field in record_data:
                            record_id = str(record_data[id_field])
                            break

                if record_id is None:
                    record_id = f"record_{i}"

                # Determine severity based on error count
                error_count = len(result.errors) if result.errors else 1
                if error_count > 5:
                    severity = "critical"
                elif error_count > 2:
                    severity = "warning"
                else:
                    severity = "info"

                self.violation_tracker.record_violation(
                    schema_id=schema_id_str,
                    record_id=record_id,
                    record_data=record_data,
                    validation_result=result,
                    severity=severity,
                    metadata={"record_index": i},
                    deduplicate=options.deduplicate_violations if options else True,
                )
                violation_count += 1

        return violation_count

    def _persist_quality_metrics(
        self,
        report: QualityReport,
        schema_id: Optional[str],
        schema_version: Optional[str],
        data_fingerprint: Optional[str] = None,
        data_version: Optional[str] = None,
        data_source: Optional[str] = None,
        skip_if_unchanged: bool = False,
    ):
        """
        Persist quality metrics to database with version tracking and deduplication.
        
        Args:
            report: Quality report
            schema_id: Schema ID
            schema_version: Schema version
            data_fingerprint: Data fingerprint for deduplication
            data_version: Data version identifier
            data_source: Data source identifier
            skip_if_unchanged: If True, skip persisting if data hasn't changed
        """
        if not self.db_session or not report.quality_score:
            return

        try:
            from pycharter.db.models.quality_metric import QualityMetricModel
            from sqlalchemy import and_

            # Always check for existing metrics with the same fingerprint to prevent metric inflation
            # This ensures that running quality checks on the same dataset doesn't create duplicate metrics
            if data_fingerprint:
                existing = self._get_existing_metric(
                    schema_id=schema_id,
                    data_fingerprint=data_fingerprint,
                    data_version=data_version
                )
                if existing:
                    # Data hasn't changed - update timestamp but don't create duplicate
                    # This prevents metric inflation from accidentally running checks on the same dataset
                    import logging
                    existing.check_timestamp = datetime.utcnow()
                    self.db_session.commit()
                    logging.info(
                        f"Skipping duplicate quality metric - data unchanged "
                        f"(fingerprint: {data_fingerprint[:16]}..., schema_id: {schema_id})"
                    )
                    return

            # Try to find data_contract_id from schema_id
            data_contract_id = None
            if schema_id and self.store:
                try:
                    # Try to get contract info from store
                    # This is a simplified approach - you may need to adjust based on your store implementation
                    pass
                except Exception:
                    pass

            quality_metric = QualityMetricModel(
                schema_id=schema_id or "unknown",
                schema_version=schema_version,
                data_contract_id=data_contract_id,
                overall_score=report.quality_score.overall_score,
                violation_rate=report.quality_score.violation_rate,
                completeness=report.quality_score.completeness,
                accuracy=report.quality_score.accuracy,
                record_count=report.record_count,
                valid_count=report.valid_count,
                invalid_count=report.invalid_count,
                violation_count=report.violation_count,
                field_scores=report.quality_score.field_scores,
                threshold_breaches=report.threshold_breaches,
                passed="true" if report.passed else "false",
                data_version=data_version,
                data_source=data_source,
                data_fingerprint=data_fingerprint,
                additional_metadata=report.metadata,
            )

            self.db_session.add(quality_metric)
            self.db_session.commit()
        except Exception as e:
            # Rollback on error and log (but don't fail the quality check)
            if self.db_session:
                self.db_session.rollback()
            # Log error but continue
            import logging
            logging.warning(f"Failed to persist quality metrics to database: {e}")

