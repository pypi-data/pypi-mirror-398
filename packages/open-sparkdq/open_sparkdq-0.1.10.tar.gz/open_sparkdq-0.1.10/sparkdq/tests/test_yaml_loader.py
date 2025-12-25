
import pytest
from pyspark.sql import SparkSession

from sparkdq.config.loader import load_suite
from sparkdq.config.schema import to_suite


@pytest.fixture(scope="module")
def spark():
    spark = (
        SparkSession.builder
        .appName("sparkdq-yaml-tests")
        .master("local[2]")
        .getOrCreate()
    )
    yield spark
    spark.stop()


def test_yaml_to_suite():
    # Load the example YAML as a dict
    suite_dict = load_suite("examples/suites/orders_dq.yml")
    assert isinstance(suite_dict, dict), "YAML should load into a dict"

    # Convert dict -> DQSuite
    suite = to_suite(suite_dict)
    assert suite.name == "orders_dq"

    # Optional sanity: suite should have at least one check
    assert len(suite.checks) > 0, "Suite must contain at least one DQ check"
