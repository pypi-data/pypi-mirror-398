from __future__ import annotations

from typing import Any, Dict, List

from pyspark.sql import DataFrame, functions as F
from pyspark.sql.types import NumericType


class DataFrameProfiler:
    """Lightweight profiler for Spark DataFrames.

    Computes:
      - row_count
      - per-column null_count
      - numeric stats: min, max, mean, stddev, quantiles (p50, p90, p95, p99)
      - string/categorical: distinct_count, top_k (value, count)
    """

    def __init__(self, top_k: int = 10, quantiles: List[float] = None, relative_error: float = 0.01):
        self.top_k = top_k
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self.relative_error = relative_error

    def profile(self, df: DataFrame) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            'row_count': df.count(),
            'columns': {},
        }
        schema = df.schema
        # Precompute null counts via aggregation (one pass)
        null_aggs = [F.sum(F.col(f.name).isNull().cast('int')).alias(f"{f.name}_nulls") for f in schema]
        null_counts_row = df.agg(*null_aggs).collect()[0]
        nulls_map = {k.replace('_nulls', ''): int(v or 0) for k, v in null_counts_row.asDict().items()}

        for field in schema.fields:
            colname = field.name
            dtype = field.dataType
            col_info: Dict[str, Any] = {
                'type': dtype.simpleString(),
                'null_count': nulls_map.get(colname, 0),
            }

            if isinstance(dtype, NumericType):
                stats = df.select(
                    F.min(F.col(colname)).alias('min'),
                    F.max(F.col(colname)).alias('max'),
                    F.mean(F.col(colname)).alias('mean'),
                    F.stddev(F.col(colname)).alias('stddev'),
                ).collect()[0]
                qvals = df.stat.approxQuantile(colname, self.quantiles, self.relative_error)
                quant_map = {f"p{int(p*100)}": float(qvals[i]) for i, p in enumerate(self.quantiles)} if qvals else {}
                col_info.update({
                    'min': float(stats['min']) if stats['min'] is not None else None,
                    'max': float(stats['max']) if stats['max'] is not None else None,
                    'mean': float(stats['mean']) if stats['mean'] is not None else None,
                    'stddev': float(stats['stddev']) if stats['stddev'] is not None else None,
                    'quantiles': quant_map,
                })
            else:
                # Distinct count (exact; swap to approx_count_distinct for very large data)
                distinct_cnt = df.select(F.col(colname)).distinct().count()
                # Top-K values excluding nulls
                topk_df = (
                    df.filter(F.col(colname).isNotNull())
                      .groupBy(F.col(colname))
                      .agg(F.count(F.lit(1)).alias('cnt'))
                      .orderBy(F.col('cnt').desc(), F.col(colname).asc())
                      .limit(self.top_k)
                )
                projected = topk_df.select(F.col(colname).alias('value'), F.col('cnt').alias('count'))
                topk = [{'value': r['value'], 'count': int(r['count'])} for r in projected.collect()]
                col_info.update({
                    'distinct_count': int(distinct_cnt),
                    'top_k': topk,
                })

            res['columns'][colname] = col_info

        # 🔁 Return the profile dict
        return res
