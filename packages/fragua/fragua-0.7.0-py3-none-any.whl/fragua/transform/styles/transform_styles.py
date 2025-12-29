"""
Transform style specifications for different data transformation scenarios.
"""

from typing import Any, Dict
from fragua.transform.params.transform_params import (
    AnalysisTransformParams,
    MLTransformParams,
    ReportTransformParams,
)
from fragua.utils.types.enums import ActionType, FieldType, TargetType

TRANSFORM_STYLES: Dict[str, Dict[str, Any]] = {
    TargetType.ML.value: {
        FieldType.ACTION.value: ActionType.TRANSFORM.value,
        FieldType.FUNC_KEY.value: TargetType.ML.value,
        FieldType.PARAMS_TYPE.value: MLTransformParams,
        FieldType.PURPOSE.value: "Apply machine learning preprocessing steps.",
    },
    TargetType.REPORT.value: {
        FieldType.ACTION.value: ActionType.TRANSFORM.value,
        FieldType.FUNC_KEY.value: TargetType.REPORT.value,
        FieldType.PARAMS_TYPE.value: ReportTransformParams,
        FieldType.PURPOSE.value: "Prepare data for reporting.",
    },
    TargetType.ANALYSIS.value: {
        FieldType.ACTION.value: ActionType.TRANSFORM.value,
        FieldType.FUNC_KEY.value: TargetType.ANALYSIS.value,
        FieldType.PARAMS_TYPE.value: AnalysisTransformParams,
        FieldType.PURPOSE.value: "Perform analytical transformations.",
    },
}
