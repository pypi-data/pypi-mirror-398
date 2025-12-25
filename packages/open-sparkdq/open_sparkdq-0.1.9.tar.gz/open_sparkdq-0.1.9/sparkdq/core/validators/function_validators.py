
from __future__ import annotations
from typing import Dict, Any, Callable, Tuple
from pyspark.sql import DataFrame
from sparkdq.core.validators.base import Validator

def _normalize_fn_output(out: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Normalize user function output to (passed: bool, metrics: dict).
    Accepted shapes:
      - dict: {"passed": bool, "metrics": {...}}  (preferred)
      - bool: True/False (metrics = {})
      - tuple: (passed, metrics_dict)
      - None: treated as False, metrics = {}
    """
    if isinstance(out, dict):
        passed = bool(out.get("passed", False))
        metrics = out.get("metrics") or out.get("details") or {}
        if not isinstance(metrics, dict):
            metrics = {"details": metrics}
        return passed, metrics
    if isinstance(out, bool):
        return out, {}
    if isinstance(out, tuple) and len(out) == 2:
        p, m = out
        return bool(p), (m if isinstance(m, dict) else {"details": m})
    # fallback
    return False, {}

class DQCheckValidator(Validator):
    def __init__(self, name: str, params: Dict[str, Any], callable_fn: Callable, severity=None):
        super().__init__(name=name, params=params, severity=severity)
        self._fn = callable_fn

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        try:
            out = self._fn(df, **(self.params or {}))
            passed, metrics = _normalize_fn_output(out)
            return {"passed": passed, "metrics": metrics}
        except AssertionError as e:
            # allow users to assert in dq_check as well
            return {"passed": False, "metrics": {"error": str(e)}}
        except Exception as e:
            # don't break the run; return a failed check with error
            return {"passed": False, "metrics": {"error": f"{type(e).__name__}: {e}"}}


class UnitTestValidator(Validator):
    def __init__(
        self,
        name: str,
        params: Dict[str, Any],
        callable_fn: Callable,
        severity=None,
        emit_metrics_on_pass: bool = False,
        pass_message_key: str = "info",
        pass_message_value: str = "unit_test passed"
    ):
        """
        UnitTestValidator runs a user-provided callable as a 'unit test'.
        - If callable raises AssertionError/Exception -> FAIL with 'error' metrics.
        - If callable returns boolean -> PASS/FAIL, no metrics on PASS (unless opt-in).
        - If callable returns (bool, metrics) -> use both.
        - If callable returns {'passed': bool, 'metrics': dict} -> use both.
        - If emit_metrics_on_pass=True and no metrics were returned, we add a small, JSON-safe
          message under `metrics[pass_message_key] = pass_message_value`.
        """
        super().__init__(name=name, params=params, severity=severity)
        self._fn = callable_fn
        self._emit_metrics_on_pass = bool(emit_metrics_on_pass)
        self._pass_message_key = str(pass_message_key)
        self._pass_message_value = str(pass_message_value)

    def _normalize_result(self, result: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Convert various callable return types into (passed: bool, metrics: dict).
        Accepted forms:
          - True/False
          - (True/False, metrics_dict)
          - {"passed": True/False, "metrics": {...}}
          - None -> treated as PASS with empty metrics (legacy assertion style)
        """
        passed = True
        metrics: Dict[str, Any] = {}

        if isinstance(result, dict):
            passed = bool(result.get("passed", True))
            maybe_metrics = result.get("metrics", {})
            metrics = maybe_metrics if isinstance(maybe_metrics, dict) else {}
        elif isinstance(result, tuple) and len(result) == 2:
            passed = bool(result[0])
            metrics = result[1] if isinstance(result[1], dict) else {}
        elif isinstance(result, bool):
            passed = result
            metrics = {}
        elif result is None:
            passed = True
            metrics = {}
        else:
            passed = True
            metrics = {"note": f"Callable returned unexpected type '{type(result).__name__}'"}

        return passed, metrics

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        try:
            # Execute the unit test callable with provided params
            result = self._fn(df, **(self.params or {}))
            passed, metrics = self._normalize_result(result)

            # Always return 'metrics' key; optionally add a message on PASS
            if passed and self._emit_metrics_on_pass and (not metrics):
                metrics = {self._pass_message_key: self._pass_message_value}

            return {"passed": bool(passed), "metrics": metrics}

        except AssertionError as e:
            # A test assertion failed; include the error string
            return {"passed": False, "metrics": {"error": str(e)}}
        except Exception as e:
            # Any other exception -> FAIL with typed error message
            return {"passed": False, "metrics": {"error": f"{type(e).__name__}: {e}"}}
