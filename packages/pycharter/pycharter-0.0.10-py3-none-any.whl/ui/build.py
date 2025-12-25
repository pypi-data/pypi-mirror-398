"""
Build script for PyCharter UI.

Builds the Next.js frontend and copies assets to the static directory.
This is used both for development and for preparing the UI for packaging.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_ui_root() -> Path:
    """Get the root directory of the UI module."""
    return Path(__file__).parent


def build_ui() -> int:
    """
    Build the Next.js UI for production.
    
    Returns:
        0 on success, 1 on failure
    """
    ui_root = get_ui_root()
    
    # Check if package.json exists
    package_json = ui_root / "package.json"
    if not package_json.exists():
        print(f"❌ Error: package.json not found at {package_json}", file=sys.stderr)
        print("Please initialize the Next.js project first.", file=sys.stderr)
        return 1
    
    # Check if node_modules exists
    node_modules = ui_root / "node_modules"
    if not node_modules.exists():
        print("Installing npm dependencies...", file=sys.stderr)
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=str(ui_root),
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: npm install failed: {e}", file=sys.stderr)
            return 1
        except FileNotFoundError:
            print("❌ Error: npm not found. Please install Node.js and npm.", file=sys.stderr)
            return 1
    
    # Build Next.js
    print("Building Next.js application...", file=sys.stderr)
    env = os.environ.copy()
    env["NODE_ENV"] = "production"
    try:
        subprocess.run(
            ["npm", "run", "build"],
            cwd=str(ui_root),
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: npm run build failed: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("❌ Error: npm not found. Please install Node.js and npm.", file=sys.stderr)
        return 1
    
    # Check if out/ directory exists (Next.js export output)
    out_dir = ui_root / "out"
    if not out_dir.exists():
        print(f"❌ Error: Build output directory not found at {out_dir}", file=sys.stderr)
        print("Next.js build may have failed.", file=sys.stderr)
        return 1
    
    # Copy built files to static/ directory
    static_dir = ui_root / "static"
    
    # Remove existing static directory if it exists
    if static_dir.exists():
        print(f"Removing existing static directory...", file=sys.stderr)
        shutil.rmtree(static_dir)
    
    # Copy out/ to static/
    print(f"Copying build output to {static_dir}...", file=sys.stderr)
    try:
        shutil.copytree(out_dir, static_dir)
        print(f"✓ Successfully built UI. Static files are in {static_dir}", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"❌ Error copying build output: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(build_ui())
