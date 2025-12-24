"""
Extract parameter schemas for supported data source types.
"""

from typing import Any, Dict, Type, Union
from pathlib import Path

from fragua.core.params import FraguaParams


class CSVExtractParams(FraguaParams):
    """Parameters for CSV data extraction."""

    purpose = "Parameters required to extract data from a CSV file."

    FIELDS = {
        "path": {
            "type": Union[str, Path],
            "required": True,
            "description": "Filesystem path to the CSV file.",
            "normalize": Path,
        }
    }


class ExcelExtractParams(FraguaParams):
    """Parameters for Excel data extraction."""

    purpose = "Parameters required to extract data from an Excel file."

    FIELDS = {
        "path": {
            "type": Union[str, Path],
            "required": True,
            "description": "Filesystem path to the Excel file.",
            "normalize": Path,
        },
        "sheet_name": {
            "type": Union[str, int],
            "default": 0,
            "description": "Name or index of the worksheet to load.",
        },
    }


class SQLExtractParams(FraguaParams):
    """Parameters for SQL database extraction."""

    purpose = "Parameters required to extract data from a SQL database."

    FIELDS = {
        "connection_string": {
            "type": str,
            "required": True,
            "description": "Database connection URL string.",
        },
        "query": {
            "type": str,
            "required": True,
            "description": "SQL query to be executed.",
        },
    }


class APIExtractParams(FraguaParams):
    """Parameters for HTTP API extraction."""

    purpose = "Parameters required to extract data from an API endpoint."

    FIELDS = {
        "url": {
            "type": str,
            "required": True,
            "description": "Full URL of the API endpoint.",
        },
        "method": {
            "type": str,
            "default": "GET",
            "description": "HTTP method to use (GET, POST, etc).",
        },
        "headers": {
            "type": Dict[str, str],
            "default": {},
            "description": "HTTP headers sent with the request.",
        },
        "params": {
            "type": Dict[str, Any],
            "default": {},
            "description": "URL query parameters sent with the request.",
        },
        "data": {
            "type": Dict[str, Any],
            "default": {},
            "description": "Body data sent for POST/PUT requests.",
        },
        "auth": {
            "type": Dict[str, str],
            "default": {},
            "description": "Authentication credentials (API dependent).",
        },
        "proxy": {
            "type": Dict[str, str],
            "default": {},
            "description": "Proxy configuration for routing the request.",
        },
        "timeout": {
            "type": float,
            "default": 30.0,
            "description": "Maximum time in seconds to wait for a response.",
        },
    }


EXTRACT_PARAMS: Dict[str, Type[FraguaParams]] = {
    "csv": CSVExtractParams,
    "excel": ExcelExtractParams,
    "sql": SQLExtractParams,
    "api": APIExtractParams,
}
