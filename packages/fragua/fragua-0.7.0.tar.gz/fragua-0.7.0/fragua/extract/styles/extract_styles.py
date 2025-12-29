"""
Extract Styles.

"""

from typing import Any, Dict
from fragua.extract.params.extract_params import (
    APIExtractParams,
    CSVExtractParams,
    ExcelExtractParams,
    SQLExtractParams,
)
from fragua.utils.types.enums import ActionType, FieldType, TargetType


EXTRACT_STYLES: Dict[str, Dict[str, Any]] = {
    TargetType.CSV.value: {
        FieldType.ACTION.value: ActionType.EXTRACT.value,
        FieldType.FUNC_KEY.value: TargetType.CSV.value,
        FieldType.PARAMS_TYPE.value: CSVExtractParams,
        "purpose": "Extract tabular data from CSV files.",
    },
    TargetType.EXCEL.value: {
        FieldType.ACTION.value: ActionType.EXTRACT.value,
        FieldType.FUNC_KEY.value: TargetType.EXCEL.value,
        FieldType.PARAMS_TYPE.value: ExcelExtractParams,
        FieldType.PURPOSE.value: "Extract structured data from Excel spreadsheets.",
    },
    TargetType.SQL.value: {
        FieldType.ACTION.value: ActionType.EXTRACT.value,
        FieldType.FUNC_KEY.value: TargetType.SQL.value,
        FieldType.PARAMS_TYPE.value: SQLExtractParams,
        FieldType.PURPOSE.value: "Extract records from SQL databases using queries.",
    },
    TargetType.API.value: {
        FieldType.ACTION.value: ActionType.EXTRACT.value,
        FieldType.FUNC_KEY.value: TargetType.API.value,
        FieldType.PARAMS_TYPE.value: APIExtractParams,
        FieldType.PURPOSE.value: "Extract data from REST APIs over HTTP.",
    },
}
