import pandas as pd
import polars as pl
import pyarrow as pa
import numpy as np
from PIL import Image
from typing import Any
from collections import deque
from pathlib import Path
import uuid
from decimal import Decimal
from datetime import datetime, date, time, timedelta


def if_any(value: Any) -> bool:

    if value is None:
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float, complex, Decimal)):
        return True

    if isinstance(value, (str, bytes, bytearray)):
        return bool(value)

    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return bool(value)

    if isinstance(value, deque):
        return bool(value)

    if isinstance(value, Path):
        return value.exists()

    if isinstance(value, pd.Series):
        return not value.empty and not value.isna().all()
    elif isinstance(value, pd.DataFrame):
        return not value.empty and not value.isna().all().all()

    if isinstance(value, pl.Series):
        return not value.is_empty() and not value.is_null().all()
    elif isinstance(value, pl.DataFrame):
        return not value.is_empty() and not (
            value.null_count().sum_horizontal().item() == value.height * value.width
        )

    if isinstance(value, np.ndarray):
        return value.size > 0

    if isinstance(value, pa.Table):
        return value.num_rows > 0

    if isinstance(value, (datetime, date, time, timedelta)):
        return True

    if isinstance(value, uuid.UUID):
        return True

    if isinstance(value, Image.Image):
        return value.size[0] > 0 and value.size[1] > 0

    # Handle file-like objects (BytesIO, StringIO, etc.)
    if hasattr(value, "read") and hasattr(value, "seek"):
        try:
            current_pos = value.tell()
            value.seek(0, 2)  # Seek to end
            size = value.tell()
            value.seek(current_pos)  # Restore position
            return size > 0
        except (OSError, IOError):
            return True  # If we can't determine size, assume it has content

    if callable(value):
        return True

    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, bytearray)):
        try:
            iterator = iter(value)
            next(iterator)
            return True
        except StopIteration:
            return False
        except (TypeError, AttributeError):
            pass

    if hasattr(value, "__bool__"):
        return bool(value)

    return True
