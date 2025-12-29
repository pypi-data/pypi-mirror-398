"""
Route handlers for async validation job submission.

These endpoints allow clients to submit validation jobs for asynchronous
processing by the worker component.
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from worker.queue.redis_queue import ValidationJobQueue

from api.dependencies.store import get_metadata_store
from pycharter.metadata_store import MetadataStoreClient

# Try to import worker components
try:
    from worker.queue.redis_queue import ValidationJobQueue
    WORKER_AVAILABLE = True
except ImportError:
    WORKER_AVAILABLE = False
    ValidationJobQueue = None

logger = logging.getLogger(__name__)

router = APIRouter()

# Define models locally to avoid import issues when worker is not installed
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

# Global queue instance (initialized on startup)
_job_queue: Optional[Any] = None


async def get_job_queue() -> Any:
    """
    Get job queue instance.

    Returns:
        ValidationJobQueue instance

    Raises:
        HTTPException: If worker component is not installed
    """
    if not WORKER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Worker component not installed. "
                "Install with: pip install pycharter[worker]"
            ),
        )

    global _job_queue
    if _job_queue is None:
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _job_queue = ValidationJobQueue(redis_url=redis_url)
        await _job_queue.connect()

    return _job_queue


@router.post(
    "/validation/jobs",
    response_model=ValidationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit async validation job",
    description=(
        "Submit a validation job for asynchronous processing. "
        "Returns immediately with job_id for status polling."
    ),
    response_description="Job submission response with job_id",
)
async def submit_validation_job(
    request: ValidationJobRequest,
    queue: Any = Depends(get_job_queue),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ValidationJobResponse:
    """
    Submit an async validation job.

    This endpoint returns immediately with a job_id. The actual validation
    is processed asynchronously by a separate validation worker service.

    Args:
        request: Validation job request with schema_id, data_source, and options
        queue: Job queue dependency
        store: Metadata store dependency (for validation)

    Returns:
        Job submission response with job_id

    Raises:
        HTTPException: If worker is not available or job submission fails
    """
    from datetime import datetime

    # Verify schema exists in store
    schema = store.get_schema(request.schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {request.schema_id}",
        )

    # Enqueue job
    job = {
        "schema_id": request.schema_id,
        "data_source": request.data_source,
        "options": request.options or {},
    }

    try:
        job_id = await queue.enqueue_job(job)

        return ValidationJobResponse(
            job_id=job_id,
            status="queued",
            message=(
                "Validation job submitted successfully. "
                "Use job_id to check status."
            ),
            created_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}",
        )


@router.get(
    "/validation/jobs/{job_id}",
    response_model=ValidationJobStatus,
    status_code=status.HTTP_200_OK,
    summary="Get validation job status",
    description="Get the status and results of a validation job.",
    response_description="Job status and results",
)
async def get_validation_job_status(
    job_id: str,
    queue: Any = Depends(get_job_queue),
) -> ValidationJobStatus:
    """
    Get validation job status.

    Args:
        job_id: Job identifier
        queue: Job queue dependency

    Returns:
        Job status with results if available

    Raises:
        HTTPException: If job not found or worker not available
    """
    status_data = await queue.get_job_status(job_id)

    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return ValidationJobStatus(
        job_id=job_id,
        **status_data,
    )

