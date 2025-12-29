"""
Load Functions Module.

This module contains:
- LoadFunction base class.
- Load excel Function class.
- Dict registry with each Function class. ('name': class)
- Dict registry with each internal function. ('name': function(Callable))
"""

from .load_functions import LOAD_FUNCTIONS
from .internal_functions import LOAD_INTERNAL_FUNCTIONS


__all__ = [
    "LOAD_FUNCTIONS",
    "LOAD_INTERNAL_FUNCTIONS",
]
