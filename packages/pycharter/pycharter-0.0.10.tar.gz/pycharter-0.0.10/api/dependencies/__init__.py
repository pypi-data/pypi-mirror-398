"""
Dependencies for API routes.

This module provides FastAPI dependency injection for shared resources.
"""

from api.dependencies.store import get_metadata_store

__all__ = ["get_metadata_store"]
