# open-spark-dlh-dq
Plug-and-play Data Quality for Apache Spark (batch + streaming) with YAML checks, profiling, and Open-Telemetry.



<pre>

open-spark-dlh-dq/
├─ pyproject.toml
├─ README.md
├─ LICENSE
│
├─ sparkdq/
│  ├─ __init__.py
│  │
│  ├─ cli/
│  │  └─ main.py                         # CLI: `sparkdq run --yaml open_spark_dlh_dq.yml`
│  │
│  ├─ config/
│  │  ├─ loader.py                       # YAML loader (safe_load + FileNotFound)
│  │  ├─ env.py                          # ENV VAR for spark version & pydeequ jar file
│  │  └─ schema.py                       # dict → DQSuite + bound validators (type/function/unit_tests)
│  │
│  ├─ core/
│  │  ├─ models.py                       #
│  │  ├─ registry.py                     # decorators + resolve_by_path + normalized keys
│  │  ├─ spark.py                        # spark session with deequ jar
│  │  ├─ runner.py                       # calls `validate(df)`; minor robustness
│  │  ├─ reporter.py                     # JSON serialization helpers (optional)
│  │  │
│  │  └─ validators/
│  │     ├─ base.py                      # Validator(name, params, severity?) + `validate(df)`
│  │     ├─ pydeequ_validators.py        # Built-in validators: not_null, uniqueness, row_count_gt, between
│  │     ├─ function_validators.py       # Adapters: FunctionValidator, UnitTestValidator
│  │     ├─ chispa_unit.py               # Optional: chispa helpers (e.g., schema equality)
│  │     └─ __init__.py                  # (optional) import/register built-ins
│  │
│  ├─ profiling/
│  │  └─ profiler.py                     # Optional: summary stats + quantiles + top-k
│  ├─ resources/
│  │  │
│  │  ├─ open_spark_dlh_dq.yml  # Root YAML users edit (source of truth)
│  │  └─ deequ/
│  │     └─ deequ-2.0.12-spark-3.3.jar
│  │  
│  │
│  ├─ observability/
│  │  └─ otel.py                         # Optional: minimal OTel span decorator for future use
│  │
│  └─ integrations/
│     └─ streaming.py                    # Optional: foreachBatch wrapper using suite validators
│
├─ user_checks/                          # Users add their DQ/unit-test functions here
│  ├─ __init__.py
│  └─ example_checks.py                  # Sample @dq_check and @unit_test functions
│
├─ examples/
│  ├─ suites/
│  │  └─ orders_dq.yml                   # Example suite (alt to root YAML)
│  ├─ batch_example.py                   # Sample: load YAML → run suite
│  └─ streaming_example.py               # Sample: foreachBatch usage
│
└─ tests/
   ├─ test_yaml_loader.py                # Verifies YAML parsing → DQSuite
   ├─ test_runner.py                     # Runs suite over small DF
   └─ test_validators.py                 # Unit tests for each validator type


<pre>


### Default Deequ JAR for Spark 3.3
The library auto-configures Deequ for Spark `3.3` by default. Place the jar `deequ-2.0.12-spark-3.3.jar` in one of:
- `C:\tools` (Windows)
- `/opt/tools`
- `/usr/local/share`

or set `DEEQU_JAR_PATH` to the exact file.

### Override for other Spark versions
Set the following environment variables in your script or shell:

```bash
# Use Spark 3.4 with a different Deequ jar
$env:SPARK_VERSION = "3.4"
$env:DEEQU_JAR_PATH = "C:\tools\deequ-2.0.12-spark-3.4.jar"
```

```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
./build.ps1

```