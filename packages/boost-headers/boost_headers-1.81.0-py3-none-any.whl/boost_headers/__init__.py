"""boost-headers headers."""

from __future__ import annotations

from pathlib import Path

__version__ = "1.81.0"


def get_include() -> Path:
    """Return the path to the boost-headers headers."""
    return Path(__file__).parent / "include"