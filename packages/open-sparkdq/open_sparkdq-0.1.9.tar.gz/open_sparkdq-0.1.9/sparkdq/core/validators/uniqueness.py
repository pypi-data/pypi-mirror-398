from __future__ import annotations

from typing import Dict, Any, List, Optional
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count
from sparkdq.core.validators.base import Validator


class UniquenessValidator(Validator):
    """
    Validates that the given column(s) have unique values across all rows.

    Ergonomic constructor:
        UniquenessValidator(
            columns: Optional[List[str]] = None,
            column: Optional[str] = None,
            name: Optional[str] = None,
        )

    Usage:
        UniquenessValidator(columns=["order_id"])
        UniquenessValidator(column="order_id")

    Metrics:
      - duplicate_groups: number of distinct key groups with count > 1
      - duplicate_rows: sum of (count - 1) across all groups with count > 1
      - total: total rows evaluated
    """

    def __init__(
        self,
        columns: Optional[List[str]] = None,
        column: Optional[str] = None,
        name: Optional[str] = None,
    ):
        # Normalize input: allow either a single `column` or a list `columns`
        if columns is None and column is None:
            raise TypeError("UniquenessValidator requires 'columns' or 'column'")

        cols: List[str]
        if columns is not None:
            if not isinstance(columns, (list, tuple)) or len(columns) == 0:
                raise TypeError("UniquenessValidator 'columns' must be a non-empty list/tuple of strings")
            cols = [str(c) for c in columns]
        else:
            cols = [str(column)]

        params = {"columns": cols}
        # Set a readable default name (e.g., uniqueness:order_id or uniqueness:colA,colB)
        default_name = f"uniqueness:{','.join(cols)}"
        super().__init__(name or default_name, params)

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        cols: List[str] = self.params["columns"]
        if not cols:
            raise ValueError("UniquenessValidator misconfigured: empty 'columns'")

        # Group by the key columns and count occurrences
        grouped = df.groupBy(*[col(c) for c in cols]).agg(count("*").alias("cnt"))

        # Duplicate groups are those with cnt > 1
        duplicate_groups_df = grouped.filter(col("cnt") > 1)

        # Compute metrics
        total = df.count()
        duplicate_groups = duplicate_groups_df.count()  # number of distinct key groups with duplicates
        # duplicate_rows = sum(cnt - 1) over duplicate groups
        duplicate_rows = duplicate_groups_df.selectExpr("CAST(cnt - 1 AS LONG) AS extras") \
                                            .groupBy() \
                                            .sum("extras") \
                                            .collect()[0][0] if duplicate_groups > 0 else 0
        # Spark returns None if sum over empty set—guard it to 0
        duplicate_rows = int(duplicate_rows or 0)

        passed = (duplicate_groups == 0)

        return {
            "passed": passed,
            "metrics": {
                "duplicate_groups": duplicate_groups,
                "duplicate_rows": duplicate_rows,
                "total": total,
            },
        }
