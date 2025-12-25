"""
Integration modules for streaming frameworks and data sources.

This package provides integrations with various streaming frameworks
and data sources to enable validation of data in motion.
"""

try:
    from pycharter.integrations.kafka import KafkaValidator
except ImportError:
    KafkaValidator = None  # type: ignore[assignment,misc]

from pycharter.integrations.streaming import StreamValidator

__all__ = [
    "StreamValidator",
    "KafkaValidator",
]

