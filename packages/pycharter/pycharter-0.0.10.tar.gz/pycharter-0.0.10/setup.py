"""
Setup script for PyCharter.

This script handles building the UI before packaging, similar to how Airflow
includes pre-built static files in its package.
"""

import os
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist


class BuildUICommand(build_py):
    """Custom build command that builds the UI before packaging."""
    
    def initialize_options(self):
        """Initialize options - ensure distribution is set up."""
        super().initialize_options()
        # Ensure packages attribute exists (needed for build_meta compatibility)
        # The base class accesses self.packages, which comes from self.distribution.packages
        if not hasattr(self.distribution, 'packages') or self.distribution.packages is None:
            # Packages should be set from pyproject.toml, but ensure it exists
            try:
                from setuptools import find_packages
                self.distribution.packages = find_packages()
            except Exception:
                self.distribution.packages = ["pycharter"]
    
    def finalize_options(self):
        """Finalize options - ensure all build attributes are set."""
        # Call super() first to let base class set up build_lib and other attributes
        super().finalize_options()
        
        # Ensure self.packages is set (copied from distribution.packages)
        if not hasattr(self, 'packages') or self.packages is None:
            self.packages = self.distribution.packages
        
        # Verify build_lib is set (base class should handle this, but verify)
        if not hasattr(self, 'build_lib') or self.build_lib is None:
            # If build_lib is still None, something went wrong with base class initialization
            # Try to set it from build_base
            build_base = getattr(self, 'build_base', None)
            if build_base:
                self.build_lib = os.path.join(build_base, 'lib')
            else:
                # Last resort: use a default
                self.build_lib = os.path.join('build', 'lib')
    
    def run(self):
        """Build the UI static files before building the package."""
        ui_dir = Path(__file__).parent / "ui"
        static_dir = ui_dir / "static"
        
        # Check if UI needs to be built
        if not static_dir.exists() or not (static_dir / "index.html").exists():
            print("Building UI static files for package...")
            
            # Check if package.json exists
            if not (ui_dir / "package.json").exists():
                print("⚠ Warning: UI package.json not found. Skipping UI build.")
                print("   UI static files will not be included in the package.")
                super().run()
                return
            
            # Check if node_modules exists
            if not (ui_dir / "node_modules").exists():
                print("⚠ Warning: node_modules not found. Skipping UI build.")
                print("   Run 'cd ui && npm install' first to include UI in package.")
                super().run()
                return
            
            # Build the UI
            try:
                env = os.environ.copy()
                env["NODE_ENV"] = "production"
                subprocess.run(
                    ["npm", "run", "build"],
                    cwd=str(ui_dir),
                    check=True,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                
                # Copy out/ to static/ if needed
                out_dir = ui_dir / "out"
                if out_dir.exists() and not static_dir.exists():
                    import shutil
                    shutil.copytree(out_dir, static_dir)
                    print("✓ UI built successfully")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"⚠ Warning: UI build failed: {e}")
                print("   Package will be built without UI static files.")
                print("   Users can build UI manually: pycharter ui build")
        
        # Continue with normal build
        super().run()


class SDistCommand(sdist):
    """Custom sdist command that builds UI before creating source distribution."""
    
    def run(self):
        """Build UI before creating source distribution."""
        # Trigger UI build by running build_py command
        # This ensures proper initialization through the command system
        self.run_command('build_py')
        super().run()


# Export cmdclass for setuptools.build_meta to use
# When using setuptools.build_meta, the build system will look for cmdclass
# in setup.py if it exists. We export it as a module-level variable.
cmdclass = {
    "build_py": BuildUICommand,
    "sdist": SDistCommand,
}

# For direct invocation (python setup.py), we still need setup()
if __name__ == "__main__":
    from setuptools import find_packages
    
    setup(
        packages=find_packages(),
        cmdclass=cmdclass,
    )
