"""
Extract Styles Module.

This module contains:
- ExtractStyle base class.
- Extract CSV, excel, API & SQL Style class.
- Dict registry with each Style class.('name': class)
"""

from .extract_styles import (
    EXTRACT_STYLES,
)


__all__ = [
    "EXTRACT_STYLES",
]
