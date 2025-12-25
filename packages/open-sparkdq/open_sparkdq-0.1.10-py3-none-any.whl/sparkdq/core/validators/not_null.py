
from __future__ import annotations

from typing import Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, trim
from sparkdq.core.validators.base import Validator

class NotNullValidator(Validator):
    """
    Validates that a column has no NULLs or blank strings.
    Metrics:
      - null_or_blank_rows: number of rows where value is NULL or ''
      - total: total rows evaluated
    """

    def __init__(self, column: str, name: str | None = None):
        if not column:
            raise TypeError("NotNullValidator requires 'column'")
        super().__init__(name or f"not_null:{column}", {"column": column})

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        c = self.params["column"]

        # Treat NULL or empty/blank strings as violations
        violation_filter = col(c).isNull() | (trim(col(c)) == "")

        total = df.count()
        null_or_blank_rows = df.filter(violation_filter).count()

        return {
            "passed": null_or_blank_rows == 0,
            "metrics": {
                "null_or_blank_rows": null_or_blank_rows,
                "total": total,  # <-- canonical key
            },
        }
