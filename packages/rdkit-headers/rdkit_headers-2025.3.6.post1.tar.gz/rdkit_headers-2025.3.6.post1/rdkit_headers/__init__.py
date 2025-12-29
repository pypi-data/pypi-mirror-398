"""rdkit-headers headers."""

from __future__ import annotations

from pathlib import Path

__version__ = "2025.03.6.post1"


def get_include() -> Path:
    """Return the path to the rdkit-headers headers."""
    return Path(__file__).parent / "include"