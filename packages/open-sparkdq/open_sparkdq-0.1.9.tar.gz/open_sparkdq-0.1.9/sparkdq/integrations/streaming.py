from __future__ import annotations

from typing import Any, Callable, Optional
from datetime import datetime

from pyspark.sql import DataFrame

from sparkdq.core.runner import DQRunner
from sparkdq.core.models import DQSuite, Severity
from sparkdq.core.reporter import JSONReporter


def foreach_batch_runner(
    suite: DQSuite,
    reporter: Optional[JSONReporter] = None,
    output_dir: Optional[str] = None,
    stop_on: Severity = Severity.ERROR,
    on_report: Optional[Callable[[dict], None]] = None,
) -> Callable[[DataFrame, int], None]:
    """Create a foreachBatch callable that runs the DQ suite on each micro-batch.

    Args:
        suite: DQSuite to execute.
        reporter: JSONReporter to serialize results. If None, a default reporter is used.
        output_dir: Directory where per-batch JSON reports will be written. If None, no file write.
        stop_on: Severity threshold for fail-fast within a batch.
        on_report: Optional callback receiving the JSON report as dict per batch.

    Returns:
        A function with signature (batch_df, batch_id) to be used with DataStreamWriter.foreachBatch.
    """
    _reporter = reporter or JSONReporter(indent=2)

    def _run(batch_df: DataFrame, batch_id: int) -> None:
        runner = DQRunner(suite=suite, stop_on=stop_on)
        report = runner.run(batch_df)
        payload_str = _reporter.build(report)
        if output_dir:
            import os
            os.makedirs(output_dir, exist_ok=True)
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            path = os.path.join(output_dir, f"{suite.name}_batch_{batch_id}_{ts}.json")
            _reporter.write(report, path)
        if on_report:
            import json
            on_report(json.loads(payload_str))

    return _run


def start_stream_with_dq(
    df: DataFrame,
    suite: DQSuite,
    output_dir: str,
    reporter: Optional[JSONReporter] = None,
    trigger: str = "5 seconds",
    sink_format: str = "console",
    stop_on: Severity = Severity.ERROR,
) -> Any:
    """Start a streaming query that applies DQ via foreachBatch and writes reports.

    Args:
        df: Source streaming DataFrame.
        suite: DQSuite to run per micro-batch.
        output_dir: Directory to write JSON reports.
        reporter: Optional custom JSONReporter.
        trigger: Processing time trigger for the stream (e.g., '5 seconds').
        sink_format: Sink format for the query (default 'console').
        stop_on: Severity threshold for fail-fast within a batch.

    Returns:
        The active StreamingQuery.
    """
    fb = foreach_batch_runner(
        suite=suite,
        reporter=reporter,
        output_dir=output_dir,
        stop_on=stop_on,
    )
    query = (
        df.writeStream
        .outputMode("append")
               .format(sink_format)
        .trigger(processingTime=trigger)
        .foreachBatch(fb)
        .start()
    )
