import pytest
from pyspark.sql import SparkSession
from chispa import assert_df_equality

@pytest.fixture(scope="module")
def spark():
    spark = SparkSession.builder.appName("chispa").master("local[2]").getOrCreate()
    yield spark
    spark.stop()

def test_chispa_df_equality(spark):
    actual = spark.createDataFrame([("O1", 10.0), ("O2", 2.0)], ["order_id", "price"])
    expected = spark.createDataFrame([("O1", 10.0), ("O2", 2.0)], ["order_id", "price"])

    # strict compare: same schema, same order, same types
    assert_df_equality(actual, expected, ignore_row_order=False, ignore_column_order=False,)
