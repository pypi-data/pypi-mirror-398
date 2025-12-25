"""
Standalone UI server for PyCharter.

Serves the built Next.js static files and proxies API requests to the PyCharter API.
Supports both installed package (pre-built static files) and development mode.
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn


def find_ui_static_files() -> Optional[Path]:
    """
    Find UI static files in multiple locations (package, source, etc.).
    
    Priority:
    1. Installed package location (pycharter/ui/static/)
    2. Source location (ui/static/)
    3. Next.js out directory (ui/out/)
    
    Returns:
        Path to static directory if found, None otherwise
    """
    # Try to find static files in installed package
    try:
        import pycharter
        pycharter_path = Path(pycharter.__file__).parent.parent
        package_static = pycharter_path / "ui" / "static"
        if package_static.exists() and (package_static / "index.html").exists():
            return package_static
    except (ImportError, AttributeError):
        pass
    
    # Try source locations (development)
    possible_paths = [
        Path(__file__).parent / "static",  # ui/static/
        Path(__file__).parent.parent / "ui" / "static",  # project root/ui/static/
        Path.cwd() / "ui" / "static",  # Current directory
        Path(__file__).parent / "out",  # ui/out/ (Next.js export)
        Path(__file__).parent.parent / "ui" / "out",  # project root/ui/out/
    ]
    
    for static_path in possible_paths:
        if static_path.exists() and (static_path / "index.html").exists():
            return static_path
    
    return None


def get_static_dir() -> Path:
    """Get the directory containing built static files."""
    static_dir = find_ui_static_files()
    
    if static_dir:
        return static_dir
    
    # Provide helpful error message
    raise FileNotFoundError(
        "No built UI found.\n\n"
        "If you installed from pip:\n"
        "  The UI static files should be included in the package.\n"
        "  If they're missing, please report this issue.\n\n"
        "If you're in development:\n"
        "  1. Build the UI: pycharter ui build\n"
        "  2. Or run in dev mode: pycharter ui dev\n\n"
        "Expected locations:\n"
        "  - Installed package: <site-packages>/ui/static/\n"
        "  - Source: ui/static/ or ui/out/"
    )


def create_app(api_url: str) -> FastAPI:
    """Create FastAPI app for serving UI and proxying API requests."""
    app = FastAPI(title="PyCharter UI")
    
    static_dir = get_static_dir()
    
    # Mount static files
    _next_dir = static_dir / "_next"
    if _next_dir.exists():
        app.mount("/_next", StaticFiles(directory=str(_next_dir), html=False), name="next")
    
    # Proxy API requests
    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    async def proxy_api(request: Request, path: str):
        """Proxy API requests to the PyCharter API."""
        url = f"{api_url.rstrip('/')}/api/{path}"
        
        # Forward query parameters
        if request.url.query:
            url = f"{url}?{request.url.query}"
        
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Forward headers (excluding host and connection)
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("connection", None)
        headers.pop("content-length", None)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    content=body,
                    timeout=30.0,
                )
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type"),
                )
            except httpx.RequestError as e:
                return Response(
                    content=f"API request failed: {str(e)}",
                    status_code=502,
                    media_type="text/plain",
                )
    
    # Serve index.html for all other routes (SPA routing)
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve the SPA index.html for all non-API routes."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return Response(
                content="UI not built. Please run 'pycharter ui build' first.",
                status_code=404,
                media_type="text/plain",
            )
    
    return app


def serve_ui(
    api_url: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 3000,
) -> None:
    """
    Serve the PyCharter UI.
    
    Args:
        api_url: URL of the PyCharter API (defaults to http://localhost:8000)
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 3000)
    """
    # Get API URL from environment or argument
    if api_url is None:
        api_url = os.getenv("PYCHARTER_API_URL", "http://localhost:8000")
    
    # Validate that static files exist
    try:
        static_dir = get_static_dir()
        print(f"✓ Found UI static files at: {static_dir}")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create and run the app
    app = create_app(api_url)
    
    print(f"PyCharter UI server starting...")
    print(f"  UI: http://{host}:{port}")
    print(f"  API: {api_url}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PyCharter UI Server")
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="URL of the PyCharter API (default: http://localhost:8000 or PYCHARTER_API_URL env var)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind to (default: 3000)",
    )
    
    args = parser.parse_args()
    serve_ui(api_url=args.api_url, host=args.host, port=args.port)
