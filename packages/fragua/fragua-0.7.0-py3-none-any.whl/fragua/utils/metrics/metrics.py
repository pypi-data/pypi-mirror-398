"""
Metrics Utilities for Fragua ETL Framework.

This module provides stable and deterministic checksum calculations
for various data structures including pandas DataFrames, dictionaries,
lists, and other Python objects. It ensures reproducible checksums
by serializing the data in a consistent way.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any
import pandas as pd
from fragua.utils.logger import get_logger
from fragua.utils.metrics.serializers import serialize_dataframe, serialize_other

logger = get_logger(__name__)


def calculate_checksum(data: Any, algorithm: str = "sha256") -> str:
    """
    Calculate a stable checksum for DataFrame, dict, list or other objects.

    - DataFrame: sorted columns + to_csv(index=False)
    - dict/list: json.dumps(sort_keys=True)
    - others: str(obj)
    """
    if isinstance(data, pd.DataFrame):
        content = serialize_dataframe(data)
    else:
        content = serialize_other(data)

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
