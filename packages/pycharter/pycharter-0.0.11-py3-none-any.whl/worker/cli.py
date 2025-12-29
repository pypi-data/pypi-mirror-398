"""
CLI commands for worker component.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

from pycharter.config import get_database_url

from worker.processor import ValidationProcessor

logger = logging.getLogger(__name__)


def cmd_worker_start(
    mode: str = "local",
    redis_url: str = "redis://localhost:6379",
    db_url: Optional[str] = None,
    spark_master: Optional[str] = None,
):
    """
    Start the validation processor service.

    Args:
        mode: Spark mode ("local", "remote", "cluster")
        redis_url: Redis connection URL
        db_url: Database connection URL (optional, uses config if not provided)
        spark_master: Spark master URL (optional, auto-detected)

    Returns:
        Exit code (0 for success)
    """
    # Check if Spark is available
    try:
        import pyspark  # noqa: F401
    except ImportError:
        print(
            "❌ Error: pyspark is required for worker.",
            file=sys.stderr,
        )
        print(
            "   Install with: pip install pycharter[worker]",
            file=sys.stderr,
        )
        return 1

    # Check if Redis is available
    try:
        import redis  # noqa: F401
    except ImportError:
        print(
            "❌ Error: redis is required for worker.",
            file=sys.stderr,
        )
        print(
            "   Install with: pip install pycharter[worker]",
            file=sys.stderr,
        )
        return 1

    # Get database URL from config if not provided
    if not db_url:
        db_url = get_database_url()
        if not db_url:
            # Default to SQLite
            db_url = "sqlite:///pycharter.db"
            print(
                f"ℹ️  No database URL configured, using default: {db_url}",
                file=sys.stderr,
            )

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create processor
    processor = ValidationProcessor(
        redis_url=redis_url,
        db_url=db_url,
        spark_mode=mode,
        spark_master=spark_master,
    )

    # Run processor
    try:
        asyncio.run(processor.start())
        return 0
    except KeyboardInterrupt:
        logger.info("Processor stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Processor error: {e}", exc_info=True)
        return 1

