
# sparkdq/core/runner.py
from __future__ import annotations

from time import perf_counter
from typing import Any, List

from datetime import datetime

from sparkdq.core.models import DQSuite, DQCheck, DQResult, DQReport, Severity, Status


class DQRunner:
    """Orchestrates execution of a DQSuite over a Spark DataFrame.

    Example:
        runner = DQRunner(suite)
        report = runner.run(df)
    """

    def __init__(self, suite: DQSuite, stop_on: Severity = Severity.ERROR):
        self.suite = suite
        self.stop_on = stop_on

    def _execute_check(self, df: Any, check: DQCheck) -> DQResult:
        start = perf_counter()
        # Use millisecond precision to aid correlation with Spark logs/OTel
        started_at = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        try:
            outcome = check.validator.validate(df)  # validator binds params at construction
            # Normalize outcome keys: prefer 'metrics', fallback to 'details'
            metrics = outcome.get("metrics")
            if metrics is None and "details" in outcome:
                metrics = outcome.get("details") or {}
            passed = bool(outcome.get("passed", False))
            status = Status.PASS if passed else Status.FAIL
            err = None
        except Exception as exc:  # Broad capture to include Spark/pydeequ/chispa errors
            passed = False
            status = Status.ERROR
            metrics = {}
            err = f"{type(exc).__name__}: {exc}"
        duration = int((perf_counter() - start) * 1000)
        return DQResult(
            check_name=check.name,
            status=status,
            severity=check.severity,
            passed=passed,
            metrics=metrics or {},
            error=err,
            duration_ms=duration,
            started_at=started_at,
        )

    def run(self, df: Any) -> DQReport:
        results: List[DQResult] = []
        for check in self.suite.checks:
            res = self._execute_check(df, check)
            results.append(res)
            # Fail-fast handling: stop when a failing/errored check meets severity threshold
            if (
                self.suite.fail_fast
                and res.status in (Status.FAIL, Status.ERROR)
                and check.severity.value >= self.stop_on.value
            ):
                break
        return DQReport(suite_name=self.suite.name, results=results)


# --- adapter functions for CLI and programmatic use ---

from typing import Optional, Dict
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType


def _build_dummy_df_for_suite(spark: SparkSession, suite: DQSuite) -> DataFrame:
    """
    Build a single-row DataFrame with columns referenced by the suite checks,
    using values that should make the example validators PASS.

    This enables CLI smoke tests to run without requiring the user to provide a data source.
    """
    referenced_cols: set[str] = set()

    for chk in suite.checks:
        params = getattr(chk.validator, "params", {}) or {}

        # singular column keys
        col_name = params.get("column") or params.get("col")
        if col_name:
            referenced_cols.add(str(col_name))

        # multi-column uniqueness keys
        cols = params.get("columns")
        if isinstance(cols, (list, tuple)):
            for c in cols:
                referenced_cols.add(str(c))

    # Default row aimed to satisfy examples/suites/orders_dq.yml checks
    default_row: Dict[str, object] = {
        "order_id": "O1",
        "customer_id": "C1",
        "price": 1.0,
        "quantity": 1,
        "status": "NEW",
        "total_amount": 1.0,  # equals price * quantity
    }

    # Ensure every referenced column exists
    for c in referenced_cols:
        default_row.setdefault(c, 1)

    # Build a permissive schema (you can tighten types later if desired)
    fields: list[StructField] = []
    for k, v in default_row.items():
        if isinstance(v, int):
            fields.append(StructField(k, IntegerType(), True))
        elif isinstance(v, float):
            fields.append(StructField(k, DoubleType(), True))
        else:
            fields.append(StructField(k, StringType(), True))
    schema = StructType(fields)

    return spark.createDataFrame([default_row], schema=schema)


def run_suite(suite: DQSuite, spark: SparkSession, df: Optional[DataFrame] = None) -> Dict[str, object]:
    """
    Execute the provided DQSuite over a DataFrame (or a dummy one when None),
    returning a structured summary dictionary suitable for CLI / reporter output.

    Returns:
        {
          "suite_name": str,
          "fail_fast": bool,
          "any_failed": bool,
          "results": [
            {
              "name": str,
              "severity": str,
              "status": "PASS" | "FAIL" | "ERROR",
              "passed": bool,
              "metrics": dict,
              "error": Optional[str],
              "duration_ms": int,
              "started_at": str
            }, ...
          ]
        }
    """
    if df is None:
        df = _build_dummy_df_for_suite(spark, suite)

    runner = DQRunner(suite)
    report = runner.run(df)

    # Aggregate and normalize
    any_failed = any(r.status in (Status.FAIL, Status.ERROR) for r in report.results)

    results = []
    for r in report.results:
        results.append({
            "name": r.check_name,
            "severity": r.severity.name if hasattr(r.severity, "name") else str(r.severity),
            "status": r.status.name if hasattr(r.status, "name") else str(r.status),
            "passed": bool(r.passed),
            "metrics": r.metrics or {},
            "error": r.error,
            "duration_ms": int(getattr(r, "duration_ms", 0)),
            "started_at": getattr(r, "started_at", None),
        })

    return {
        "suite_name": report.suite_name,
        "fail_fast": bool(getattr(suite, "fail_fast", False)),
        "any_failed": any_failed,
        "results": results,
    }
