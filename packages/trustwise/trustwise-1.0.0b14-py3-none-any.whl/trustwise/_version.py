"""
Version information for the trustwise package.
This file provides a fallback version when the package is not installed.
"""

import re
from pathlib import Path


def get_version() -> str:
    """Get version from pyproject.toml for development."""
    try:
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path) as f:
                content = f.read()
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
    except Exception:  # noqa: BLE001, S110
        pass
    
    return "unknown"

__version__ = get_version() 