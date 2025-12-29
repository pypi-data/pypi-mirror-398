"""
Route handlers for quality assurance.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
import json
import tempfile
from pathlib import Path

from pycharter.quality import (
    QualityCheck,
    QualityCheckOptions,
    QualityReport,
    QualityThresholds,
)
from api.dependencies.store import get_metadata_store
from api.dependencies.database import get_db_session
from api.models.quality import (
    FieldQualityMetricsResponse,
    QualityCheckRequest,
    QualityReportResponse,
    QualityScoreResponse,
    ViolationQueryRequest,
    ViolationRecordResponse,
    ViolationsResponse,
)
from pycharter.metadata_store import MetadataStoreClient

router = APIRouter()


@router.post(
    "/quality/check",
    response_model=QualityReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Run quality check",
    description="Run a quality check against a data contract. Supports both inline data and file uploads (JSON/CSV).",
    response_description="Quality check report",
)
async def quality_check(
    request: QualityCheckRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
    db: Session = Depends(get_db_session),
) -> QualityReportResponse:
    """
    Run a quality check against a data contract.

    This endpoint validates data against a contract and calculates quality metrics,
    optionally recording violations and checking thresholds.
    
    The system automatically prevents metric inflation by detecting duplicate datasets
    using data fingerprinting. If the same dataset is checked multiple times, only one
    metric entry is created/updated.

    Args:
        request: Quality check request
        store: Metadata store dependency
        db: Database session for persisting metrics

    Returns:
        Quality report with metrics and violations

    Raises:
        HTTPException: If quality check fails or required parameters are missing
    """
    # Validate request
    if not request.schema_id and not request.contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either schema_id or contract must be provided",
        )

    # Create quality check instance with database session for metric persistence
    quality_check_instance = QualityCheck(
        store=store if request.schema_id else None,
        db_session=db
    )

    # Build thresholds if provided
    thresholds = None
    if request.check_thresholds and request.thresholds:
        thresholds = QualityThresholds(**request.thresholds)

    # Build options
    options = QualityCheckOptions(
        record_violations=request.record_violations,
        calculate_metrics=request.calculate_metrics,
        check_thresholds=request.check_thresholds,
        thresholds=thresholds,
        include_field_metrics=request.include_field_metrics,
        sample_size=request.sample_size,
        data_source=request.data_source,
        data_version=request.data_version,
    )

    # Run quality check
    report = quality_check_instance.run(
        schema_id=request.schema_id,
        contract=request.contract,
        data=request.data,
        options=options,
    )

    # Convert to response model
    return _convert_report_to_response(report)


@router.post(
    "/quality/check/upload",
    response_model=QualityReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Run quality check with file upload",
    description="Run a quality check against a data contract using an uploaded file (JSON or CSV). The system automatically prevents metric inflation by detecting duplicate datasets.",
    response_description="Quality check report",
)
async def quality_check_upload(
    file: UploadFile = File(..., description="Data file (JSON or CSV)"),
    schema_id: Optional[str] = Form(None, description="Schema ID (for store-based validation)"),
    contract: Optional[str] = Form(None, description="Contract JSON string (for contract-based validation)"),
    record_violations: bool = Form(True, description="Record violations"),
    calculate_metrics: bool = Form(True, description="Calculate quality metrics"),
    check_thresholds: bool = Form(False, description="Check quality thresholds"),
    thresholds: Optional[str] = Form(None, description="Quality thresholds JSON string"),
    include_field_metrics: bool = Form(True, description="Include field-level metrics"),
    sample_size: Optional[int] = Form(None, description="Sample size for large datasets"),
    data_source: Optional[str] = Form(None, description="Data source identifier (e.g., file name)"),
    data_version: Optional[str] = Form(None, description="Data version identifier"),
    store: MetadataStoreClient = Depends(get_metadata_store),
    db: Session = Depends(get_db_session),
) -> QualityReportResponse:
    """
    Run a quality check with an uploaded file (JSON or CSV).

    This endpoint accepts a file upload and validates it against a contract,
    calculating quality metrics. The system automatically prevents metric inflation
    by detecting duplicate datasets using data fingerprinting.

    Args:
        file: Uploaded data file (JSON or CSV)
        schema_id: Schema ID (for store-based validation)
        contract: Contract JSON string (for contract-based validation)
        record_violations: Whether to record violations
        calculate_metrics: Whether to calculate quality metrics
        check_thresholds: Whether to check quality thresholds
        thresholds: Quality thresholds as JSON string
        include_field_metrics: Whether to include field-level metrics
        sample_size: Sample size for large datasets
        data_source: Data source identifier (defaults to file name)
        data_version: Data version identifier
        store: Metadata store dependency
        db: Database session for persisting metrics

    Returns:
        Quality report with metrics and violations

    Raises:
        HTTPException: If quality check fails or required parameters are missing
    """
    try:
        # Validate request
        if not schema_id and not contract:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either schema_id or contract must be provided",
            )

        # Parse contract if provided
        contract_dict = None
        if contract:
            try:
                contract_dict = json.loads(contract)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid contract JSON format",
                )

        # Parse thresholds if provided
        thresholds_dict = None
        if thresholds:
            try:
                thresholds_dict = json.loads(thresholds)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid thresholds JSON format",
                )

        # Save uploaded file temporarily
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.json', '.csv']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_extension}. Only JSON and CSV files are supported.",
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            # Read file content
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Create quality check instance with database session
            quality_check_instance = QualityCheck(
                store=store if schema_id else None,
                db_session=db
            )

            # Build thresholds if provided
            thresholds_obj = None
            if check_thresholds and thresholds_dict:
                thresholds_obj = QualityThresholds(**thresholds_dict)

            # Build options
            # Use file name as data_source if not provided
            data_source_value = data_source or file.filename

            options = QualityCheckOptions(
                record_violations=record_violations,
                calculate_metrics=calculate_metrics,
                check_thresholds=check_thresholds,
                thresholds=thresholds_obj,
                include_field_metrics=include_field_metrics,
                sample_size=sample_size,
                data_source=data_source_value,
                data_version=data_version,
            )

            # Run quality check with file path
            report = quality_check_instance.run(
                schema_id=schema_id,
                contract=contract_dict,
                data=tmp_file_path,
                options=options,
            )

            # Convert to response model
            return _convert_report_to_response(report)
        finally:
            # Clean up temporary file
            try:
                Path(tmp_file_path).unlink()
            except Exception:
                pass

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality check failed: {str(e)}",
        )


@router.post(
    "/quality/violations",
    response_model=ViolationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Query violations",
    description="Query data quality violations",
    response_description="List of violations",
)
async def query_violations(
    request: ViolationQueryRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ViolationsResponse:
    """
    Query data quality violations.

    Args:
        request: Violation query request
        store: Metadata store dependency

    Returns:
        List of violations matching the query

    Raises:
        HTTPException: If query fails
    """
    try:
        # Get violation tracker from quality check
        quality_check_instance = QualityCheck(store=store)
        tracker = quality_check_instance.violation_tracker

        # Query violations
        violations = tracker.get_violations(
            schema_id=request.schema_id,
            start_date=request.start_date,
            end_date=request.end_date,
            severity=request.severity,
            status=request.status,
        )

        # Get summary
        summary = tracker.get_violation_summary(schema_id=request.schema_id)

        # Convert to response models
        violation_responses = [
            ViolationRecordResponse(
                id=str(v.id),
                schema_id=v.schema_id,
                record_id=v.record_id,
                severity=v.severity,
                status=v.status,
                field_violations=v.field_violations,
                error_count=len(v.field_violations),
                timestamp=v.timestamp,
                resolved_at=v.resolved_at,
                resolved_by=v.resolved_by,
                metadata=v.metadata,
            )
            for v in violations
        ]

        return ViolationsResponse(
            violations=violation_responses,
            total=len(violation_responses),
            summary=summary,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query violations: {str(e)}",
        )


@router.get(
    "/quality/metrics",
    status_code=status.HTTP_200_OK,
    summary="List quality metrics",
    description="Retrieve quality metrics for different data feeds/schemas",
    response_description="List of quality metrics",
)
async def list_quality_metrics(
    schema_id: Optional[str] = Query(None, description="Filter by schema ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db_session),
) -> dict:
    """
    List quality metrics from the database.
    
    Returns quality metrics grouped by schema/data source, showing the latest
    quality check results for each data feed.
    
    Args:
        schema_id: Optional filter by schema ID
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        
    Returns:
        Dictionary with quality metrics list and total count
    """
    try:
        from pycharter.db.models.quality_metric import QualityMetricModel
        
        # Build query
        query = db.query(QualityMetricModel)
        
        if schema_id:
            query = query.filter(QualityMetricModel.schema_id == schema_id)
        
        # Get total count
        total = query.count()
        
        # Get latest metrics for each schema_id + data_source combination
        # Order by check_timestamp descending to get most recent first
        metrics = query.order_by(desc(QualityMetricModel.check_timestamp)).offset(offset).limit(limit).all()
        
        # Close session after use (session is managed by dependency)
        # Note: In production, you might want to use a session manager that handles cleanup
        
        # Convert to response format
        metrics_list = []
        for metric in metrics:
            metrics_list.append({
                "id": str(metric.id),
                "schema_id": metric.schema_id,
                "schema_version": metric.schema_version,
                "data_contract_id": str(metric.data_contract_id) if metric.data_contract_id else None,
                "overall_score": metric.overall_score,
                "violation_rate": metric.violation_rate,
                "completeness": metric.completeness,
                "accuracy": metric.accuracy,
                "record_count": metric.record_count,
                "valid_count": metric.valid_count,
                "invalid_count": metric.invalid_count,
                "violation_count": metric.violation_count,
                "field_scores": metric.field_scores,
                "threshold_breaches": metric.threshold_breaches,
                "passed": metric.passed == "true",
                "data_version": metric.data_version,
                "data_source": metric.data_source,
                "data_fingerprint": metric.data_fingerprint,
                "check_timestamp": metric.check_timestamp.isoformat() if metric.check_timestamp else None,
                "created_at": metric.created_at.isoformat() if metric.created_at else None,
                "updated_at": metric.updated_at.isoformat() if metric.updated_at else None,
            })
        
        return {
            "metrics": metrics_list,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quality metrics: {str(e)}",
        )


@router.get(
    "/quality/metrics/{metric_id}",
    status_code=status.HTTP_200_OK,
    summary="Get quality metric by ID",
    description="Retrieve a specific quality metric from the database by its ID",
    response_description="Quality metric details",
)
async def get_quality_metric(
    metric_id: str,
    db: Session = Depends(get_db_session),
) -> dict:
    """
    Get a specific quality metric from the database by ID.
    
    Args:
        metric_id: Quality metric ID (UUID)
        db: Database session
        
    Returns:
        Quality metric details
        
    Raises:
        HTTPException: If metric not found or database query fails
    """
    try:
        import uuid
        from pycharter.db.models.quality_metric import QualityMetricModel
        
        metric_uuid = uuid.UUID(metric_id)
        metric = db.query(QualityMetricModel).filter(
            QualityMetricModel.id == metric_uuid
        ).first()
        
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quality metric not found: {metric_id}",
            )
        
        return {
            "id": str(metric.id),
            "schema_id": metric.schema_id,
            "schema_version": metric.schema_version,
            "data_contract_id": str(metric.data_contract_id) if metric.data_contract_id else None,
            "overall_score": metric.overall_score,
            "violation_rate": metric.violation_rate,
            "completeness": metric.completeness,
            "accuracy": metric.accuracy,
            "record_count": metric.record_count,
            "valid_count": metric.valid_count,
            "invalid_count": metric.invalid_count,
            "violation_count": metric.violation_count,
            "field_scores": metric.field_scores,
            "threshold_breaches": metric.threshold_breaches,
            "passed": metric.passed == "true",
            "data_version": metric.data_version,
            "data_source": metric.data_source,
            "data_fingerprint": metric.data_fingerprint,
            "check_timestamp": metric.check_timestamp.isoformat() if metric.check_timestamp else None,
            "created_at": metric.created_at.isoformat() if metric.created_at else None,
            "updated_at": metric.updated_at.isoformat() if metric.updated_at else None,
            "additional_metadata": metric.additional_metadata,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metric ID format: {metric_id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality metric: {str(e)}",
        )


@router.get(
    "/quality/reports/{schema_id}",
    status_code=status.HTTP_200_OK,
    summary="Get quality report for schema",
    description="Retrieve the latest quality report for a specific schema/data feed",
    response_description="Quality report with metrics",
)
async def get_quality_report(
    schema_id: str,
    data_source: Optional[str] = Query(None, description="Filter by data source"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of reports to return"),
    db: Session = Depends(get_db_session),
) -> dict:
    """
    Get quality reports for a specific schema.
    
    Returns the latest quality metrics for a schema, optionally filtered by data source.
    This provides a comprehensive quality report for a data feed.
    
    Args:
        schema_id: Schema identifier
        data_source: Optional filter by data source
        limit: Maximum number of reports to return (default: 10, most recent)
        db: Database session
        
    Returns:
        Dictionary with quality reports list and summary
    """
    try:
        from pycharter.db.models.quality_metric import QualityMetricModel
        from sqlalchemy import desc
        
        # Build query
        query = db.query(QualityMetricModel).filter(
            QualityMetricModel.schema_id == schema_id
        )
        
        if data_source:
            query = query.filter(QualityMetricModel.data_source == data_source)
        
        # Get latest reports ordered by check_timestamp
        reports = query.order_by(desc(QualityMetricModel.check_timestamp)).limit(limit).all()
        
        if not reports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No quality reports found for schema: {schema_id}",
            )
        
        # Convert to response format
        reports_list = []
        for metric in reports:
            reports_list.append({
                "id": str(metric.id),
                "schema_id": metric.schema_id,
                "schema_version": metric.schema_version,
                "data_contract_id": str(metric.data_contract_id) if metric.data_contract_id else None,
                "overall_score": metric.overall_score,
                "violation_rate": metric.violation_rate,
                "completeness": metric.completeness,
                "accuracy": metric.accuracy,
                "record_count": metric.record_count,
                "valid_count": metric.valid_count,
                "invalid_count": metric.invalid_count,
                "violation_count": metric.violation_count,
                "field_scores": metric.field_scores,
                "threshold_breaches": metric.threshold_breaches,
                "passed": metric.passed == "true",
                "data_version": metric.data_version,
                "data_source": metric.data_source,
                "data_fingerprint": metric.data_fingerprint,
                "check_timestamp": metric.check_timestamp.isoformat() if metric.check_timestamp else None,
                "created_at": metric.created_at.isoformat() if metric.created_at else None,
                "updated_at": metric.updated_at.isoformat() if metric.updated_at else None,
                "additional_metadata": metric.additional_metadata,
            })
        
        # Calculate summary statistics
        latest_report = reports_list[0] if reports_list else None
        avg_score = sum(r["overall_score"] for r in reports_list) / len(reports_list) if reports_list else 0
        
        return {
            "schema_id": schema_id,
            "data_source": data_source,
            "reports": reports_list,
            "count": len(reports_list),
            "summary": {
                "latest_score": latest_report["overall_score"] if latest_report else None,
                "average_score": round(avg_score, 2),
                "latest_check": latest_report["check_timestamp"] if latest_report else None,
                "latest_status": "passed" if latest_report and latest_report["passed"] else "failed" if latest_report else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality report: {str(e)}",
        )


def _convert_report_to_response(report: QualityReport) -> QualityReportResponse:
    """Convert QualityReport to API response model."""
    quality_score_response = None
    if report.quality_score:
        quality_score_response = QualityScoreResponse(
            overall_score=report.quality_score.overall_score,
            violation_rate=report.quality_score.violation_rate,
            completeness=report.quality_score.completeness,
            accuracy=report.quality_score.accuracy,
            field_scores=report.quality_score.field_scores,
            record_count=report.quality_score.record_count,
            valid_count=report.quality_score.valid_count,
            invalid_count=report.quality_score.invalid_count,
        )

    field_metrics_response = {}
    for field_name, metrics in report.field_metrics.items():
        field_metrics_response[field_name] = FieldQualityMetricsResponse(
            field_name=metrics.field_name,
            null_count=metrics.null_count,
            violation_count=metrics.violation_count,
            total_count=metrics.total_count,
            violation_rate=metrics.violation_rate,
            completeness=metrics.completeness,
            error_types=metrics.error_types,
        )

    return QualityReportResponse(
        schema_id=report.schema_id,
        schema_version=report.schema_version,
        check_timestamp=report.check_timestamp,
        quality_score=quality_score_response,
        field_metrics=field_metrics_response,
        violation_count=report.violation_count,
        record_count=report.record_count,
        valid_count=report.valid_count,
        invalid_count=report.invalid_count,
        threshold_breaches=report.threshold_breaches,
        passed=report.passed,
        metadata=report.metadata,
    )

