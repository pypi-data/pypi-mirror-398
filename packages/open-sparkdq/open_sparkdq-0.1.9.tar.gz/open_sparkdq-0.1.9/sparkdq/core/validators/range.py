from __future__ import annotations

from typing import Dict, Any, Optional, Tuple
from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from sparkdq.core.validators.base import Validator


class RangeValidator(Validator):
    """
    Validates numeric ranges based on a predicate applied to a column.

    Ergonomic constructor:
        RangeValidator(
            column: str,
            *,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            eq: Optional[float] = None,
            between: Optional[Tuple[float, float]] = None,
            inclusive: bool = True,
        )

    Rules:
      - Provide exactly ONE of gt/ge/lt/le/eq OR 'between'.
      - For 'between', you can set inclusive=(True|False).

    validate() returns:
      {
        "passed": bool,
        "metrics": {
          "out_of_range_rows": int,  # number of rows violating the predicate
          "total": int,              # total rows evaluated
          "predicate": str,          # human-readable predicate description
          "bounds": [low, high] | value,  # the threshold(s) used
          "inclusive": bool          # only present for 'between'
        }
      }
    """

    def __init__(
        self,
        column: str,
        *,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        eq: Optional[float] = None,
        between: Optional[Tuple[float, float]] = None,
        inclusive: bool = True,
    ):
        if not column:
            raise TypeError("RangeValidator requires 'column'")

        # Determine which predicate is specified
        single_ops = [(name, val) for name, val in [
            ("gt", gt), ("ge", ge), ("lt", lt), ("le", le), ("eq", eq)
        ] if val is not None]

        # Validate predicate exclusivity
        if between is not None and single_ops:
            raise ValueError("Provide either one of gt/ge/lt/le/eq OR 'between', not both")
        if between is None and len(single_ops) != 1:
            raise ValueError("Provide exactly one of gt/ge/lt/le/eq OR 'between'")

        # Build params
        if between is not None:
            low, high = self._require_between(between)
            params = {
                "column": column,
                "op": "between",
                "between": [low, high],
                "inclusive": bool(inclusive),
            }
        else:
            op, value = single_ops[0]
            value_num = self._require_value(value)
            params = {
                "column": column,
                "op": op,
                "value": value_num,
            }

        super().__init__(name=f"range:{column}", params=params)

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        c = self.params.get("column") or self.params.get("col")
        op = (self.params.get("op") or "").lower()
        if c is None or op not in {"gt", "ge", "lt", "le", "eq", "between"}:
            raise ValueError("RangeValidator misconfigured params")

        # Build violation filter and human-readable predicate description
        if op == "between":
            low, high = self._require_between(self.params.get("between"))
            inclusive = bool(self.params.get("inclusive", True))
            if inclusive:
                violation_filter = (col(c) < low) | (col(c) > high)
                predicate_desc = f"{c} in [{low}, {high}]"
            else:
                violation_filter = (col(c) <= low) | (col(c) >= high)
                predicate_desc = f"{c} in ({low}, {high})"
            bounds_desc = [low, high]
        else:
            value = self._require_value(self.params.get("value"))
            if op == "gt":
                violation_filter = col(c) <= value
                predicate_desc = f"{c} > {value}"
            elif op == "ge":
                violation_filter = col(c) < value
                predicate_desc = f"{c} >= {value}"
            elif op == "lt":
                violation_filter = col(c) >= value
                predicate_desc = f"{c} < {value}"
            elif op == "le":
                violation_filter = col(c) > value
                predicate_desc = f"{c} <= {value}"
            elif op == "eq":
                violation_filter = col(c) != value
                predicate_desc = f"{c} == {value}"
            else:
                raise ValueError(f"Unsupported op '{op}'")
            bounds_desc = value

        total = df.count()
        out_of_range_rows = df.filter(violation_filter).count()

        metrics: Dict[str, Any] = {
            "out_of_range_rows": out_of_range_rows,
            "total": total,
            "predicate": predicate_desc,
            "bounds": bounds_desc,
        }
        if op == "between":
            metrics["inclusive"] = bool(self.params.get("inclusive", True))

        return {"passed": out_of_range_rows == 0, "metrics": metrics}

    @staticmethod
    def _require_value(v: Optional[Any]) -> float:
        if v is None:
            raise ValueError("RangeValidator requires 'value' for op gt/ge/lt/le/eq")
        try:
            return float(v)
        except Exception:
            raise ValueError(f"RangeValidator 'value' must be numeric, got {v!r}")

    @staticmethod
    def _require_between(b: Optional[Any]) -> Tuple[float, float]:
        if not isinstance(b, (list, tuple)) or len(b) != 2:
            raise ValueError("RangeValidator requires 'between' as [low, high]")
        low, high = b
        try:
            return float(low), float(high)
        except Exception:
            raise ValueError(f"RangeValidator 'between' must be numeric bounds, got {b!r}")
