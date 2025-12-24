"""
Internal transformation functions used by TransformFunction pipelines.

Each function operates over a TransformParams instance, mutating
its internal DataFrame and returning the same params object to
allow sequential pipeline execution.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
from pandas.errors import UndefinedVariableError
from sklearn.preprocessing import MinMaxScaler

from fragua.utils.logger import get_logger

logger = get_logger(__name__)


def fill_missing(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Fill missing values in numeric and categorical columns.

    Config keys:
        - numeric_fill: Strategy for numeric columns ("mean" | "zero").
          Default: "mean".
        - categorical_fill: Fill value for categorical columns.
          Default: "unknown".

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.

    Returns:
        pd.DataFrame:
            DataFrame with missing values filled.
    """
    cfg = config or {}

    numeric_fill: str = cfg.get("numeric_fill", "mean")
    categorical_fill: str = cfg.get("categorical_fill", "unknown")

    df = data.copy()

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            fill_value = df[col].mean() if numeric_fill == "mean" else 0
            df[col] = df[col].fillna(fill_value)
        else:
            df[col] = df[col].fillna(categorical_fill)

    logger.info("Transform: Missing values filled.")
    return df


def standardize(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,  # pylint: disable=unused-argument
) -> pd.DataFrame:
    """
    Standardize string columns for consistency.

    Applies trimming and lowercase normalization to all object-type
    columns.

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Unused. Present for interface consistency.

    Returns:
        pd.DataFrame:
            DataFrame with standardized string columns.
    """
    df = data.copy()

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.lower()

    logger.info("Transform: String columns standardized.")
    return df


def encode_categoricals(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,  # pylint: disable=unused-argument
) -> pd.DataFrame:
    """
    Encode categorical columns into dummy variables.

    All object-type columns are converted using one-hot encoding.

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.
            Currently unused but reserved for future options.

    Returns:
        pd.DataFrame:
            DataFrame with encoded categorical features.
    """
    df = data.copy()

    cat_cols = df.select_dtypes(include="object").columns
    if len(cat_cols) > 0:
        df = pd.get_dummies(df, columns=cat_cols)
        logger.info("Transform: Encoded categoricals: %s", list(cat_cols))

    return df


def scale_numeric(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,  # pylint: disable=unused-argument
) -> pd.DataFrame:
    """
    Scale numeric columns to a normalized range.

    Applies Min-Max scaling to all numeric columns, transforming
    values to the [0, 1] range.

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.
            Currently unused but reserved for future options.

    Returns:
        pd.DataFrame:
            DataFrame with scaled numeric columns.
    """
    df = data.copy()
    num_cols = df.select_dtypes(include="number").columns

    if len(num_cols) > 0:
        scaler = MinMaxScaler()
        df[num_cols] = scaler.fit_transform(df[num_cols])
        logger.info("Transform: Scaled numeric columns: %s", list(num_cols))

    return df


def treat_outliers(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Cap outliers in numeric columns using the IQR method.

    Config keys:
        - outlier_threshold: IQR multiplier used for clipping.
          Default: 1.5.

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.

    Returns:
        pd.DataFrame:
            DataFrame with numeric outliers capped.
    """
    cfg = config or {}
    factor: float = cfg.get("outlier_threshold", 1.5) or 1.5

    df = data.copy()
    num_cols = df.select_dtypes(include="number").columns

    for col in num_cols:
        Q1, Q3 = df[col].quantile([0.25, 0.75])
        IQR = Q3 - Q1
        df[col] = np.clip(df[col], Q1 - factor * IQR, Q3 + factor * IQR)

    logger.info("Transform: Outliers treated with factor %.2f", factor)
    return df


def add_derived_columns(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Add derived or computed columns to the DataFrame.

    Config keys:
        - derived_columns: Mapping of column names to pandas
          evaluation expressions.

    If no derived columns are provided and both 'quantity' and 'price'
    columns exist, a default 'total' column is computed.

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.

    Returns:
        pd.DataFrame:
            DataFrame with derived columns added.
    """
    cfg = config or {}
    derived: Optional[Dict[str, str]] = cfg.get("derived_columns")

    df = data.copy()

    if derived:
        for new_col, expr in derived.items():
            try:
                df[new_col] = df.eval(expr)
                logger.debug(
                    "Transform: Derived column '%s' created from '%s'.",
                    new_col,
                    expr,
                )
            except (UndefinedVariableError, SyntaxError, TypeError, ValueError) as exc:
                logger.warning(
                    "Transform: Could not compute derived column '%s': %s",
                    new_col,
                    exc,
                )

    elif {"quantity", "price"}.issubset(df.columns):
        df["total"] = df["quantity"] * df["price"]
        logger.debug("Transform: Default derived column 'total' added.")

    return df


def format_numeric(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Format numeric columns by rounding values.

    Config keys:
        - rounding_precision: Number of decimal places to apply.
          Default: 2.

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.

    Returns:
        pd.DataFrame:
            DataFrame with formatted numeric values.
    """
    cfg = config or {}
    precision: int = cfg.get("rounding_precision", 2) or 2

    df = data.copy()
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].round(precision)

    logger.info("Transform: Numeric columns formatted with precision %d", precision)
    return df


def group_and_aggregate(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Group and aggregate data based on provided configuration.

    Config keys:
        - groupby_cols: List of columns used for grouping.
        - agg_functions: Mapping of column names to aggregation functions.
          If omitted, a default 'sum' aggregation is applied.

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.

    Returns:
        pd.DataFrame:
            Grouped and aggregated DataFrame.
    """
    cfg = config or {}
    groupby_cols = cfg.get("groupby_cols", []) or []
    agg_functions = cfg.get("agg_functions", {}) or {}

    df = data.copy()

    if groupby_cols:
        if agg_functions:
            df = df.groupby(groupby_cols).agg(agg_functions).reset_index()
            logger.info(
                "Transform: Grouped by %s with custom aggregations.", groupby_cols
            )
        else:
            df = df.groupby(groupby_cols).agg("sum").reset_index()
            logger.info(
                "Transform: Grouped by %s using default sum aggregation.", groupby_cols
            )

    return df


def sort_dataframe(
    data: pd.DataFrame,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Sort the DataFrame by specified columns.

    Config keys:
        - sort_by: List of columns to sort by (ascending order).

    Args:
        data (pd.DataFrame):
            Input DataFrame to process.
        config (Optional[Dict[str, Any]]):
            Optional configuration dictionary.

    Returns:
        pd.DataFrame:
            Sorted DataFrame.
    """
    cfg = config or {}
    sort_by = cfg.get("sort_by", []) or []

    df = data.copy()

    if sort_by:
        df = df.sort_values(by=sort_by)
        logger.info("Transform: Sorted DataFrame by %s.", sort_by)

    return df


TransformFunc = Callable[
    [pd.DataFrame],
    pd.DataFrame,
]


@dataclass(frozen=True)
class TransformInternalSpec:
    """
    Specification for an internal transform function.
    """

    func: Callable[..., pd.DataFrame]
    description: str
    config_keys: List[str]


TRANSFORM_INTERNAL_FUNCTIONS: Dict[str, TransformInternalSpec] = {
    "fill_missing": TransformInternalSpec(
        func=fill_missing,
        description="Fill missing values in numeric and categorical columns.",
        config_keys=["numeric_fill", "categorical_fill"],
    ),
    "standardize": TransformInternalSpec(
        func=standardize,
        description="Trim and lowercase all string columns.",
        config_keys=[],
    ),
    "encode_categoricals": TransformInternalSpec(
        func=encode_categoricals,
        description="Convert categorical columns to dummy variables.",
        config_keys=[],
    ),
    "scale_numeric": TransformInternalSpec(
        func=scale_numeric,
        description="Scale numeric columns using MinMaxScaler.",
        config_keys=[],
    ),
    "treat_outliers": TransformInternalSpec(
        func=treat_outliers,
        description="Cap outliers using the IQR method.",
        config_keys=["outlier_threshold"],
    ),
    "add_derived_columns": TransformInternalSpec(
        func=add_derived_columns,
        description="Create derived columns based on expressions.",
        config_keys=["derived_columns"],
    ),
    "format_numeric": TransformInternalSpec(
        func=format_numeric,
        description="Round numeric columns to a given precision.",
        config_keys=["rounding_precision"],
    ),
    "group_and_aggregate": TransformInternalSpec(
        func=group_and_aggregate,
        description="Group and aggregate data using columns and aggregation functions.",
        config_keys=["groupby_cols", "agg_functions"],
    ),
    "sort_dataframe": TransformInternalSpec(
        func=sort_dataframe,
        description="Sort the DataFrame by specified columns.",
        config_keys=["sort_by"],
    ),
}
