"""
API v1 route handlers.

This module contains all FastAPI route handlers for API version 1.
All routers defined here are automatically included in the main application
with the `/api/v1` prefix.
"""

from api.routes.v1 import contracts, metadata, quality, schemas, validation

# Export all routers for automatic inclusion in main.py
__all__ = [
    "contracts",
    "metadata",
    "quality",
    "schemas",
    "validation",
]

