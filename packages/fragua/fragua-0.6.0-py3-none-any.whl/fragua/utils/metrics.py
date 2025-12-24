"""
Metrics Utilities for Fragua ETL Framework.

This module provides stable and deterministic checksum calculations
for various data structures including pandas DataFrames, dictionaries,
lists, and other Python objects. It ensures reproducible checksums
by serializing the data in a consistent way.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, cast, Optional, Dict, Literal
import pandas as pd
from fragua.utils.logger import get_logger

logger = get_logger(__name__)
StorageType = Literal["", "box", "container"]


def _serialize_dataframe(df: pd.DataFrame) -> bytes:
    """Make a copy and sort columns to guarantee deterministic ordering."""
    df_copy = df.copy()
    cols = sorted(df_copy.columns.tolist())
    df_copy = df_copy[cols]
    csv_str = cast(str, df_copy.to_csv(index=False))
    return csv_str.encode("utf-8")


def _serialize_other(obj: Any) -> bytes:
    """Serialize dictionaries, lists, or generic Python objects into bytes."""
    if isinstance(obj, (dict, list)):
        serialized = json.dumps(obj, sort_keys=True, default=str)
    else:
        serialized = repr(obj)
    return serialized.encode("utf-8")


def calculate_checksum(data: Any, algorithm: str = "sha256") -> str:
    """
    Calculate a stable checksum for DataFrame, dict, list or other objects.

    - DataFrame: sorted columns + to_csv(index=False)
    - dict/list: json.dumps(sort_keys=True)
    - others: str(obj)
    """
    if isinstance(data, pd.DataFrame):
        content = _serialize_dataframe(data)
    else:
        content = _serialize_other(data)

    h = hashlib.new(algorithm)
    h.update(content)
    return h.hexdigest()


def get_local_time_and_offset() -> tuple[str, str]:
    """Return local time string and timezone offset."""
    now_utc = datetime.now(timezone.utc)
    local_tz = datetime.now().astimezone().tzinfo
    now_local = now_utc.astimezone(local_tz)
    local_time_str = now_local.strftime("%H:%M:%S.%f")[:-3]
    timezone_offset = now_local.strftime("%z")
    if len(timezone_offset) == 5:
        timezone_offset = timezone_offset[:3] + ":" + timezone_offset[3:]
    return local_time_str, timezone_offset


def generate_metadata(
    storage: Any,
    **metadata_kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate metadata dictionary for objects with .data and .name.

    Args:
        storage: Storage object that holds data (e.g.  Box, Container).
        **kwargs: Additional metadata fields
            (e.g.,metadata_type, storage_name, agent_name, style_name, etc.).
    """
    data_attr = getattr(storage, "data", storage)
    rows, columns = getattr(data_attr, "shape", (None, None))
    checksum = calculate_checksum(data_attr)
    local_time, timezone_offset = get_local_time_and_offset()

    base_metadata: dict[str, Any] = {
        "local_time": local_time,
        "timezone_offset": timezone_offset,
        "rows": rows,
        "columns": columns,
        "base_checksum": checksum,
    }

    class_type = storage.__class__.__name__.lower()

    if metadata_kwargs.get("metadata_type") == "base":
        base_metadata.update({"type": class_type})
    elif metadata_kwargs.get("metadata_type") == "operation":
        base_metadata.update(
            {
                "origin": metadata_kwargs.get("origin_name"),
                "style_name": metadata_kwargs.get("style_name"),
                "operation_checksum": checksum,
            }
        )
    elif metadata_kwargs.get("metadata_type") == "save":
        base_metadata.update(
            {
                "storage_name": metadata_kwargs.get("storage_name"),
                "store_manager": metadata_kwargs.get("store_manager_name"),
                "agent_name": metadata_kwargs.get("agent_name"),
                "save_checksum": checksum,
            }
        )
    else:
        raise ValueError(
            f"Unknown metadata_type '{metadata_kwargs.get('metadata_type')}'"
        )

    return base_metadata


def add_metadata_to_storage(
    storage: Any,
    metadata: Optional[dict[str, object]] = None,
) -> None:
    """
    Add or merge metadata into a unified metadata dictionary of a storage object.

    Args:
        storage (Storage): The target storage object (e.g., Box, Container).
        data (dict | None): Metadata to add.

    Notes:
        - Automatically ignores None or empty data.
        - Merges keys recursively (non-destructive).
    """
    if not metadata:
        logger.debug("[%s] No metadata provided.", storage.name)
        return

    if not hasattr(storage, "metadata") or storage.metadata is None:
        storage.metadata = {}

    storage.metadata.update(metadata)
