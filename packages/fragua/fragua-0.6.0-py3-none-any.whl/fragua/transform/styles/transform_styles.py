"""
Transform style specifications for different data transformation scenarios.
"""

from typing import Any, Dict
from fragua.transform.params.transform_params import (
    AnalysisTransformParams,
    MLTransformParams,
    ReportTransformParams,
)

TRANSFORM_STYLES: Dict[str, Dict[str, Any]] = {
    "ml": {
        "action": "transform",
        "function_key": "ml",
        "params_type": MLTransformParams,
        "purpose": "Apply machine learning preprocessing steps.",
    },
    "report": {
        "action": "transform",
        "function_key": "report",
        "params_type": ReportTransformParams,
        "purpose": "Prepare data for reporting.",
    },
    "analysis": {
        "action": "transform",
        "function_key": "analysis",
        "params_type": AnalysisTransformParams,
        "purpose": "Perform analytical transformations.",
    },
}
