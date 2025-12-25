import pytest
from pyspark.sql import SparkSession
from sparkdq.core.validators import (
    NotNullValidator, RegexValidator, RangeValidator,
    UniquenessValidator, RowCountGreaterThan, RowCountBetween,
    ExpressionValidator
)

@pytest.fixture(scope="module")
def spark():
    spark = SparkSession.builder.appName("contracts").master("local[2]").getOrCreate()
    yield spark
    spark.stop()

def test_metric_keys(spark):
    df = spark.createDataFrame([{"a": 1, "b": "X"}, {"a": None, "b": "Y"}])

    v = NotNullValidator(column="a").validate(df)
    assert set(v["metrics"].keys()) == {"null_or_blank_rows", "total"}

    v = RegexValidator(column="b", pattern="(X|Z)", allow_nulls=False, full_match=True).validate(df)
    assert {"non_matching_rows", "null_rows", "violations", "total", "pattern", "full_match", "allow_nulls"} <= set(v["metrics"].keys())

    v = RangeValidator(column="a", ge=0).validate(df)
    assert {"out_of_range_rows", "total", "predicate", "bounds"} <= set(v["metrics"].keys())

    v = UniquenessValidator(columns=["b"]).validate(df)
    assert {"duplicate_groups", "duplicate_rows", "total"} <= set(v["metrics"].keys())

    v = RowCountGreaterThan(threshold=0).validate(df)
    assert {"row_count", "threshold"} <= set(v["metrics"].keys())

    v = RowCountBetween(between=(0, 10)).validate(df)
    assert {"row_count", "bounds", "inclusive"} <= set(v["metrics"].keys())
