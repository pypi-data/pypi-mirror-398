
from typing import Dict, Any
from pyspark.sql import DataFrame, SparkSession
from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import VerificationSuite, VerificationResult
from sparkdq.core.validators.base import Validator
from sparkdq.core.models import Severity

def _level(sev: Severity) -> CheckLevel:
    # Map ERROR/CRITICAL -> Error; INFO/WARN -> Warning
    if sev in (Severity.ERROR, Severity.CRITICAL):
        return CheckLevel.Error
    return CheckLevel.Warning

def _verify(spark: SparkSession, df: DataFrame, check: Check) -> Dict[str, Any]:
    v = VerificationSuite(spark).onData(df).addCheck(check).run()
    res = VerificationResult.checkResultsAsJson(spark, v)
    passed = all(
        c["constraint_status"] == "Success"
        for check in res.get("check_results", [])
        for c in check.get("constraint_results", [])
    )
    return {"passed": passed, "metrics": {"deequ": res}}

class NotNullValidator(Validator):
    def run(self, df: DataFrame, **params) -> Dict[str, Any]:
        col = params["col"]
        spark = df.sql_ctx.sparkSession
        check = Check(spark, _level(self.severity), self.name).isComplete(col)
        return _verify(spark, df, check)

class UniqueValidator(Validator):
    def run(self, df: DataFrame, **params) -> Dict[str, Any]:
        col = params["col"]
        spark = df.sql_ctx.sparkSession
        check = Check(spark, _level(self.severity), self.name).isUnique(col)
        return _verify(spark, df, check)

class RowCountGtValidator(Validator):
    def run(self, df: DataFrame, **params) -> Dict[str, Any]:
        value = int(params["value"])
        spark = df.sql_ctx.sparkSession
        check = Check(spark, _level(self.severity), self.name).hasSize(lambda s: s > value)
        return _verify(spark, df, check)

class BetweenValidator(Validator):
    def run(self, df: DataFrame, **params) -> Dict[str, Any]:
        col = params["column"]
        low, high = params["between"]
        inclusive = bool(params.get("inclusive", True))
        spark = df.sql_ctx.sparkSession
        check = Check(spark, _level(self.severity), self.name).isContainedIn(col, low, high, includeBoundaries=inclusive)
        return _verify(spark, df, check)
