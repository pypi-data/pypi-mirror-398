"""
Load Params Module.

This module contains:
- LoadParams base class.
- Load CSV, excel, API & SQL Params class.
- Generic types for each Params class(e.g. LoadParamsT).
- Dict registry with each Params class.('name': class)
"""

from .load_params import (
    ExcelLoadParams,
    APILoadParams,
    CSVLoadParams,
    SQLLoadParams,
    LOAD_PARAMS,
)


__all__ = [
    "ExcelLoadParams",
    "CSVLoadParams",
    "SQLLoadParams",
    "APILoadParams",
    "LOAD_PARAMS",
]
