
import pytest
from pyspark.sql import SparkSession

from sparkdq.core.validators import (
    NotNullValidator,
    RangeValidator,
    RegexValidator,
    UniquenessValidator,
    RowCountGreaterThan,
)


@pytest.fixture(scope="module")
def spark():
    spark = SparkSession.builder.appName("sparkdq-tests").master("local[2]").getOrCreate()
    yield spark
    spark.stop()


def test_not_null_and_regex(spark):
    data = [
        {"order_id": "O1", "status": "NEW"},
        {"order_id": None, "status": "INVALID"},
    ]
    df = spark.createDataFrame(data)
    nn = NotNullValidator(column="order_id")
    res_nn = nn.validate(df)
    assert res_nn['passed'] is False
    assert res_nn['metrics']['null_or_blank_rows'] == 1

    regex = RegexValidator(column="status", pattern="(NEW|SHIPPED|DELIVERED|CANCELLED)", allow_nulls=False)
    res_rgx = regex.validate(df)
    assert res_rgx['passed'] is False
    assert res_rgx['metrics']['non_matching_rows'] == 1


def test_range_and_uniqueness(spark):
    data = [
        {"order_id": "O1", "price": 10.0},
        {"order_id": "O2", "price": -1.0},
        {"order_id": "O2", "price": 2.0},
    ]
    df = spark.createDataFrame(data)
    rng = RangeValidator(column="price", ge=0)
    res_rng = rng.validate(df)
    assert res_rng['passed'] is False
    assert res_rng['metrics']['out_of_range_rows'] == 1

    uniq = UniquenessValidator(columns=["order_id"])
    res_uniq = uniq.validate(df)
    assert res_uniq['passed'] is False
    assert res_uniq['metrics']['duplicate_groups'] == 1
    assert res_uniq['metrics']['duplicate_rows'] == 1


def test_row_count_gt(spark):
    df = spark.createDataFrame([{"x": 1}, {"x": 2}])
    rc = RowCountGreaterThan(threshold=1)
    res = rc.validate(df)
    assert res['passed'] is True
