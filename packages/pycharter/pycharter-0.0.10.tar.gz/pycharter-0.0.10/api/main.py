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
