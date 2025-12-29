"""
Transform parameter classes for different transformation pipelines.

Each class defines the configuration schema required by a specific
TransformFunction and TransformStyle, encapsulating both the input
DataFrame and transformation-specific options.
"""

from typing import Any, Dict, List, Optional, Type


from fragua.core.params import FraguaParams
from fragua.utils.types.enums import AttrType, FieldType, TargetType


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
        FieldType.TARGET_COLUMN.value: {
            AttrType.TYPE.value: str,
            AttrType.REQUIRED.value: True,
            AttrType.DESCRIPTION.value: "Name of the target variable to be predicted.",
        },
        FieldType.CATEGORICAL_COLS.value: {
            AttrType.TYPE.value: List[str],
            AttrType.DEFAULT.value: [],
            AttrType.DESCRIPTION.value: "List of columns treated as categorical features.",
        },
        FieldType.NUMERIC_COLS.value: {
            AttrType.TYPE.value: List[str],
            AttrType.DEFAULT.value: [],
            AttrType.DESCRIPTION.value: "List of columns treated as numeric features.",
        },
        FieldType.OUTLIER_THRESHOLD.value: {
            AttrType.TYPE.value: Optional[float],
            AttrType.DEFAULT.value: None,
            AttrType.DESCRIPTION.value: "Threshold factor used for outlier detection or capping.",
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(style=TargetType.ML.value, **kwargs)


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
        FieldType.FORMAT_CONFIG.value: {
            AttrType.TYPE.value: Dict[str, Any],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "Formatting rules such as styles or alignment.",
        },
        FieldType.DERIVED_COLUMNS.value: {
            AttrType.TYPE.value: Dict[str, str],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "Computed columns defined via expressions.",
        },
        FieldType.ROUND_PRECISION.value: {
            AttrType.TYPE.value: int,
            AttrType.DEFAULT.value: 2,
            AttrType.DESCRIPTION.value: "Decimal precision applied to numeric values.",
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(style=TargetType.REPORT.value, **kwargs)


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
        FieldType.GROUP_BY_COLS.value: {
            AttrType.TYPE.value: List[str],
            AttrType.DEFAULT.value: [],
            AttrType.DESCRIPTION.value: "Columns used to group the data.",
        },
        FieldType.AGG_FUNCTION.value: {
            AttrType.TYPE.value: Dict[str, str],
            AttrType.DEFAULT.value: {},
            AttrType.DESCRIPTION.value: "Aggregation functions applied per column.",
        },
        FieldType.SORT_BY.value: {
            AttrType.TYPE.value: List[str],
            AttrType.DEFAULT.value: [],
            AttrType.DESCRIPTION.value: "Columns used to sort the final result.",
        },
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(style=TargetType.ANALYSIS.value, **kwargs)


TRANSFORM_PARAMS: Dict[str, Type[FraguaParams]] = {
    TargetType.ML.value: MLTransformParams,
    TargetType.REPORT.value: ReportTransformParams,
    TargetType.ANALYSIS.value: AnalysisTransformParams,
}
