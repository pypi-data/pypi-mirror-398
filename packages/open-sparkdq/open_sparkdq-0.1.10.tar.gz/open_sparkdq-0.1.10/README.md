# open-spark-dlh-dq

Open source Plug-and-play Data Quality for Apache Spark (Batch + Streaming) with YAML checks, profiling, and OpenTelemetry.

---

## 📌 Project Overview
`open-spark-dlh-dq` is an open-source Python library providing a **Data Quality (DQ) framework for Apache Spark**.

It supports:

- ✅ **Batch & Streaming DQ** with declarative YAML suites
- ✅ **Custom checks** via Python (`dq_check`, `unit_test`)
- ✅ **CLI execution** for datasets in directories or Spark DataFrames
- ✅ **Inline checks** in PySpark scripts
- ✅ **Format support**: Parquet, CSV, Iceberg, Delta, JSON, ORC
- ✅ **Profiler & OpenTelemetry** for observability

Built on **PySpark**, **PyDeequ**, and **Chispa**, this library enables robust data validation pipelines.

---

## ✅ Features

- **Batch DQ**: Validate static datasets using YAML or inline rules.
- **Streaming DQ**: Apply checks on micro-batches via `foreachBatch`.
- **Custom Checks**: Extend with Python functions in `user_checks/`.
- **CLI Tool**: Run suites via `sparkdq run --yaml <suite.yml>`.
- **Profiler**: Generate summary stats and quantiles.
- **OpenTelemetry**: Capture spans and traces for test cases.

---

## 📂 Repository Structure

<pre>

open-spark-dlh-dq/
├─ pyproject.toml
├─ README.md
├─ LICENSE
│
├─ sparkdq/
│  ├─ cli/main.py                          # CLI entry point
│  ├─ config/                              # YAML loader, env vars, schema binding
│  ├─ core/                                # Models, registry, Spark session, runner
│  │  └─ validators/                       # Built-in + custom validator classes
│  ├─ profiling/profiler.py                # Profiling utilities
│  ├─ resources/open_spark_dlh_dq.yml      # Default YAML suite
│  ├─ observability/otel.py                # OpenTelemetry integration
│  └─ integrations/streaming.py            # foreachBatch wrapper
│
├─ user_checks/                            # User-defined checks
│  └─ example_checks.py
│
├─ examples/                               # Usage examples
│  ├─ suites/orders_dq.yml
│  ├─ batch_example.py
│  └─ streaming_example.py
│
└─ tests/                                  # Unit tests
   ├─ test_yaml_loader.py
   ├─ test_chispa_integration.py
   ├─ test_pydeequ_integration.py
   ├─ test_runner.py
   ├─ test_validators.py
   ├─ test_validator_contracts.py
   └─ test_cli.py

</pre>

---

## 🛠 Usage

### **Run CLI with YAML suite**
```bash
sparkdq run --yaml ./sparkdq/resources/open_spark_dlh_dq.yml --suite-name orders_dq --format text
```

### **Inline checks in PySpark**
```python
from sparkdq.core.runner import run_suite
from sparkdq.config.loader import load_yaml_suite

suite = load_yaml_suite("./sparkdq/resources/open_spark_dlh_dq.yml")
df = spark.read.parquet("./data/orders")
run_suite(df, suite)
```

### **Streaming example**
```bash
python examples/streaming_example.py
```

---

## 🧩 Custom Checks
Add Python methods in `user_checks/example_checks.py`:
```python
from sparkdq.core.registry import dq_check, unit_test

@dq_check("amount_positive")
def amount_positive(df):
    return df.filter(df.amount > 0).count() == df.count()
```
Reference them in YAML:
```yaml
test_cases:
  - name: amount_positive
    type: dq_check
```

---

## 📊 Profiler & OpenTelemetry
Enable profiling and observability in your pipeline:
```python
from sparkdq.profiling.profiler import profile_df
profile_df(df)
```

OpenTelemetry spans can be enabled via `sparkdq/observability/otel.py`.

---

## 🔨 Build & Publish

### **Build for PyPI (Windows)**
```powershell
./build.ps1
```

### **Build for PyPI (Linux)**
```bash
./build.sh
```

### **Example Repository to understand how to use**

https://github.com/aashish72it/spark-test


