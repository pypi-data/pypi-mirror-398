
import pytest
from pyspark.sql import SparkSession

from sparkdq.core.models import DQSuite, DQCheck, Severity
from sparkdq.core.runner import DQRunner
from sparkdq.core.validators import NotNullValidator, RangeValidator


@pytest.fixture(scope="module")
def spark():
    spark = SparkSession.builder.appName("sparkdq-runner-tests").master("local[2]").getOrCreate()
    yield spark
    spark.stop()


def test_runner_report_counts(spark):
    data = [
        {"order_id": "O1", "price": 10.0},
        {"order_id": None, "price": -1.0},
        {"order_id": "O3", "price": 2.0},
    ]
    df = spark.createDataFrame(data)

    suite = DQSuite(
        name="orders_dq",
        fail_fast=False,
        checks=[
            DQCheck(name="order_id_not_null", validator=NotNullValidator("order_id"), severity=Severity.ERROR),
            DQCheck(name="price_non_negative", validator=RangeValidator("price", ge=0), severity=Severity.ERROR),
        ]
    )

    report = DQRunner(suite).run(df)
    summary = report.summary
    assert summary['total_checks'] == 2
    assert summary['failed'] == 2
