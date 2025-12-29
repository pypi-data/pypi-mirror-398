"""Metadata utilities for Fragua."""

from typing import Any, Dict, Optional
from fragua.utils.metrics.metrics import calculate_checksum, get_local_time_and_offset
from fragua.utils.logger import get_logger

logger = get_logger(__name__)


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
