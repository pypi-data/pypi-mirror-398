"""
Transform Functions.
"""

from typing import Any, Dict, Iterable

import pandas as pd
from fragua.core.params import FraguaParams
from fragua.transform.functions.internal_functions import (
    TRANSFORM_INTERNAL_FUNCTIONS,
)

from fragua.transform.params.transform_params import (
    AnalysisTransformParams,
    MLTransformParams,
    ReportTransformParams,
)


def execute_transform_pipeline(
    input_data: pd.DataFrame,
    params: FraguaParams,
    steps: Iterable[str],
) -> pd.DataFrame:
    """
    Execute a transformation pipeline composed of ordered steps.

    Args:
        input_data:
            Input DataFrame to be transformed.
        params:
            Configuration object containing transformation options.
        steps:
            Ordered list of internal transform step names.
        context:
            Optional execution context (reserved for future use).

    Returns:
        pd.DataFrame:
            Transformed DataFrame.

    Raises:
        KeyError:
            If a transformation step is not registered.
    """
    data = input_data

    for step in steps:
        if step not in TRANSFORM_INTERNAL_FUNCTIONS:
            raise KeyError(f"Transform function '{step}' not registered.")

        spec = TRANSFORM_INTERNAL_FUNCTIONS[step]

        kwargs = {
            key: getattr(params, key)
            for key in spec.config_keys
            if hasattr(params, key)
        }

        data = spec.func(data, **kwargs)

    return data


def transform_ml(
    input_data: pd.DataFrame,
    params: MLTransformParams,
) -> pd.DataFrame:
    """
    Apply ML-ready transformations including cleanup, encoding,
    outlier treatment, and scaling.
    """
    return execute_transform_pipeline(
        input_data=input_data,
        params=params,
        steps=[
            "fill_missing",
            "standardize",
            "encode_categoricals",
            "treat_outliers",
            "scale_numeric",
        ],
    )


def transform_report(
    input_data: pd.DataFrame,
    params: ReportTransformParams,
) -> pd.DataFrame:
    """
    Prepare data for reporting by cleaning values, standardizing text,
    adding derived columns, and formatting numbers.
    """
    return execute_transform_pipeline(
        input_data=input_data,
        params=params,
        steps=[
            "fill_missing",
            "standardize",
            "add_derived_columns",
            "format_numeric",
        ],
    )


def transform_analysis(
    input_data: pd.DataFrame,
    params: AnalysisTransformParams,
) -> pd.DataFrame:
    """
    Prepare datasets for exploratory analysis using grouping,
    aggregation, sorting, and basic cleanup.
    """
    return execute_transform_pipeline(
        input_data=input_data,
        params=params,
        steps=[
            "fill_missing",
            "standardize",
            "group_and_aggregate",
            "sort_dataframe",
        ],
    )


TRANSFORM_FUNCTIONS: Dict[str, Dict[str, Any]] = {
    "ml": {
        "action": "transform",
        "purpose": (
            "Apply ML-ready transformations including cleanup, "
            "encoding, outlier treatment, and scaling."
        ),
        "params_type": MLTransformParams.__name__,
        "function": transform_ml,
    },
    "report": {
        "action": "transform",
        "purpose": (
            "Prepare data for reporting by cleaning values, "
            "standardizing text, adding derived columns, "
            "and formatting numbers."
        ),
        "params_type": ReportTransformParams.__name__,
        "function": transform_report,
    },
    "analysis": {
        "action": "transform",
        "purpose": (
            "Prepare datasets for exploratory analysis using grouping, "
            "aggregation, sorting, and basic cleanup."
        ),
        "params_type": AnalysisTransformParams.__name__,
        "function": transform_analysis,
    },
}
