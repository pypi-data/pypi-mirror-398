"""
Main validation processor service.

Consumes jobs from message queue and processes them using Spark backend.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from pycharter.metadata_store import (
    PostgresMetadataStore,
    SQLiteMetadataStore,
    MetadataStoreClient,
)
from pycharter.db.models.base import get_session
from sqlalchemy.orm import Session

from worker.backends.spark import SparkValidationBackend
from worker.queue.redis_queue import ValidationJobQueue

logger = logging.getLogger(__name__)


class ValidationProcessor:
    """
    Separate validation processor service.

    This runs as a separate process/service, truly offloading validation.
    It consumes jobs from the queue and processes them using Spark.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db_url: Optional[str] = None,
        spark_mode: str = "local",  # "local", "remote", "cluster"
        spark_master: Optional[str] = None,
    ):
        """
        Initialize validation processor.

        Args:
            redis_url: Redis connection URL
            db_url: Database connection URL (optional)
            spark_mode: Spark mode ("local", "remote", "cluster")
            spark_master: Spark master URL (optional, auto-detected)
        """
        self.queue = ValidationJobQueue(redis_url)
        self.db_url = db_url
        self.spark_backend = SparkValidationBackend(
            mode=spark_mode, master=spark_master
        )
        self.store = None
        self.db_session: Optional[Session] = None

    async def start(self):
        """Start the processor."""
        await self.queue.connect()

        # Initialize metadata store
        # Try to detect database type from db_url
        if self.db_url:
            if self.db_url.startswith("postgresql://") or self.db_url.startswith(
                "postgres://"
            ):
                self.store = PostgresMetadataStore()
            elif self.db_url.startswith("sqlite://"):
                self.store = SQLiteMetadataStore()
            else:
                # Default to Postgres
                self.store = PostgresMetadataStore()

            self.store.connect()

        # Initialize database session
        if self.db_url:
            self.db_session = get_session(self.db_url)

        logger.info("Validation processor started. Waiting for jobs...")

        # Start consuming jobs
        while True:
            try:
                # Blocking pop from queue
                job = await self.queue.dequeue_job(timeout=1)

                if job:
                    await self.process_job(job)

            except KeyboardInterrupt:
                logger.info("Shutting down processor...")
                break
            except Exception as e:
                logger.error(f"Error processing job: {e}", exc_info=True)
                await asyncio.sleep(1)

        # Cleanup
        await self.shutdown()

    async def process_job(self, job: Dict[str, Any]):
        """Process a single validation job."""
        job_id = job["job_id"]
        schema_id = job["schema_id"]
        data_source = job["data_source"]
        options = job.get("options", {})

        try:
            # Update status to processing
            await self.queue.update_job_status(job_id, "processing")

            logger.info(f"Processing job {job_id} for schema {schema_id}")

            # Ensure store is available
            if not self.store:
                raise ValueError(
                    "Metadata store not initialized. "
                    "Provide --db-url when starting the worker."
                )

            # Execute validation using Spark (run in executor since Spark is synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.spark_backend.validate,
                schema_id,
                data_source,
                self.store,
                options,
            )

            # Persist results to database
            if self.db_session:
                await self._persist_results(job_id, schema_id, result)

            # Update job status
            await self.queue.update_job_status(
                job_id,
                "completed",
                result=result,
            )

            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            await self.queue.update_job_status(
                job_id,
                "failed",
                error=str(e),
            )

    async def _persist_results(
        self,
        job_id: str,
        schema_id: str,
        result: Dict[str, Any],
    ):
        """Persist validation results to database."""
        from pycharter.db.models import QualityMetricModel
        import uuid

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._persist_results_sync,
            job_id,
            schema_id,
            result,
        )

    def _persist_results_sync(
        self,
        job_id: str,
        schema_id: str,
        result: Dict[str, Any],
    ):
        """Synchronous persistence (runs in executor)."""
        from pycharter.db.models import QualityMetricModel
        import uuid

        if not self.db_session:
            return

        try:
            metric = QualityMetricModel(
                id=uuid.uuid4(),
                schema_id=schema_id,
                overall_score=result["quality_score"] * 100,
                violation_rate=1.0 - result["quality_score"],
                completeness=1.0,  # Calculate from data if needed
                accuracy=result["quality_score"],
                record_count=result["total_count"],
                valid_count=result["valid_count"],
                invalid_count=result["invalid_count"],
                violation_count=len(result.get("violations", [])),
                data_source=result.get("data_source"),
            )

            self.db_session.add(metric)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Failed to persist results: {e}", exc_info=True)
            self.db_session.rollback()

    async def shutdown(self):
        """Shutdown processor and cleanup resources."""
        logger.info("Shutting down validation processor...")

        # Close Spark session
        self.spark_backend.close()

        # Disconnect from queue
        await self.queue.disconnect()

        # Close database session
        if self.db_session:
            self.db_session.close()

        # Disconnect from store
        if self.store:
            self.store.disconnect()

        logger.info("Validation processor shut down")

