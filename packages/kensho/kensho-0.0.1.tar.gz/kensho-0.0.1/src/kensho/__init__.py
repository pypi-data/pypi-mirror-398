"""Placeholder module for the Kensho Python SDK.

The 0.0.1 release exists solely to reserve the PyPI name. Future releases
will ship the actual Health OS client libraries.
"""

from __future__ import annotations

__all__ = ["get_version", "PRODUCT_NAME"]

PRODUCT_NAME = "Kensho Health OS"


def get_version() -> str:
    """Return the placeholder package version."""

    return "0.0.1"
