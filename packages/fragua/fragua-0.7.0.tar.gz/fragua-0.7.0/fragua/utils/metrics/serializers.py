"""Serializer utilities for Fragua."""

from typing import Any, cast
import json
import pandas as pd


def serialize_dataframe(df: pd.DataFrame) -> bytes:
    """Make a copy and sort columns to guarantee deterministic ordering."""
    df_copy = df.copy()
    cols = sorted(df_copy.columns.tolist())
    df_copy = df_copy[cols]
    csv_str = cast(str, df_copy.to_csv(index=False))
    return csv_str.encode("utf-8")


def serialize_other(obj: Any) -> bytes:
    """Serialize dictionaries, lists, or generic Python objects into bytes."""
    if isinstance(obj, (dict, list)):
        serialized = json.dumps(obj, sort_keys=True, default=str)
    else:
        serialized = repr(obj)
    return serialized.encode("utf-8")
