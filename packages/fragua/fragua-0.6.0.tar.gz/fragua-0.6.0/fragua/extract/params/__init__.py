"""
Extract Params Module.

This module contains:
- ExtractParams base class.
- Extract CSV, excel, API & SQL Params class.
- Generic types for each Params class(e.g. ExtractParamsT).
- Dict registry with each Params class.('name': class)
"""

from .extract_params import (
    CSVExtractParams,
    ExcelExtractParams,
    APIExtractParams,
    SQLExtractParams,
    EXTRACT_PARAMS,
)


__all__ = [
    "CSVExtractParams",
    "ExcelExtractParams",
    "SQLExtractParams",
    "APIExtractParams",
    "EXTRACT_PARAMS",
]
