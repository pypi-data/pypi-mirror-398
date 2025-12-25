
from __future__ import annotations

from pyspark.sql import DataFrame
from sparkdq.core.registry import dq_check, unit_test

@dq_check("not_null_col")
def not_null_col(df: DataFrame, col: str, **kwargs):
    null_count = df.filter(f"{col} IS NULL").count()
    return {"passed": null_count == 0, "metrics": {"null_count": null_count}}

@dq_check("range_check")
def range_check(df: DataFrame, col: str, min: float, max: float, **kwargs):
    out_of_range = df.filter((df[col] < float(min)) | (df[col] > float(max))).count()
    return {"passed": out_of_range == 0, "metrics": {"out_of_range": out_of_range, "bounds": [min, max]}}

@unit_test("schema_equals")
def schema_equals(df: DataFrame, expected_cols, **kwargs):
    actual = df.columns
    assert actual == list(expected_cols), f"Schema mismatch. expected={expected_cols}, actual={actual}"
