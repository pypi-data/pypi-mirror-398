from pyspark.sql import SparkSession
from sparkdq.config.env import resolve_deequ_jar
import platform
from pathlib import Path
import os
import shutil

def _persist_jar_if_windows(jar_path: str) -> str:
    """
    On Windows, copy the deequ jar to a stable cache location to avoid Spark staging it under %TEMP%.
    """
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    cache_dir = Path(os.environ.get("OPEN_SPARKDQ_CACHE_DIR", Path(base) / "open_sparkdq" / "jars"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / Path(jar_path).name
    if not dest.exists():
        shutil.copyfile(jar_path, dest)
    return str(dest)

def _make_spark(app_name: str = "sparkdq", master: str = "local[2]") -> SparkSession:
    _, deequ_jar = resolve_deequ_jar()

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.ui.enabled", "false")
    )

    if platform.system() == "Windows":
        # Use a persistent classpath instead of spark.jars to avoid %TEMP%/userFiles-* deletion on shutdown
        stable_jar = _persist_jar_if_windows(deequ_jar)
        builder = (
            builder
            .config("spark.driver.extraClassPath", stable_jar)
            .config("spark.executor.extraClassPath", stable_jar)
            # Optional: keep Spark's temp under a known folder (hygiene, not required)
            .config("spark.local.dir", os.environ.get("OPEN_SPARKDQ_LOCAL_DIR",
                                                     str(Path(os.environ.get("LOCALAPPDATA", Path.home()))
                                                         / "open_sparkdq" / "tmp")))
        )
    else:
        builder = builder.config("spark.jars", deequ_jar)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    try:
        _ = spark._jvm.com.amazon.deequ.checks.CheckLevel.Error()
    except Exception as e:
        raise RuntimeError(
            "Deequ classes not found on Spark classpath. "
            "If you have overridden SPARK_VERSION, also set DEEQU_JAR_PATH to a compatible jar."
        ) from e

    return spark
