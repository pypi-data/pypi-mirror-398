"""
Transform parameter classes for different transformation pipelines.

Each class defines the configuration schema required by a specific
TransformFunction and TransformStyle, encapsulating both the input
DataFrame and transformation-specific options.
"""

from typing import Any, Dict, List, Optional, Type


from fragua.core.params import FraguaParams


class MLTransformParams(FraguaParams):
    """
    Parameters for machine learning transformation pipelines.

    These parameters define how raw datasets should be prepared
    for ML workflows, including handling of categorical and numeric
    features, target definition, and outlier treatment.
    """

    purpose = (
        "Transformation parameters used to prepare data for machine learning tasks."
    )

    FIELDS = {
        "target_column": {
            "type": str,
            "required": True,
            "description": "Name of the target variable to be predicted.",
        },
        "categorical_cols": {
            "type": List[str],
            "default": [],
            "description": "List of columns treated as categorical features.",
        },
        "numeric_cols": {
            "type": List[str],
            "default": [],
            "description": "List of columns treated as numeric features.",
        },
        "outlier_threshold": {
            "type": Optional[float],
            "default": None,
            "description": "Threshold factor used for outlier detection or capping.",
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(style="ml", **kwargs)


class ReportTransformParams(FraguaParams):
    """
    Parameters for report-oriented transformation pipelines.

    These parameters focus on formatting, derived metrics,
    and presentation-ready transformations.
    """

    purpose = (
        "Parameters used to prepare, derive, and format data for reporting purposes."
    )

    FIELDS = {
        "format_config": {
            "type": Dict[str, Any],
            "default": {},
            "description": "Formatting rules such as styles or alignment.",
        },
        "derived_columns": {
            "type": Dict[str, str],
            "default": {},
            "description": "Computed columns defined via expressions.",
        },
        "rounding_precision": {
            "type": int,
            "default": 2,
            "description": "Decimal precision applied to numeric values.",
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(style="report", **kwargs)


class AnalysisTransformParams(FraguaParams):
    """
    Parameters for analytical transformation pipelines.

    These parameters enable grouping, aggregation, and sorting
    operations commonly used in exploratory data analysis.
    """

    purpose = (
        "Parameters for performing analytical operations such as "
        "grouping, aggregation, and sorting."
    )

    FIELDS = {
        "groupby_cols": {
            "type": List[str],
            "default": [],
            "description": "Columns used to group the data.",
        },
        "agg_functions": {
            "type": Dict[str, str],
            "default": {},
            "description": "Aggregation functions applied per column.",
        },
        "sort_by": {
            "type": List[str],
            "default": [],
            "description": "Columns used to sort the final result.",
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(style="analysis", **kwargs)


TRANSFORM_PARAMS: Dict[str, Type[FraguaParams]] = {
    "ml": MLTransformParams,
    "report": ReportTransformParams,
    "analysis": AnalysisTransformParams,
}
