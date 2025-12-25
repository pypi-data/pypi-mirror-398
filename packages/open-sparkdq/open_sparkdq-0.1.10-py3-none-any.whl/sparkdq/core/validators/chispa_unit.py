
from typing import Dict, Any, List
from pyspark.sql import DataFrame
from chispa.dataframe_comparer import assert_df_equality
from sparkdq.core.validators.base import Validator

class SchemaEqualsValidator(Validator):
    def run(self, df: DataFrame, **params) -> Dict[str, Any]:
        expected_cols: List[str] = params["expected_cols"]
        actual = df.columns
        passed = actual == expected_cols
        return {"passed": passed, "metrics": {"actual": actual, "expected": expected_cols}}

class DataFrameEqualsValidator(Validator):
    def run(self, df: DataFrame, **params) -> Dict[str, Any]:
        other_df: DataFrame = params["other_df"]
        try:
            assert_df_equality(df, other_df, ignore_row_order=True, ignore_column_order=False)
            return {"passed": True, "metrics": {}}
        except AssertionError as e:
            return {"passed": False, "metrics": {"diff": str(e)}}
