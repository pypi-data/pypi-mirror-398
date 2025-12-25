
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable

from importlib import import_module
from importlib.metadata import entry_points

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType

# SparkDQ internals
from sparkdq.config.env import resolve_deequ_jar
from sparkdq.core.spark import _make_spark
from sparkdq.config.loader import load_suite
from sparkdq.config.schema import to_suite
from sparkdq.core.runner import run_suite
from sparkdq.core.reporter import to_json


# =====================================================================================
# Dataset loader helpers
# =====================================================================================

def _import_callable(fn_path: str) -> Callable:
    """
    Import a callable by fully qualified path.
    Supports 'pkg.mod:func' and 'pkg.mod.func'.
    """
    mod, sep, fn = fn_path.replace(":", ".").rpartition(".")
    if not mod or not fn:
        raise ValueError(f"Invalid callable '{fn_path}'. Expected 'module:function'")
    return getattr(import_module(mod), fn)


def _dataset_from_plugin(plugin_name: str) -> Optional[Callable]:
    """
    Resolve a dataset loader via entry points group 'sparkdq.datasets'.
    The user repo should define:
      [project.entry-points."sparkdq.datasets"]
      orders_df = "user_checks.data:load_df"
    """
    try:
        # Python 3.11+: entry_points().get(group, [])
        eps = entry_points().get("sparkdq.datasets", [])
    except Exception:
        # Python < 3.11 fallback
        eps = entry_points(group="sparkdq.datasets")

    for ep in eps:
        if ep.name == plugin_name:
            return ep.load()
    return None


def _parse_struct_type(schema_json: Any) -> Optional[StructType]:
    """
    Parse a StructType from dict / JSON string (optional/advanced).
    If parsing fails, return None and let Spark infer or error explicitly.
    """
    if not schema_json:
        return None
    try:
        payload = json.loads(schema_json) if isinstance(schema_json, str) else schema_json
        return StructType.fromJson(payload)
    except Exception:
        return None


def load_df(
    spark: SparkSession,
    path: Optional[str] = None,
    table: Optional[str] = None,
    format: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    schema: Optional[Any] = None,
    **kwargs,
) -> DataFrame:
    """
    Built-in dataset loader supporting common formats without extra dependencies:
      - parquet, csv, tsv (native)
      - json, orc (native)
      - delta, iceberg (via format() if runtime has the connectors configured)

    Avro is intentionally NOT included by default because many runtimes require
    additional packages/jars. If you need Avro, either:
      - Provide a custom loader in your user repo and point 'dataset.fn' to it, or
      - Ensure the runtime includes the connector and pass format='avro' (generic fallback).

    Rules:
      - If 'table' provided -> spark.read.options(**options).table(table)
      - Else require 'path' and either an explicit 'format' or infer from extension (safe set).
      - 'options' is optional; csv/tsv apply sane defaults merged with user options.
      - 'schema' is optional (StructType or JSON); applied for csv/json/tsv when provided.
    """
    options = options or {}

    # 1) Table read (e.g., Iceberg/Delta catalogs, Hive)
    if table:
        return spark.read.options(**options).table(table)

    # 2) Path read
    if not path:
        raise ValueError("Dataset requires at least one of: 'table' OR ('path' + 'format')")

    fmt = (format or "").strip().lower()
    if not fmt:
        # Infer from extension only for safe formats
        ext = Path(path).suffix.lower().lstrip(".")
        if ext in {"parquet", "csv", "json", "orc", "tsv"}:
            fmt = ext

    reader = spark.read
    struct = _parse_struct_type(schema)

    # Apply schema when supported
    if struct and fmt in {"csv", "json", "tsv"}:
        reader = reader.schema(struct)

    # Parquet
    if fmt == "parquet":
        return reader.options(**options).parquet(path)

    # CSV
    if fmt == "csv":
        default = {"header": "true", "inferSchema": "true"}
        merged = {**default, **{k: str(v) for k, v in options.items()}}
        return reader.options(**merged).csv(path)

    # TSV (CSV with tab)
    if fmt == "tsv":
        default = {"header": "true", "sep": "\t", "inferSchema": "true"}
        merged = {**default, **{k: str(v) for k, v in options.items()}}
        return reader.options(**merged).csv(path)

    # JSON
    if fmt == "json":
        return reader.options(**options).json(path)

    # ORC
    if fmt == "orc":
        return reader.options(**options).orc(path)

    # Delta (requires connector present in runtime)
    if fmt == "delta":
        return reader.format("delta").options(**options).load(path)

    # Iceberg (requires connector + catalog config present)
    if fmt == "iceberg":
        return reader.format("iceberg").options(**options).load(path)

    # Fallback: try generic format() loader (for custom connectors)
    if fmt:
        return reader.format(fmt).options(**options).load(path)

    raise ValueError(
        f"Unable to resolve dataset format for path='{path}'. "
        f"Provide 'format' or use a custom dataset loader via 'dataset.fn' or CLI flags."
    )


# =====================================================================================
# CLI parser
# =====================================================================================

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sparkdq",
        description="Run data quality suites over Spark DataFrames.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # --- run subcommand ---
    run_p = subparsers.add_parser(
        "run",
        help="Run a DQ suite from a YAML file",
        description="Execute a DQ suite specified in a YAML file.",
    )
    run_p.add_argument("--yaml", required=True, help="Path to the suite YAML file")
    run_p.add_argument("--suite-name", help="Suite name inside YAML (when multiple suites exist)")

    # Dataset provider (all optional)
    run_p.add_argument("--dataset-plugin", help="Entry-point name registered under 'sparkdq.datasets'")
    run_p.add_argument("--dataset-fn", help="Fully qualified dataset loader 'module:function'")
    run_p.add_argument(
        "--dataset-params",
        help="JSON dict of params for dataset loader (optional); defaults to '{}'",
    )

    run_p.add_argument("--fail-fast", action="store_true", help="Stop on the first failure")
    run_p.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    run_p.add_argument("--master", default="local[2]", help="Spark master")
    run_p.add_argument("--spark-jars", default=None, help="Comma-separated extra jars")
    run_p.add_argument(
        "--packages",
        default=None,
        help="Comma-separated Maven coordinates for Spark packages (e.g., io.delta:delta-core_2.12:2.4.0)",
    )
    run_p.add_argument("--app-name", default="sparkdq-cli", help="Spark application name")

    # --- ergonomic top-level (optional) ---
    # Allow `--yaml` without subcommand to default to `run`
    parser.add_argument("--yaml")
    parser.add_argument("--suite-name")
    parser.add_argument("--dataset-plugin")
    parser.add_argument("--dataset-fn")
    parser.add_argument("--dataset-params")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--format", choices=["json", "text"])
    parser.add_argument("--master")
    parser.add_argument("--spark-jars")
    parser.add_argument("--packages")
    parser.add_argument("--app-name")
    return parser


# =====================================================================================
# Suite & Dataset resolution
# =====================================================================================

def _resolve_suite_dict(yaml_file: Path, suite_name: Optional[str]) -> Dict[str, Any]:
    """
    Load the YAML and select a suite. Supports either:
      - a root dict with 'suites' mapping; or
      - a single-suite dict.
    """
    suite_all = load_suite(str(yaml_file))
    if "suites" in suite_all and isinstance(suite_all["suites"], dict):
        if not suite_name:
            raise ValueError("YAML contains multiple suites; please provide --suite-name")
        selected = suite_all["suites"].get(suite_name, {})
        if not selected:
            raise ValueError(f"Suite '{suite_name}' not found in {yaml_file}")
        return {
            "suite": selected.get("suite", suite_name),
            "fail_fast": bool(selected.get("fail_fast", False)),
            "checks": selected.get("checks", []),
            "per_column_checks": selected.get("per_column_checks", {}),
            "dataset": selected.get("dataset", None),
        }
    else:
        # Single suite dict already
        return suite_all


def _get_df(
    spark: SparkSession,
    suite_dict: Dict[str, Any],
    dataset_plugin: Optional[str],
    dataset_fn: Optional[str],
    dataset_params_json: Optional[str],
) -> DataFrame:
    """
    Resolution order (first match wins):
      1) --dataset-plugin (entry-point 'sparkdq.datasets')
      2) --dataset-fn (fully qualified 'module:function')
      3) YAML suites[...].dataset.fn (if present)
      4) Built-in load_df(**params from YAML dataset)
    '--dataset-params' is optional and defaults to {}.
    """
    # 0) Parse CLI params object (optional)
    params: Dict[str, Any] = {}
    if dataset_params_json:
        try:
            parsed = json.loads(dataset_params_json)
            if not isinstance(parsed, dict):
                raise ValueError("dataset-params must be a JSON object")
            params = parsed
        except Exception as e:
            raise ValueError(f"Failed to parse --dataset-params: {e}")

    # 1) Entry-point plugin from user repo
    if dataset_plugin:
        loader = _dataset_from_plugin(dataset_plugin)
        if loader is None:
            raise ValueError(f"Dataset plugin '{dataset_plugin}' not found in entry points 'sparkdq.datasets'")
        return loader(spark=spark, **params)

    # 2) Explicit module:function from user repo
    if dataset_fn:
        loader = _import_callable(dataset_fn)
        return loader(spark=spark, **params)

    # 3) YAML dataset section (fn optional)
    ds_spec = suite_dict.get("dataset") or {}
    ds_fn = ds_spec.get("fn")
    ds_params = ds_spec.get("params") or {}

    if ds_fn:
        loader = _import_callable(ds_fn)
        return loader(spark=spark, **ds_params)

    # 4) Built-in loader: use YAML params (table/path/format/options/schema)
    return load_df(spark=spark, **ds_params)


# =====================================================================================
# Runner
# =====================================================================================

def _run(
    yaml_path: str,
    suite_name: Optional[str],
    dataset_plugin: Optional[str],
    dataset_fn: Optional[str],
    dataset_params_json: Optional[str],
    fail_fast: bool,
    out_format: str,
    master: str,
    spark_jars: Optional[str],
    packages: Optional[str],
    app_name: str,
) -> int:

    yaml_file = Path(yaml_path)
    if not yaml_file.exists() or not yaml_file.is_file():
        print(f"ERROR: YAML file not found: {yaml_file}", file=sys.stderr)
        return 2

    # Prepare Spark extra jars / packages
    extra_jars: List[str] = []
    if spark_jars:
        extra_jars = [tok.strip() for tok in str(spark_jars).split(",") if tok.strip()]

    packages_list: List[str] = []
    if packages:
        packages_list = [tok.strip() for tok in str(packages).split(",") if tok.strip()]

    try:
        deequ_jar = resolve_deequ_jar()
        if deequ_jar:
            extra_jars.append(deequ_jar)
    except Exception:
        # Non-fatal: continue without Deequ
        pass

    # Create SparkSession, attempting to pass jars/packages if supported
    # Fallbacks ensure backward compatibility with older _make_spark signatures.
    try:
        spark = _make_spark(
            app_name=app_name,
            master=master,
            extra_jars=(extra_jars or None),
            packages=(packages_list or None),
        )
    except TypeError:
        # Try without packages
        try:
            spark = _make_spark(app_name=app_name, master=master, extra_jars=(extra_jars or None))
        except TypeError:
            # Minimal fallback
            spark = _make_spark(app_name=app_name, master=master)

        # If _make_spark didn't handle packages, apply via builder config (best-effort)
        if packages_list:
            try:
                # rebuild session with packages (best-effort for environments where builder is available)
                builder = SparkSession.builder.appName(app_name).master(master)
                builder = builder.config("spark.jars.packages", ",".join(packages_list))
                if extra_jars:
                    builder = builder.config("spark.jars", ",".join(extra_jars))
                # Transfer existing configs if needed (optional)
                spark.stop()
                spark = builder.getOrCreate()
            except Exception:
                # Ignore if builder path not desired in your environment; keep earlier spark
                pass

    exit_code = 0
    try:
        # Suite
        suite_dict = _resolve_suite_dict(yaml_file, suite_name)
        suite = to_suite(suite_dict)

        # Override fail_fast if flag provided
        if hasattr(suite, "fail_fast"):
            suite.fail_fast = bool(fail_fast)

        # Dataset
        df = _get_df(
            spark=spark,
            suite_dict=suite_dict,
            dataset_plugin=dataset_plugin,
            dataset_fn=dataset_fn,
            dataset_params_json=dataset_params_json,
        )

        # Run
        results = run_suite(suite=suite, spark=spark, df=df)

        # Output
        if out_format == "json":
            print(to_json(results))
        else:
            print(f"Suite:     {getattr(suite, 'name', suite_dict.get('suite', 'suite'))}")
            print(f"FailFast:  {getattr(suite, 'fail_fast', False)}")
            print("Results:")
            for r in results.get("results", []):
                name    = r.get("name")
                status  = r.get("status")
                sev     = r.get("severity")
                metrics = r.get("metrics", {})
                print(f"- {name}")
                print(f"    Severity: [{sev}]")
                print(f"    Status:   {status}")
                print(f"    Metrics:  {metrics}")

        # Exit codes by severity
        has_error_fail = any(
            (r.get("status") == "FAIL") and (str(r.get("severity")).upper() == "ERROR")
            for r in results.get("results", [])
        )
        has_warn_fail = any(
            (r.get("status") == "FAIL") and (str(r.get("severity")).upper() == "WARN")
            for r in results.get("results", [])
        )
        exit_code = 2 if has_error_fail else (1 if has_warn_fail else 0)

    finally:
        try:
            spark.stop()
        except Exception:
            pass

    return exit_code


# =====================================================================================
# Entrypoint
# =====================================================================================

def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Default to 'run' if top-level --yaml provided without subcommand
    if args.command is None and args.yaml:
        return _run(
            yaml_path=args.yaml,
            suite_name=getattr(args, "suite_name", None),
            dataset_plugin=getattr(args, "dataset_plugin", None),
            dataset_fn=getattr(args, "dataset_fn", None),
            dataset_params_json=getattr(args, "dataset_params", None),
            fail_fast=bool(getattr(args, "fail_fast", False)),
            out_format=(getattr(args, "format", None) or "json"),
            master=(getattr(args, "master", None) or "local[2]"),
            spark_jars=getattr(args, "spark_jars", None),
            packages=getattr(args, "packages", None),
            app_name=(getattr(args, "app_name", None) or "sparkdq-cli"),
        )

    # Run subcommand
    if args.command == "run":
        return _run(
            yaml_path=args.yaml,
            suite_name=args.suite_name,
            dataset_plugin=args.dataset_plugin,
            dataset_fn=args.dataset_fn,
            dataset_params_json=args.dataset_params,
            fail_fast=bool(args.fail_fast),
            out_format=args.format,
            master=args.master,
            spark_jars=args.spark_jars,
            packages=args.packages,
            app_name=args.app_name,
        )

    parser.print_help()
    return 2


def app():
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
