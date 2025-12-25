from __future__ import annotations

from typing import Dict, Any, Optional
from pyspark.sql import DataFrame
from pyspark.sql.functions import expr
from sparkdq.core.validators.base import Validator


class ExpressionValidator(Validator):
    """
    Validates a row-level boolean expression over the DataFrame.

    The expression must evaluate to a boolean per row. Rows where the expression
    evaluates to False (or NULL) are counted as violations.

    Ergonomic constructor:
        ExpressionValidator(expression: str, name: Optional[str] = None)

    Returns:
      {
        "passed": bool,
        "metrics": {
          "violations": int,
          "total": int,
          "expression": str
        }
      }
    """

    def __init__(self, expression: str, name: Optional[str] = None):
        if not isinstance(expression, str) or not expression.strip():
            raise TypeError("ExpressionValidator requires a non-empty 'expression' string")
        params = {"expression": expression.strip()}
        super().__init__(name or "expression", params)

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        expression_str = self.params["expression"]

        # Evaluate the expression: False or NULL rows are violations.
        # In Spark SQL, NULL is treated as unknown; explicitly treat it as a violation
        # by coalescing to False where needed.
        # violation_filter = NOT(expr) OR expr IS NULL
        violation_df = df.filter(f"NOT ({expression_str}) OR ({expression_str}) IS NULL")

        total = df.count()
        violations = violation_df.count()

        return {
            "passed": violations == 0,
            "metrics": {
                "violations": violations,
                "total": total,
                "expression": expression_str,
            },
        }
