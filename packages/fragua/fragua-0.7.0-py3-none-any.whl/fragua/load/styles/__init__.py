"""
Load Styles Module.

This module contains:
- ExtractStyle base class.
- Load CSV, excel, API & SQL Style class.
- Dict registry with each Style class.('name': class)
"""

from .load_styles import (
    LOAD_STYLES,
)


__all__ = [
    "LOAD_STYLES",
]
