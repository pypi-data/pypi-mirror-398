import os 
os.environ.setdefault("SPARK_VERSION", "3.3")

import pytest
pydeequ = pytest.importorskip("pydeequ", reason="pydeequ not installed")

from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import VerificationSuite, VerificationResult
from sparkdq.core.spark import _make_spark


@pytest.fixture(scope="module")
def spark():
    """
    Create Spark via the project's central factory (_make_spark).
    If Deequ classes are missing, skip the module gracefully.
    """
    try:
        spark = _make_spark(app_name="pydeequ", master="local[2]")
    except RuntimeError as e:
        # _make_spark already performs Deequ classpath check and errors if missing
        pytest.skip(
            "Deequ classes not on classpath; provide deequ_2.12-<version>.jar via DEEQU_JAR_PATH or spark.jars.\n"
            f"Cause: {e}"
        )
        return

    yield spark
    spark.stop()


@pytest.mark.pydeequ
def test_pydeequ_completeness_and_uniqueness(spark):
    # Extra safety: if for some reason Deequ is not available, skip the test
    try:
        _ = spark._jvm.com.amazon.deequ.checks.CheckLevel.Error()
    except Exception:
        pytest.skip("Deequ classes not on classpath; provide deequ_2.12-<version>.jar via spark.jars")

    df = spark.createDataFrame([
        {"order_id": "O1", "status": "NEW"},
        {"order_id": None, "status": "SHIPPED"},
        {"order_id": "O2", "status": "NEW"},
        {"order_id": "O2", "status": "NEW"},
    ])

    check = (
        Check(spark, CheckLevel.Error, "dq")
        .isComplete("order_id")
        .isUnique("order_id")
        .isContainedIn("status", ["NEW", "SHIPPED", "DELIVERED", "CANCELLED"])
    )

    result = VerificationSuite(spark).onData(df).addCheck(check).run()
    res_df = VerificationResult.checkResultsAsDataFrame(spark, result)
    rows = res_df.collect()

    def find_status(predicate) -> str:
        for row in rows:
            constraint_str = row["constraint"]
            if predicate(constraint_str.lower()):
                return row["constraint_status"]
        raise AssertionError(
            "Expected constraint not found in verification results.\n"
            f"Available: {[r['constraint'] for r in rows]}"
        )

    completeness_status = find_status(lambda s: "completeness" in s and "order_id" in s)
    uniqueness_status = find_status(lambda s: "uniqueness" in s and "order_id" in s)
    containment_status = find_status(lambda s: "compliance" in s and "status" in s)

    assert completeness_status == "Failure"
    assert uniqueness_status == "Failure"
    assert containment_status == "Success" or ("Success" in containment_status)
