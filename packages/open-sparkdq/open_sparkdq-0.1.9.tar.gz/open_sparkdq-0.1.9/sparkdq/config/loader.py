from __future__ import annotations

from importlib import resources
import os
from typing import Any, Dict
import yaml

from sparkdq.config.schema import to_suite
from sparkdq.core.models import DQSuite


def load_suite(path: str = "open_spark_dlh_dq.yml") -> Dict[str, Any]:
    """
    Load YAML as dict. If the file is missing, return {} (YAML optional).
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}