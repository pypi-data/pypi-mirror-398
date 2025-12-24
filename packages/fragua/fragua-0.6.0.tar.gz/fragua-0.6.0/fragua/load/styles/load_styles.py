"""
Load style specifications for various data loading methods.
"""

from typing import Any, Dict
from fragua.load.params.load_params import (
    APILoadParams,
    CSVLoadParams,
    ExcelLoadParams,
    SQLLoadParams,
)

LOAD_STYLES: Dict[str, Dict[str, Any]] = {
    "excel": {
        "action": "load",
        "function_key": "excel",
        "params_type": ExcelLoadParams,
        "purpose": "Export tabular data to an Excel file.",
    },
    "csv": {
        "action": "load",
        "function_key": "csv",
        "params_type": CSVLoadParams,
        "purpose": "Export tabular data to a CSV file.",
    },
    "sql": {
        "action": "load",
        "function_key": "sql",
        "params_type": SQLLoadParams,
        "purpose": "Load tabular data into a SQL database.",
    },
    "api": {
        "action": "load",
        "function_key": "api",
        "params_type": APILoadParams,
        "purpose": "Send tabular data to a REST API over HTTP.",
    },
}
