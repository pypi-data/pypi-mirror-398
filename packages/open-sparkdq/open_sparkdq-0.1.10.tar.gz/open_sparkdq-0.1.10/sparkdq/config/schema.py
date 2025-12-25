from __future__ import annotations
from typing import Any, Dict, List, Optional
import importlib

from sparkdq.core.models import DQSuite, DQCheck, Severity

from sparkdq.core.validators.not_null import NotNullValidator
from sparkdq.core.validators.uniqueness import UniquenessValidator
from sparkdq.core.validators.range import RangeValidator
from sparkdq.core.validators.regex import RegexValidator
from sparkdq.core.validators.expression import ExpressionValidator
from sparkdq.core.validators.dataframe import RowCountGreaterThan, RowCountBetween
from sparkdq.core.validators.function_validators import DQCheckValidator, UnitTestValidator


def _import_callable(fn_path: str):
    mod, fn = fn_path.rsplit(".", 1)
    return getattr(importlib.import_module(mod), fn)

def _sev(s: Optional[str]) -> Severity:
    """Map string severity to Severity enum (defaults to ERROR)."""
    if not s:
        return Severity.ERROR
    s_up = s.upper()
    return Severity.__members__.get(s_up, Severity.ERROR)

def _build_validator_from_check_dict(c: Dict[str, Any]):
    """
    Construct a validator instance from a type-based check dict.

    Supported shapes (examples):
      - {"type": "not_null", "params": {"column": "order_id"}}
      - {"type": "uniqueness", "params": {"columns": ["order_id"]}}
      - {"type": "regex", "params": {"column": "email", "pattern": "^[A-Za-z0-9._%+-]+@", "full_match": true, "allow_nulls": false}}
      - {"type": "row_count_gt", "params": {"value": 0}}
      - {"type": "row_count_between", "params": {"between": [10, 100], "inclusive": true}}
      - {"type": "between", "params": {"column": "amount", "between": [0, 10000], "inclusive": true}}
      - {"type": "gt|ge|lt|le|eq", "params": {"column": "amount", "value": 0}}
      - {"type": "range", "params": {"column": "amount", "ge": 0}}  # shorthand
      - {"type": "expression", "params": {"expression": "amount >= 0 AND amount <= 10000"}}
    """
    t = (c.get("type") or "").lower()
    params = c.get("params", {}) or {}
    col = c.get("column") or c.get("col") or params.get("column") or params.get("col")

    if t == "not_null":
        if not col:
            raise ValueError("not_null requires 'params.column'")
        return NotNullValidator(column=col)

    if t == "uniqueness":
        # Support either params.column (str) OR params.columns (list[str])
        columns_param = params.get("columns")
        column_param = col
        if columns_param and isinstance(columns_param, (list, tuple)) and len(columns_param) > 0:
            columns = [str(x) for x in columns_param]
        elif column_param:
            columns = [str(column_param)]
        else:
            raise ValueError("uniqueness requires 'params.column' (str) OR 'params.columns' (list[str])")
        return UniquenessValidator(columns=columns)

    if t == "regex":
        pattern = params.get("pattern")
        if not col or not isinstance(pattern, str) or pattern == "":
            raise ValueError("regex requires 'params.column' and non-empty 'params.pattern'")
        full_match = bool(params.get("full_match", False))
        allow_nulls = bool(params.get("allow_nulls", True))
        return RegexValidator(column=col, pattern=pattern, full_match=full_match, allow_nulls=allow_nulls)

    # Single-op range (explicit types)
    if t in {"gt", "ge", "lt", "le", "eq"}:
        if not col:
            raise ValueError(f"{t} requires 'params.column'")
        value = params.get("value")
        if value is None:
            raise ValueError(f"{t} requires 'params.value'")
        return RangeValidator(column=col, **{t: value})

    # Between range (explicit type)
    if t == "between":
        if not col:
            raise ValueError("between requires 'params.column'")
        between = params.get("between")
        if not isinstance(between, (list, tuple)) or len(between) != 2:
            raise ValueError("between requires 'params.between = [low, high]'")
        inclusive = bool(params.get("inclusive", True))
        return RangeValidator(column=col, between=tuple(between), inclusive=inclusive)

    # Shorthand umbrella: type="range" with one of gt/ge/lt/le/eq/ or between(+inclusive)
    if t == "range":
        if not col:
            raise ValueError("range requires 'params.column'")
        if "between" in params:
            between = params["between"]
            if not isinstance(between, (list, tuple)) or len(between) != 2:
                raise ValueError("range requires 'params.between = [low, high]' when using between")
            inclusive = bool(params.get("inclusive", True))
            return RangeValidator(column=col, between=tuple(between), inclusive=inclusive)
        for op in ("gt", "ge", "lt", "le", "eq"):
            if op in params:
                return RangeValidator(column=col, **{op: params[op]})
        raise ValueError("range requires one of params: gt|ge|lt|le|eq OR 'between' (with optional 'inclusive')")

    if t == "row_count_gt":
        value = params.get("value", params.get("threshold"))
        if value is None:
            raise ValueError("row_count_gt requires 'params.value' or 'params.threshold'")
        return RowCountGreaterThan(threshold=int(value))

    if t == "row_count_between":
        between = params.get("between")
        if not isinstance(between, (list, tuple)) or len(between) != 2:
            raise ValueError("row_count_between requires 'params.between = [low, high]'")
        inclusive = bool(params.get("inclusive", True))
        return RowCountBetween(between=(int(between[0]), int(between[1])), inclusive=inclusive)

    if t == "expression":
        expr_str = params.get("expression")
        if not isinstance(expr_str, str) or not expr_str.strip():
            raise ValueError("expression requires non-empty 'params.expression' string")
        return ExpressionValidator(expression=expr_str)
        
    
    if t == "dq_check":
        fn_path = params.get("fn")
        if not isinstance(fn_path, str) or not fn_path.strip():
            raise ValueError("function requires non-empty 'params.fn' (module.function)")
        callable_fn = _import_callable(fn_path)
        call_params = {k: v for k, v in params.items() if k != "fn"}
        return DQCheckValidator(
            name=c.get("name") or "dq_check",
            params=call_params,
            callable_fn=callable_fn,
            severity=c.get("severity")
        )

    if t == "unit_test":
        fn_path = params.get("fn")
        if not isinstance(fn_path, str) or not fn_path.strip():
            raise ValueError("unit_test requires non-empty 'params.fn' (module.function)")
        callable_fn = _import_callable(fn_path)
        call_params = {k: v for k, v in params.items() if k != "fn"}
        emit_metrics_on_pass = bool(params.get("emit_metrics_on_pass", False))  # <--

        return UnitTestValidator(
            name=c.get("name") or "unit_test",
            params=call_params,
            callable_fn=callable_fn,
            severity=c.get("severity"),
            emit_metrics_on_pass=emit_metrics_on_pass
        )


    raise ValueError(f"Unsupported validator type '{c.get('type')}'")


def to_suite(data: Dict[str, Any]) -> DQSuite:
    """
    Convert a YAML dict (already loaded) into a DQSuite model.

    Minimal expected structure:
      suite_name: "orders_dq"
      fail_fast: false
      checks:
        - name: "order_id_not_null"
          type: "not_null"
          params: { column: "order_id" }
          severity: "ERROR"
      per_column_checks:
        order_id:
          - name: "order_id_unique"
            type: "uniqueness"
            severity: "ERROR"
    """
    if not isinstance(data, dict):
        raise TypeError("to_suite expects a dict")

    name = data.get("suite") or data.get("name") or "suite"
    fail_fast = bool(data.get("fail_fast", False))

    checks: List[DQCheck] = []

    # Global checks
    for c in (data.get("checks", []) or []):
        cname = c.get("name") or c.get("type") or "check"
        severity = _sev(c.get("severity"))
        validator = _build_validator_from_check_dict(c)
        checks.append(DQCheck(name=cname, validator=validator, severity=severity))

    # Per-column checks
    for col, items in (data.get("per_column_checks", {}) or {}).items():
        if not isinstance(items, list):
            raise ValueError(f"per_column_checks['{col}'] must be a list")
        for c in items:
            # Ensure column present in params for per-column items
            c = {**c}
            params = c.get("params", {}) or {}
            if not any(k in c for k in ("column", "col")) and not any(k in params for k in ("column", "col")):
                params["column"] = col
                c["params"] = params

            cname = c.get("name") or c.get("type") or f"{col}_check"
            severity = _sev(c.get("severity"))
            validator = _build_validator_from_check_dict(c)
            checks.append(DQCheck(name=cname, validator=validator, severity=severity))

    return DQSuite(name=name, checks=checks, fail_fast=fail_fast)
