"""
PyCharter Worker - Async validation processing with Spark.

This optional component provides asynchronous validation processing using Spark.
It runs as a separate service that consumes validation jobs from a message queue
and processes them using Spark (local or cluster mode).

To use:
1. Install: pip install pycharter[worker]
2. Start worker: pycharter worker start
3. Submit jobs via API: POST /api/v1/validation/jobs
"""

__version__ = "0.0.1"

# Check if dependencies are available
try:
    import pyspark  # noqa: F401
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False

try:
    import redis  # noqa: F401
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

__all__ = ["SPARK_AVAILABLE", "REDIS_AVAILABLE"]

