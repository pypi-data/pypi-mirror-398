from __future__ import annotations

from typing import Dict, Any, Optional, Tuple
from pyspark.sql import DataFrame
from sparkdq.core.validators.base import Validator


class RowCountGreaterThan(Validator):
    """
    Validates that the DataFrame has more than a given threshold of rows.

    Ergonomic constructor:
        RowCountGreaterThan(threshold: int, name: Optional[str] = None)

    Metrics:
      - row_count: total number of rows
      - threshold: value used for comparison

    Passed if: row_count > threshold
    """

    def __init__(self, threshold: int, name: Optional[str] = None):
        if threshold is None:
            raise TypeError("RowCountGreaterThan requires 'threshold'")
        try:
            thr = int(threshold)
        except Exception:
            raise TypeError(f"RowCountGreaterThan 'threshold' must be an integer, got {threshold!r}")

        params = {"threshold": thr}
        super().__init__(name or f"row_count_gt:{thr}", params)

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        row_count = df.count()
        threshold = int(self.params["threshold"])
        passed = row_count > threshold

        return {
            "passed": passed,
            "metrics": {
                "row_count": row_count,
                "threshold": threshold,
            },
        }


class RowCountBetween(Validator):
    """
    Validates that the DataFrame row count lies between [low, high], inclusive or exclusive.

    Ergonomic constructor:
        RowCountBetween(
            between: Tuple[int, int],
            inclusive: bool = True,
            name: Optional[str] = None,
        )

    Metrics:
      - row_count: total number of rows
      - bounds: [low, high]
      - inclusive: whether bounds are inclusive

    Passed if:
      inclusive=True  -> low <= row_count <= high
      inclusive=False -> low <  row_count <  high
    """

    def __init__(self, between: Tuple[int, int], inclusive: bool = True, name: Optional[str] = None):
        if not isinstance(between, (list, tuple)) or len(between) != 2:
            raise TypeError("RowCountBetween requires 'between' as a 2-tuple/list of [low, high]")
        low, high = between
        try:
            low_i = int(low)
            high_i = int(high)
        except Exception:
            raise TypeError(f"RowCountBetween bounds must be integers, got {between!r}")
        if low_i > high_i:
            raise ValueError(f"RowCountBetween lower bound must be <= upper bound, got {between!r}")

        params = {"between": [low_i, high_i], "inclusive": bool(inclusive)}
        super().__init__(name or f"row_count_between:{low_i}-{high_i}:{'incl' if inclusive else 'excl'}", params)

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        row_count = df.count()
        low, high = self.params["between"]
        inclusive = bool(self.params.get("inclusive", True))

        if inclusive:
            passed = (row_count >= low) and (row_count <= high)
        else:
            passed = (row_count > low) and (row_count < high)

        return {
            "passed": passed,
            "metrics": {
                "row_count": row_count,
                "bounds": [low, high],
                "inclusive": inclusive,
            },
        }
