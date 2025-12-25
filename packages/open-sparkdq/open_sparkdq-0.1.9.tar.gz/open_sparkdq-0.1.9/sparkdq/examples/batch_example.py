
from pyspark.sql import SparkSession
from sparkdq.config.loader import load_suite
from sparkdq.config.schema import to_suite
from sparkdq.core.runner import run_suite
from sparkdq.core.reporter import to_json
from sparkdq.core.spark import _make_spark
from sparkdq.config.env import resolve_deequ_jar



def main():
    
    spark_version, deequ_jar = resolve_deequ_jar()

    spark = _make_spark("sparkdq-example")
    
    try:
        suite_dict = load_suite("open_spark_dlh_dq.yml")  #examples/suites/orders_dq.yml
        suite = to_suite(suite_dict)

        # Sample data
        data = [
            {"order_id": "O1", "customer_id": "C1", "price": 10.0, "quantity": 2, "total_amount": 20.0, "status": "NEW"},
            {"order_id": "O2", "customer_id": "C2", "price": 5.5,  "quantity": 1, "total_amount": 5.5,  "status": "SHIPPED"},
            {"order_id": "O3", "customer_id": None, "price": 12.0, "quantity": 3, "total_amount": 36.0, "status": "DELIVERED"},
            {"order_id": "O2", "customer_id": "C4", "price": -1.0, "quantity": 1, "total_amount": -1.0, "status": "CANCELLED"},
        ]
        df = spark.createDataFrame(data)

        # Load suite from YAML
        suite_dict = load_suite("examples/suites/orders_dq.yml")
        suite = to_suite(suite_dict)
        # Run DQ
        report = run_suite(suite, spark, df)

        # Also show in console
        print(to_json(report))
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
