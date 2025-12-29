"""
Version comparison utilities for data contracts.

Supports semantic versioning (semver) format: MAJOR.MINOR.PATCH
"""

import re
from typing import Optional, Tuple


def parse_version(version: str) -> Tuple[int, int, int, Optional[str]]:
    """
    Parse a version string into components.
    
    Supports formats:
    - "1.0.0" -> (1, 0, 0, None)
    - "1.0.0-alpha" -> (1, 0, 0, "alpha")
    - "1.0" -> (1, 0, 0, None)  # PATCH defaults to 0
    - "1" -> (1, 0, 0, None)  # MINOR and PATCH default to 0
    
    Args:
        version: Version string (e.g., "1.0.0", "2.1.3-alpha")
        
    Returns:
        Tuple of (major, minor, patch, prerelease)
        
    Raises:
        ValueError: If version format is invalid
    """
    if not version or not isinstance(version, str):
        raise ValueError(f"Invalid version: {version}")
    
    # Remove leading 'v' if present
    version = version.lstrip('vV')
    
    # Match semantic version pattern: MAJOR.MINOR.PATCH[-PRERELEASE]
    pattern = r'^(\d+)\.(\d+)(?:\.(\d+))?(?:-([a-zA-Z0-9.-]+))?$'
    match = re.match(pattern, version)
    
    if not match:
        # Try simple integer version
        try:
            major = int(version)
            return (major, 0, 0, None)
        except ValueError:
            raise ValueError(f"Invalid version format: {version}. Expected format: MAJOR.MINOR.PATCH[-PRERELEASE]")
    
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3)) if match.group(3) else 0
    prerelease = match.group(4) if match.group(4) else None
    
    return (major, minor, patch, prerelease)


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    v1_major, v1_minor, v1_patch, v1_prerelease = parse_version(version1)
    v2_major, v2_minor, v2_patch, v2_prerelease = parse_version(version2)
    
    # Compare major version
    if v1_major < v2_major:
        return -1
    if v1_major > v2_major:
        return 1
    
    # Compare minor version
    if v1_minor < v2_minor:
        return -1
    if v1_minor > v2_minor:
        return 1
    
    # Compare patch version
    if v1_patch < v2_patch:
        return -1
    if v1_patch > v2_patch:
        return 1
    
    # Compare prerelease (prerelease versions are lower than release versions)
    if v1_prerelease is None and v2_prerelease is not None:
        return 1
    if v1_prerelease is not None and v2_prerelease is None:
        return -1
    if v1_prerelease is not None and v2_prerelease is not None:
        # Simple string comparison for prerelease
        if v1_prerelease < v2_prerelease:
            return -1
        if v1_prerelease > v2_prerelease:
            return 1
    
    return 0


def is_version_higher(new_version: str, existing_version: str) -> bool:
    """
    Check if new_version is higher than existing_version.
    
    Args:
        new_version: New version string
        existing_version: Existing version string
        
    Returns:
        True if new_version > existing_version, False otherwise
    """
    return compare_versions(new_version, existing_version) > 0


def get_latest_version(versions: list[str]) -> Optional[str]:
    """
    Get the latest version from a list of version strings.
    
    Args:
        versions: List of version strings
        
    Returns:
        Latest version string, or None if list is empty
    """
    if not versions:
        return None
    
    latest = versions[0]
    for version in versions[1:]:
        if compare_versions(version, latest) > 0:
            latest = version
    return latest

