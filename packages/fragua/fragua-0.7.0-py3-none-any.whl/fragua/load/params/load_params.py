"""
Load parameter classes for different data destinations.

Each LoadParams subclass defines the configuration schema required
by a specific load style and its corresponding load function.
"""

from typing import Dict, Optional, Type

from fragua.core.params import FraguaParams
from fragua.utils.types.enums import AttrType, FieldType, TargetType


class ExcelLoadParams(FraguaParams):
    """Parameters for loading data into Excel files."""

    purpose = "Parameters required to load data into an Excel file."

    FIELDS = {
        FieldType.DESTINATION.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: None,
            AttrType.DESCRIPTION.value: "Target path where the file will be saved.",
        },
        FieldType.FILE_NAME: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: None,
            AttrType.DESCRIPTION.value: "Name of the Excel file to create or overwrite.",
        },
        FieldType.SHEET_NAME: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: None,
            AttrType.DESCRIPTION.value: "Worksheet name where the data will be written.",
        },
        FieldType.INDEX: {
            AttrType.TYPE.value: bool,
            AttrType.DEFAULT.value: False,
            AttrType.DESCRIPTION.value: "Whether to include DataFrame row indices in the output.",
        },
        FieldType.ENGINE: {
            AttrType.TYPE.value: Optional[str],
            AttrType.DEFAULT.value: None,
            AttrType.DESCRIPTION.value: "Optional Excel writer engine (e.g. openpyxl, xlsxwriter).",
        },
    }


class CSVLoadParams(FraguaParams):
    """Parameters for loading data into CSV files."""

    purpose = "Parameters required to load data into a CSV file."

    FIELDS = {
        FieldType.DESTINATION.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Directory or full path where the CSV file will be saved.",
        },
        FieldType.FILE_NAME.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Name of the output CSV file.",
        },
        FieldType.INDEX.value: {
            AttrType.TYPE.value: bool,
            AttrType.DEFAULT.value: False,
            AttrType.DESCRIPTION.value: "Whether to include the DataFrame index in the CSV.",
        },
        FieldType.SEPARATOR.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: ",",
            AttrType.DESCRIPTION.value: "Delimiter for the CSV file (e.g., comma, tab, etc.).",
        },
        FieldType.HEADER.value: {
            AttrType.TYPE.value: bool,
            AttrType.DEFAULT.value: True,
            AttrType.DESCRIPTION.value: "Whether to write column names in the CSV file.",
        },
        FieldType.ENCODING.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: "utf-8",
            AttrType.DESCRIPTION.value: "Character encoding for the CSV file.",
        },
    }


class SQLLoadParams(FraguaParams):
    """Parameters for loading data into SQL database tables."""

    purpose = "Parameters required to load data into a SQL database table."

    FIELDS = {
        FieldType.DESTINATION.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: "",
            AttrType.DESCRIPTION.value: "Database target or connection identifier.",
        },
        FieldType.TABLE_NAME.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Name of the target SQL table.",
        },
        FieldType.IF_EXISTS.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: "fail",
            AttrType.DESCRIPTION.value: "Behavior when the table already exists.",
        },
        FieldType.INDEX.value: {
            AttrType.TYPE.value: bool,
            AttrType.DEFAULT.value: False,
            AttrType.DESCRIPTION.value: "Whether to persist DataFrame indices as table columns.",
        },
        FieldType.CHUNKSIZE.value: {
            AttrType.TYPE.value: Optional[int],
            AttrType.DEFAULT.value: None,
            AttrType.DESCRIPTION.value: "Number of rows per batch insert operation.",
        },
    }


class APILoadParams(FraguaParams):
    """Parameters for sending data to remote APIs."""

    purpose = "Parameters required to send data to a remote API."

    FIELDS = {
        FieldType.DESTINATION.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: "",
            AttrType.DESCRIPTION.value: "Optional identifier for the API service.",
        },
        FieldType.ENDPOINT.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Target API endpoint URL.",
        },
        FieldType.METHOD.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: "POST",
            AttrType.DESCRIPTION.value: "HTTP method to use (POST, PUT, etc.).",
        },
        FieldType.HEADERS.value: {
            AttrType.TYPE.value: Dict[str, str],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "HTTP request headers.",
        },
        FieldType.AUTH.value: {
            AttrType.TYPE.value: Dict[str, str],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "Authentication configuration (tokens, API keys, etc.).",
        },
        FieldType.TIMEOUT.value: {
            AttrType.TYPE.value: float,
            AttrType.DEFAULT.value: 30.0,
            AttrType.DESCRIPTION.value: "Maximum time in seconds to wait for the API response.",
        },
    }


LOAD_PARAMS: Dict[str, Type[FraguaParams]] = {
    TargetType.EXCEL.value: ExcelLoadParams,
    TargetType.CSV.value: CSVLoadParams,
    TargetType.SQL.value: SQLLoadParams,
    TargetType.API.value: APILoadParams,
}
