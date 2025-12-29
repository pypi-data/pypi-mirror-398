"""
Internal helper functions for LoadFunction implementations.

These utilities encapsulate reusable logic commonly required
by load styles, such as validation, path resolution, data
normalization, and persistence operations.
"""

import os
from typing import Any, Callable, Dict, List, Literal
from dataclasses import dataclass
import requests
import pandas as pd
from sqlalchemy import create_engine

# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments


def validate_load(
    data: pd.DataFrame,
    destination: str,
) -> None:
    """
    Validate required inputs for load operations.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Load function requires a pandas DataFrame")

    if not destination:
        raise ValueError("'destination' is required")


def validate_sql_load(
    data: pd.DataFrame,
    destination: str,
    table_name: str | None,
) -> None:
    """validate sql required inputs operations."""
    validate_load(data, destination)

    if not table_name:
        raise ValueError("'table_name' is required")


def validate_api_load(
    data: pd.DataFrame,
    url: str,
    method: str,
) -> None:
    """Validate required inputs for API load operations."""
    validate_load(data, url)

    if method not in {"POST", "PUT", "PATCH"}:
        raise ValueError(f"Unsupported HTTP method: {method}")


def build_path(
    destination: str,
    file_name: str,
) -> dict[str, str]:
    """
    Build and validate the output file path."""
    if not destination:
        raise ValueError("'destination' must be provided")

    if not file_name:
        raise ValueError("'file_name' must be provided")

    os.makedirs(destination, exist_ok=True)

    _, ext = os.path.splitext(file_name)
    final_name = file_name if ext else f"{file_name}.xlsx"

    return {"path": os.path.join(destination, final_name)}


def convert_datetime_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    Convert timezone-aware datetime columns to naive datetime.
    """
    datetime_cols = data.select_dtypes(include=["datetimetz"]).columns
    if len(datetime_cols) > 0:
        data = data.copy()
        for col in datetime_cols:
            data[col] = pd.to_datetime(data[col]).dt.tz_convert(None)

    return data


def write_excel(
    data: pd.DataFrame,
    path: str,
    sheet_name: str | None = None,
    index: bool = False,
    engine: Literal["openpyxl", "xlsxwriter", "odf"] = "openpyxl",
) -> None:
    """
    Write a DataFrame to an Excel file.
    """
    if os.path.exists(path):
        with pd.ExcelWriter(
            path,
            mode="a",
            engine=engine,
            if_sheet_exists="new",
        ) as writer:
            if sheet_name:
                data.to_excel(writer, sheet_name=sheet_name, index=index)
            else:
                data.to_excel(writer, index=index)
    else:
        with pd.ExcelWriter(path, engine=engine) as writer:
            if sheet_name:
                data.to_excel(writer, sheet_name=sheet_name, index=index)
            else:
                data.to_excel(writer, index=index)


def write_csv(
    data: pd.DataFrame,
    path: str,
    delimiter: str | None,
    encoding: str | None,
    index: bool | None,
) -> None:
    """
    Write a DataFrame to a CSV file.
    """
    data.to_csv(
        path,
        sep=delimiter or ",",
        encoding=encoding or "utf-8",
        index=bool(index),
    )


def write_sql(
    data: pd.DataFrame,
    destination: str,
    table_name: str,
    if_exists: Literal["fail", "replace", "append", "delete_rows"] = "fail",
    index: bool = False,
    chunksize: int | None = None,
) -> pd.DataFrame:
    """Write a DataFrame as an new table into an database."""
    engine = create_engine(destination)

    try:
        data.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=index,
            chunksize=chunksize,
        )
    finally:
        engine.dispose()

    return data


def write_api(
    data: pd.DataFrame,
    url: str,
    method: str,
    headers: dict[str, Any] | None = None,
    timeout: int = 30,
    raise_for_status: bool = True,
) -> pd.DataFrame:
    """Send a DataFrame to an external API endpoint."""

    payload = data.to_dict(orient="records")

    response = requests.request(
        method=method,
        url=url,
        json=payload,
        headers=headers,
        timeout=timeout,
    )

    if raise_for_status:
        response.raise_for_status()

    return data


@dataclass(frozen=True)
class LoadInternalSpec:
    """Specification for internal load helper functions."""

    func: Callable[..., Any]
    description: str
    config_keys: List[str]
    data_arg: str | None = None


LOAD_INTERNAL_FUNCTIONS: Dict[str, LoadInternalSpec] = {
    "validate_load": LoadInternalSpec(
        func=validate_load,
        description="Validate load inputs.",
        config_keys=["destination"],
        data_arg="data",
    ),
    "build_path": LoadInternalSpec(
        func=build_path,
        description="Build and validate output path.",
        config_keys=["destination", "file_name"],
        data_arg=None,
    ),
    "convert_datetime_columns": LoadInternalSpec(
        func=convert_datetime_columns,
        description="Convert timezone-aware datetime columns.",
        config_keys=[],
        data_arg="data",
    ),
    "write_excel": LoadInternalSpec(
        func=write_excel,
        description="Write DataFrame to an Excel file.",
        config_keys=["sheet_name", "index", "engine", "path"],
        data_arg="data",
    ),
    "write_csv": LoadInternalSpec(
        func=write_csv,
        description="Persist DataFrame to CSV file.",
        config_keys=["delimiter", "encoding", "index", "path"],
        data_arg="data",
    ),
    "validate_sql_load": LoadInternalSpec(
        func=validate_sql_load,
        description="Validate SQL load configuration.",
        config_keys=["destination", "table_name"],
        data_arg="data",
    ),
    "write_sql": LoadInternalSpec(
        func=write_sql,
        description="Persist DataFrame into a SQL table.",
        config_keys=["destination", "table_name", "if_exists", "index", "chunksize"],
        data_arg="data",
    ),
    "validate_api_load": LoadInternalSpec(
        func=validate_api_load,
        description="Validate API load configuration.",
        config_keys=["url", "method"],
        data_arg="data",
    ),
    "write_api": LoadInternalSpec(
        func=write_api,
        description="Send DataFrame to an external API endpoint.",
        config_keys=["url", "method", "headers", "timeout", "raise_for_status"],
        data_arg="data",
    ),
}
