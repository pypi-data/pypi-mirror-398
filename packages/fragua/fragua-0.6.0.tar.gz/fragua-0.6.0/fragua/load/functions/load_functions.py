"""
Load function implementations.

This module defines concrete LoadFunction classes responsible
for persisting processed data into external destinations.
Each function encapsulates the low-level persistence logic
for a specific target system or format.
"""

from typing import Any, Dict, Iterable
import pandas as pd

from fragua.core.params import FraguaParams
from fragua.load.functions.internal_functions import LOAD_INTERNAL_FUNCTIONS
from fragua.load.params.load_params import (
    APILoadParams,
    CSVLoadParams,
    ExcelLoadParams,
    SQLLoadParams,
)


def execute_load_pipeline(
    input_data: pd.DataFrame,
    params: FraguaParams,
    steps: Iterable[str],
) -> pd.DataFrame:
    """Execute a sequence of load internal functions as a pipeline."""
    data = input_data
    artifacts: dict[str, Any] = {}

    for step in steps:
        if step not in LOAD_INTERNAL_FUNCTIONS:
            raise KeyError(f"Load function '{step}' not registered.")

        spec = LOAD_INTERNAL_FUNCTIONS[step]

        kwargs = {}

        # 1. params → kwargs
        for key in spec.config_keys:
            value = params.get(key)
            if value is not None:
                kwargs[key] = value

        # 2. artifacts → kwargs (override params)
        for key in spec.config_keys:
            if key in artifacts:
                kwargs[key] = artifacts[key]

        # 3. execute
        if spec.data_arg:
            result = spec.func(**{spec.data_arg: data}, **kwargs)
        else:
            result = spec.func(**kwargs)

        # 4. collect outputs
        if isinstance(result, pd.DataFrame):
            data = result
        elif isinstance(result, dict):
            artifacts.update(result)

    return data


def load_excel(
    input_data: pd.DataFrame,
    params: ExcelLoadParams,
) -> pd.DataFrame:
    """Export a DataFrame to an Excel file."""
    return execute_load_pipeline(
        input_data=input_data,
        params=params,
        steps=[
            "validate_load",
            "build_path",
            "convert_datetime_columns",
            "write_excel",
        ],
    )


def load_csv(
    input_data: pd.DataFrame,
    params: CSVLoadParams,
) -> pd.DataFrame:
    """Export a DataFrame to a CSV file."""
    return execute_load_pipeline(
        input_data=input_data,
        params=params,
        steps=[
            "validate_load",
            "build_path",
            "write_csv",
        ],
    )


def load_sql(
    input_data: pd.DataFrame,
    params: SQLLoadParams,
) -> pd.DataFrame:
    """Persist a DataFrame into a SQL database table."""
    return execute_load_pipeline(
        input_data=input_data,
        params=params,
        steps=[
            "validate_sql_load",
            "write_sql",
        ],
    )


def load_api(
    input_data: pd.DataFrame,
    params: APILoadParams,
) -> pd.DataFrame:
    """Send data to an external API."""
    return execute_load_pipeline(
        input_data=input_data,
        params=params,
        steps=[
            "validate_api_load",
            "write_api",
        ],
    )


LOAD_FUNCTIONS: Dict[str, Dict[str, Any]] = {
    "excel": {
        "action": "load",
        "purpose": "Export a DataFrame to an Excel file.",
        "params_type": ExcelLoadParams.__name__,
        "function": load_excel,
    },
    "csv": {
        "action": "load",
        "purpose": "Export a DataFrame to a CSV file.",
        "params_type": CSVLoadParams.__name__,
        "function": load_csv,
    },
    "sql": {
        "action": "load",
        "purpose": "Persist a DataFrame into a SQL database table.",
        "params_type": SQLLoadParams.__name__,
        "function": load_sql,
    },
    "api": {
        "action": "load",
        "purpose": "Send data to an external API.",
        "params_type": APILoadParams.__name__,
        "function": load_api,
    },
}
