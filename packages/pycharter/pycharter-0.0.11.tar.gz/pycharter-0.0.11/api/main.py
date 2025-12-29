"""
FastAPI application entry point for PyCharter API.

This module sets up the FastAPI application with all routes, middleware, and dependencies.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from pycharter import __version__ as pycharter_version

# Import routers from v1
from api.routes.v1 import contracts, metadata, quality, schemas, validation

# Try to import validation_jobs router (requires worker component)
try:
    from api.routes.v1 import validation_jobs
    VALIDATION_JOBS_AVAILABLE = True
except ImportError:
    VALIDATION_JOBS_AVAILABLE = False

# API version
API_VERSION = "v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events.
    """
    # Startup: Initialize resources if needed
    yield
    # Shutdown: Cleanup resources if needed


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="PyCharter API",
        description="REST API for PyCharter data contract management and validation",
        version=pycharter_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers from v1 with automatic /api/v1 prefix
    # All routers in routes/v1/ are automatically included with the /api/v1 prefix
    app.include_router(
        contracts.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Contracts"],
    )
    app.include_router(
        metadata.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Metadata"],
    )
    app.include_router(
        schemas.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Schemas"],
    )
    app.include_router(
        validation.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Validation"],
    )
    app.include_router(
        quality.router,
        prefix=f"/api/{API_VERSION}",
        tags=["Quality"],
    )

    # Include validation_jobs router if worker component is available
    if VALIDATION_JOBS_AVAILABLE:
        app.include_router(
            validation_jobs.router,
            prefix=f"/api/{API_VERSION}",
            tags=["Validation Jobs"],
        )
    
    # Root endpoint
    @app.get(
        "/",
        summary="API Information",
        description="Get API information and version",
        tags=["General"],
    )
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": "PyCharter API",
            "version": pycharter_version,
            "api_version": API_VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
        }
    
    # Health check endpoint
    @app.get(
        "/health",
        summary="Health Check",
        description="Check API health status",
        tags=["General"],
    )
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy", "version": pycharter_version}
    
    # Request validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
            },
        )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler for unhandled errors."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )
    
    # Override openapi() method to handle schema generation errors gracefully
    # This is a workaround for a Pydantic v2 issue with unhashable types in schema generation
    original_openapi = app.openapi
    
    def openapi_with_error_handling():
        """OpenAPI schema with error handling for unhashable types."""
        try:
            return original_openapi()
        except TypeError as e:
            if "unhashable type" in str(e):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"OpenAPI schema generation encountered an issue: {e}. "
                    "Returning minimal schema."
                )
                # Return a minimal valid OpenAPI schema as fallback
                return {
                    "openapi": "3.1.0",
                    "info": {
                        "title": app.title,
                        "version": app.version,
                        "description": app.description,
                    },
                    "paths": {},
                    "components": {"schemas": {}},
                }
            raise
    
    app.openapi = openapi_with_error_handling
    
    return app


# Create application instance
app = create_application()


def main():
    """Main entry point for running the API server."""
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
    )


if __name__ == "__main__":
    main()
