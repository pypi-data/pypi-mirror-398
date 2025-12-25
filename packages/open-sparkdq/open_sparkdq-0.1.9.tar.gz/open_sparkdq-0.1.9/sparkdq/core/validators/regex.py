from __future__ import annotations

from typing import Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from sparkdq.core.validators.base import Validator


class RegexValidator(Validator):
    """
    Validates that a column's values match a given regular expression.

    Args:
        column: Column name to validate.
        pattern: Spark SQL regex pattern.
        allow_nulls: If False, NULLs are violations. Default True.
        full_match: If True, anchors ^pattern$ for full-string match. Default False.
        name: Optional validator name; defaults to f"regex:{column}".
    """

    def __init__(
        self,
        column: str,
        pattern: str,
        allow_nulls: bool = True,
        full_match: bool = False,
        name: str | None = None,
    ):
        if not column:
            raise TypeError("RegexValidator requires 'column'")
        if not isinstance(pattern, str) or pattern == "":
            raise TypeError("RegexValidator requires non-empty 'pattern'")

        params = {
            "column": column,
            "pattern": pattern,
            "allow_nulls": allow_nulls,
            "full_match": full_match,
        }
        super().__init__(name or f"regex:{column}", params)

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        c = self.params["column"]
        pattern = self.params["pattern"]
        full_match = bool(self.params.get("full_match", False))
        allow_nulls = bool(self.params.get("allow_nulls", True))

        final_pattern = f"^{pattern}$" if full_match else pattern

        non_match_filter = ~col(c).rlike(final_pattern)
        null_filter = col(c).isNull()

        total = df.count()
        non_matching_rows = df.filter(non_match_filter).count()
        null_rows = 0 if allow_nulls else df.filter(null_filter).count()
        violations = non_matching_rows + null_rows

        return {
            "passed": violations == 0,
            "metrics": {
                "violations": violations,
                "non_matching_rows": non_matching_rows,
                "null_rows": null_rows,
                "total": total,
                "pattern": final_pattern,
                "full_match": full_match,
                "allow_nulls": allow_nulls,
            },
        }
