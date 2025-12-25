from __future__ import annotations
import os
from importlib.resources import files
from pathlib import Path
from typing import Optional, Tuple

# Map supported Spark versions to the jar names shipped in the package
DEFAULT_DEEQU_JARS = {
    "3.3": "deequ-2.0.12-spark-3.3.jar",
}

def _package_jar_path(jar_name: str) -> Optional[str]:
    """
    Return absolute path to a jar bundled inside the package
    """
    try:
        p = files("sparkdq.resources.deequ").joinpath(jar_name)
        path = Path(str(p))
        if path.exists():
            return str(path)
    except Exception:
        pass
    return None

def resolve_deequ_jar() -> Tuple[str, str]:
    """
    Resolve (spark_version, deequ_jar_path) with this priority:
      1) DEEQU_JAR_PATH env → use it (validate exists)
      2) SPARK_VERSION env → try matching bundled jar
      3) default Spark version '3.3' → bundled jar
    Raises descriptive errors if not resolvable.
    """
    spark_version = os.getenv("SPARK_VERSION", "3.3")
    explicit_jar = os.getenv("DEEQU_JAR_PATH")

    if explicit_jar:
        jp = Path(explicit_jar)
        if not jp.exists():
            raise FileNotFoundError(f"DEEQU_JAR_PATH does not exist: {jp}")
        return spark_version, str(jp)

    # No explicit jar—try bundled default for the (possibly overridden) spark_version
    jar_name = DEFAULT_DEEQU_JARS.get(spark_version)
    if not jar_name:
        raise RuntimeError(
            f"No bundled Deequ jar for Spark '{spark_version}'. "
            f"Set DEEQU_JAR_PATH to a compatible jar (e.g., deequ-2.x-spark-{spark_version}.jar)."
        )

    bundled_path = _package_jar_path(jar_name)
    if bundled_path:
        return spark_version, bundled_path

    raise FileNotFoundError(
        f"Bundled jar '{jar_name}' not found inside package. "
        f"Please reinstall the library or set DEEQU_JAR_PATH explicitly."
    )
