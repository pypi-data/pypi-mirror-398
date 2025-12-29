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
from fragua.utils.types.enums import ActionType, FieldType, TargetType

LOAD_STYLES: Dict[str, Dict[str, Any]] = {
    TargetType.EXCEL.value: {
        FieldType.ACTION.value: ActionType.LOAD.value,
        FieldType.FUNC_KEY.value: TargetType.EXCEL.value,
        FieldType.PARAMS_TYPE.value: ExcelLoadParams,
        FieldType.PURPOSE.value: "Export tabular data to an Excel file.",
    },
    TargetType.CSV.value: {
        FieldType.ACTION.value: ActionType.LOAD.value,
        FieldType.FUNC_KEY.value: TargetType.CSV.value,
        FieldType.PARAMS_TYPE.value: CSVLoadParams,
        FieldType.PURPOSE.value: "Export tabular data to a CSV file.",
    },
    TargetType.SQL: {
        FieldType.ACTION.value: ActionType.LOAD.value,
        FieldType.FUNC_KEY.value: TargetType.SQL.value,
        FieldType.PARAMS_TYPE.value: SQLLoadParams,
        FieldType.PURPOSE.value: "Load tabular data into a SQL database.",
    },
    TargetType.API.value: {
        FieldType.ACTION.value: ActionType.LOAD.value,
        FieldType.FUNC_KEY.value: TargetType.API.value,
        FieldType.PARAMS_TYPE.value: APILoadParams,
        FieldType.PURPOSE.value: "Send tabular data to a REST API over HTTP.",
    },
}
