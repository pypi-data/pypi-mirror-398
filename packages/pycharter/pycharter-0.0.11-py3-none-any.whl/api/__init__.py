"""
PyCharter API - FastAPI wrapper for PyCharter services.

This module provides REST API endpoints for all PyCharter core services:
- Contract parsing and building
- Metadata storage and retrieval
- Schema generation and conversion
- Runtime validation

To use the API:
1. Install with API dependencies: pip install pycharter[api]
2. Run the server: pycharter api
3. Access documentation: http://localhost:8000/docs
"""

__version__ = "0.0.3"

# Check if FastAPI is available
try:
    from api.main import app, create_application
    __all__ = ["app", "create_application"]
except (ImportError, ModuleNotFoundError):
    # FastAPI not installed or api module not available
    __all__ = []
