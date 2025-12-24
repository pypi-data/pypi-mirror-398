"""
Concrete extraction functions.

This module provides functional extract implementations for common
data sources such as CSV files, Excel spreadsheets, SQL databases,
and REST APIs.
"""

from pathlib import Path
from typing import Any, Dict
import pandas as pd
from sqlalchemy import create_engine
import requests
from requests.auth import HTTPBasicAuth

from fragua.extract.params.extract_params import (
    APIExtractParams,
    CSVExtractParams,
    ExcelExtractParams,
    SQLExtractParams,
)


def extract_csv(
    params: CSVExtractParams,
) -> pd.DataFrame:
    """Extract tabular data from a CSV file."""
    path = params.get("path")
    if not path:
        raise ValueError("'path' is required in params")

    return pd.read_csv(str(Path(path)))


def extract_excel(
    params: ExcelExtractParams,
) -> pd.DataFrame:
    """Extract data from an Excel spreadsheet."""
    path = params.get("path")
    if not path:
        raise ValueError("'path' is required in params")

    return pd.read_excel(
        str(Path(path)),
        sheet_name=params.get("sheet_name"),
    )


def extract_sql(
    params: SQLExtractParams,
) -> pd.DataFrame:
    """Execute a SQL query and extract the result as a DataFrame."""
    connection_string = params.get("connection_string")
    query = params.get("query")

    if not connection_string or not query:
        raise ValueError("'connection_string' and 'query' are required in params")

    engine = create_engine(connection_string)
    try:
        with engine.connect() as conn:
            return pd.read_sql_query(query, conn)
    finally:
        engine.dispose()


def extract_api(
    params: APIExtractParams,
) -> pd.DataFrame:
    """Fetch JSON data from a REST API endpoint."""
    url = params.get("url")
    if not url:
        raise ValueError("'url' is required in params")

    response = requests.request(
        method=params.get("method"),
        url=url,
        headers=params.get("headers"),
        params=params.get("params"),
        data=params.get("data"),
        auth=HTTPBasicAuth(**params.get("auth")) if params.get("auth") else None,
        proxies=params.get("proxy"),
        timeout=params.get("timeout"),
    )
    response.raise_for_status()

    payload = response.json()

    if isinstance(payload, list):
        return pd.DataFrame(payload)

    if isinstance(payload, dict):
        return pd.json_normalize(payload)

    raise ValueError(f"Unexpected API response type: {type(payload)}")


EXTRACT_FUNCTIONS: Dict[str, Dict[str, Any]] = {
    "csv": {
        "action": "extract",
        "purpose": "Extract tabular data from a CSV file.",
        "params_type": CSVExtractParams.__name__,
        "function": extract_csv,
    },
    "excel": {
        "action": "extract",
        "purpose": "Extract data from an Excel spreadsheet.",
        "params_type": ExcelExtractParams.__name__,
        "function": extract_excel,
    },
    "sql": {
        "action": "extract",
        "purpose": "Execute a SQL query and extract the result as a DataFrame.",
        "params_type": SQLExtractParams.__name__,
        "function": extract_sql,
    },
    "api": {
        "action": "extract",
        "purpose": "Fetch JSON data from a REST API endpoint.",
        "params_type": APIExtractParams.__name__,
        "function": extract_api,
    },
}
