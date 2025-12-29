"""
Development server wrapper for PyCharter UI.

Runs Next.js dev server with API proxying configured.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_ui_root() -> Path:
    """Get the root directory of the UI module."""
    return Path(__file__).parent


def run_dev_server(
    api_url: Optional[str] = None,
    port: int = 3000,
) -> None:
    """
    Run Next.js development server.
    
    Args:
        api_url: URL of the PyCharter API (defaults to http://localhost:8000)
        port: Port to run dev server on (default: 3000)
    """
    ui_root = get_ui_root()
    
    # Check if package.json exists
    package_json = ui_root / "package.json"
    if not package_json.exists():
        print(f"Error: package.json not found at {package_json}", file=sys.stderr)
        print("Please initialize the Next.js project first.", file=sys.stderr)
        sys.exit(1)
    
    # Get API URL from environment or argument
    if api_url is None:
        api_url = os.getenv("PYCHARTER_API_URL", "http://localhost:8000")
    
    # Set environment variables for Next.js
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_URL"] = api_url
    env["PORT"] = str(port)
    # Note: WebSocket max payload size is controlled by Next.js internally
    # The webpack watchOptions in next.config.js should exclude large directories
    
    # Check if node_modules exists, if not, suggest running npm install
    node_modules = ui_root / "node_modules"
    if not node_modules.exists():
        print("Warning: node_modules not found. Running 'npm install' first...", file=sys.stderr)
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=str(ui_root),
                check=True,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error: npm install failed: {e}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError:
            print("Error: npm not found. Please install Node.js and npm.", file=sys.stderr)
            sys.exit(1)
    
    print(f"PyCharter UI development server starting...")
    print(f"  UI: http://localhost:{port}")
    print(f"  API: {api_url}")
    print(f"  API proxied via: /api/* -> {api_url}/api/*")
    print()
    
    # Run Next.js dev server
    try:
        subprocess.run(
            ["npm", "run", "dev"],
            cwd=str(ui_root),
            env=env,
        )
    except KeyboardInterrupt:
        print("\nShutting down dev server...", file=sys.stderr)
        sys.exit(0)
    except FileNotFoundError:
        print("Error: npm not found. Please install Node.js and npm.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PyCharter UI Development Server")
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="URL of the PyCharter API (default: http://localhost:8000 or PYCHARTER_API_URL env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to run dev server on (default: 3000)",
    )
    
    args = parser.parse_args()
    run_dev_server(api_url=args.api_url, port=args.port)

