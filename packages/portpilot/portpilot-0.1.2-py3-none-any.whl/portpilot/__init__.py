"""PortPilot package.

This file marks the `portpilot` directory as a Python package so that the
console scripts defined in `pyproject.toml` (e.g. `portpilot = portpilot.cli:main`)
can import correctly.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Keep in sync with `pyproject.toml` if you manually bump versions.
__version__ = "0.1.0"
