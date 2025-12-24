"""
Load parameter classes for different data destinations.

Each LoadParams subclass defines the configuration schema required
by a specific load style and its corresponding load function.
"""

from typing import Dict, Optional, Type

from fragua.core.params import FraguaParams


class ExcelLoadParams(FraguaParams):
    """Parameters for loading data into Excel files."""

    purpose = "Parameters required to load data into an Excel file."

    FIELDS = {
        "destination": {
            "type": str,
            "default": "",
            "description": "Target directory or full path where the Excel file will be saved.",
        },
        "file_name": {
            "type": str,
            "default": "",
            "description": "Name of the Excel file to create or overwrite.",
        },
        "sheet_name": {
            "type": str,
            "default": None,
            "description": "Worksheet name where the data will be written.",
        },
        "index": {
            "type": bool,
            "default": False,
            "description": "Whether to include DataFrame row indices in the output file.",
        },
        "engine": {
            "type": Optional[str],
            "default": None,
            "description": "Optional Excel writer engine (e.g., openpyxl, xlsxwriter).",
        },
    }


class CSVLoadParams(FraguaParams):
    """Parameters for loading data into CSV files."""

    purpose = "Parameters required to load data into a CSV file."

    FIELDS = {
        "destination": {
            "type": str,
            "required": True,
            "description": "Directory or full path where the CSV file will be saved.",
        },
        "file_name": {
            "type": str,
            "required": True,
            "description": "Name of the output CSV file.",
        },
        "index": {
            "type": bool,
            "default": False,
            "description": "Whether to include the DataFrame index in the CSV.",
        },
        "sep": {
            "type": str,
            "default": ",",
            "description": "Delimiter for the CSV file (e.g., comma, tab, etc.).",
        },
        "header": {
            "type": bool,
            "default": True,
            "description": "Whether to write column names in the CSV file.",
        },
        "encoding": {
            "type": str,
            "default": "utf-8",
            "description": "Character encoding for the CSV file.",
        },
    }


class SQLLoadParams(FraguaParams):
    """Parameters for loading data into SQL database tables."""

    purpose = "Parameters required to load data into a SQL database table."

    FIELDS = {
        "destination": {
            "type": str,
            "default": "",
            "description": "Database target or connection identifier.",
        },
        "table_name": {
            "type": str,
            "required": True,
            "description": "Name of the target SQL table.",
        },
        "if_exists": {
            "type": str,
            "default": "fail",
            "description": "Behavior when the table already exists (fail, replace, append).",
        },
        "index": {
            "type": bool,
            "default": False,
            "description": "Whether to persist DataFrame indices as table columns.",
        },
        "chunksize": {
            "type": Optional[int],
            "default": None,
            "description": "Number of rows per batch insert operation.",
        },
    }


class APILoadParams(FraguaParams):
    """Parameters for sending data to remote APIs."""

    purpose = "Parameters required to send data to a remote API."

    FIELDS = {
        "destination": {
            "type": str,
            "default": "",
            "description": "Optional identifier for the API service.",
        },
        "endpoint": {
            "type": str,
            "required": True,
            "description": "Target API endpoint URL.",
        },
        "method": {
            "type": str,
            "default": "POST",
            "description": "HTTP method to use (POST, PUT, etc.).",
        },
        "headers": {
            "type": Dict[str, str],
            "default": {},
            "description": "HTTP request headers.",
        },
        "auth": {
            "type": Dict[str, str],
            "default": {},
            "description": "Authentication configuration (tokens, API keys, etc.).",
        },
        "timeout": {
            "type": float,
            "default": 30.0,
            "description": "Maximum time in seconds to wait for the API response.",
        },
    }


LOAD_PARAMS: Dict[str, Type[FraguaParams]] = {
    "excel": ExcelLoadParams,
    "csv": CSVLoadParams,
    "sql": SQLLoadParams,
    "api": APILoadParams,
}
