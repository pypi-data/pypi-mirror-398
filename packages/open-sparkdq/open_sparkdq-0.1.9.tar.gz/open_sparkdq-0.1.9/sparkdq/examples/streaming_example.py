from pyspark.sql import SparkSession
from sparkdq.core.runner import DQRunner
from sparkdq.core.reporter import JSONReporter
from sparkdq.config.loader import load_yaml
from sparkdq.config.schema import suite_from_dict


def run_dq_on_batch(batch_df, batch_id, suite, output_dir="examples/stream_reports"):
    # Execute DQ on the micro-batch
    runner = DQRunner(suite)
    report = runner.run(batch_df)

    # Write per-batch JSON
    path = f"{output_dir}/orders_dq_report_batch_{batch_id}.json}"
    JSONReporter(indent=2).write(report, path)
    print(f"Wrote DQ report to {path}")


def main():
    spark = (
        SparkSession.builder
        .appName("sparkdq-streaming-example")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Prepare suite
    suite_dict = load_yaml("examples/suites/orders_dq.yml")
    suite = suite_from_dict(suite_dict)

    # Example streaming source (replace with your source)
    # Here we use a rate stream and transform it to mimic orders
    rate_df = spark.readStream.format("rate").option("rowsPerSecond", 5).load()
    orders_df = rate_df.selectExpr(
        "CAST(value AS string) as order_id",
        "CAST(value % 3 AS string) as customer_id",
        "CAST((value % 10) - 3 AS double) as price",
        "CAST((value % 5) + 1 AS int) as quantity",
        "CAST(((value % 10) - 3) * ((value % 5) + 1) AS double) as total_amount",
        "CASE WHEN value % 4 = 0 THEN 'NEW' WHEN value % 4 = 1 THEN 'SHIPPED' WHEN value % 4 = 2 THEN 'DELIVERED' ELSE 'CANCELLED' END as status"
    )

    # Ensure output dir exists
    import os
    os.makedirs("examples/stream_reports", exist_ok=True)

    # Run DQ per micro-batch via foreachBatch
    query = (
        orders_df.writeStream
        .outputMode("append")
        .format("console")
        .trigger(processingTime="5 seconds")
        .foreachBatch(lambda df, bid: run_dq_on_batch(df, bid, suite))
        .start()
    )

    print("Streaming query started. Press Ctrl+C to stop.")
    query.awaitTermination()


if __name__ == "__main__":
    main()