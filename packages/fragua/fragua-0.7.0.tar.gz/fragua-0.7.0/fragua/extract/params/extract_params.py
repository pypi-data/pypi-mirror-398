"""
Extract parameter schemas for supported data source types.
"""

from typing import Any, Dict, Type, Union
from pathlib import Path

from fragua.core.params import FraguaParams
from fragua.utils.types.enums import AttrType, FieldType, OperationType, TargetType


class CSVExtractParams(FraguaParams):
    """Parameters for CSV data extraction."""

    purpose = "Parameters required to extract data from a CSV file."

    FIELDS = {
        FieldType.PATH.value: {
            AttrType.TYPE.value: Union[str, Path],
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Filesystem path to the CSV file.",
            AttrType.NORMALIZE.value: Path,
        }
    }


class ExcelExtractParams(FraguaParams):
    """Parameters for Excel data extraction."""

    purpose = "Parameters required to extract data from an Excel file."

    FIELDS = {
        FieldType.PATH.value: {
            AttrType.TYPE.value: Union[str, Path],
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Filesystem path to the Excel file.",
            AttrType.NORMALIZE.value: Path,
        },
        FieldType.SHEET_NAME.value: {
            AttrType.TYPE.value: Union[str, int],
            AttrType.DEFAULT.value: 0,
            AttrType.DESCRIPTION.value: "Name or index of the worksheet to load.",
        },
    }


class SQLExtractParams(FraguaParams):
    """Parameters for SQL database extraction."""

    purpose = "Parameters required to extract data from a SQL database."

    FIELDS = {
        FieldType.CONNECTION_STRING.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Database connection URL string.",
        },
        FieldType.QUERY.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "SQL query to be executed.",
        },
    }


class APIExtractParams(FraguaParams):
    """Parameters for HTTP API extraction."""

    purpose = "Parameters required to extract data from an API endpoint."

    FIELDS = {
        FieldType.URL.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Full URL of the API endpoint.",
        },
        FieldType.METHOD.value: {
            AttrType.TYPE.value: str,
            AttrType.DEFAULT.value: OperationType.GET.value,
            AttrType.DESCRIPTION.value: "HTTP method to use (GET, POST, etc).",
        },
        FieldType.HEADERS.value: {
            AttrType.TYPE.value: Dict[str, str],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "HTTP headers sent with the request.",
        },
        FieldType.PARAMS.value: {
            AttrType.TYPE.value: Dict[str, Any],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "URL query parameters sent with the request.",
        },
        FieldType.DATA.value: {
            AttrType.TYPE.value: Dict[str, Any],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "Body data sent for POST/PUT requests.",
        },
        FieldType.AUTH.value: {
            AttrType.TYPE.value: Dict[str, str],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "Authentication credentials (API dependent).",
        },
        FieldType.PROXY.value: {
            AttrType.TYPE.value: Dict[str, str],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "Proxy configuration for routing the request.",
        },
        FieldType.TIMEOUT.value: {
            AttrType.TYPE.value: float,
            AttrType.DEFAULT.value: 30.0,
            AttrType.DESCRIPTION.value: "Maximum time in seconds to wait for a response.",
        },
    }


EXTRACT_PARAMS: Dict[str, Type[FraguaParams]] = {
    TargetType.CSV.value: CSVExtractParams,
    TargetType.EXCEL.value: ExcelExtractParams,
    TargetType.SQL.value: SQLExtractParams,
    TargetType.API.value: APIExtractParams,
}
