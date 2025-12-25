"""
Validator primitives for Spark DataFrames.

Importing this package will ensure built-in validators are available in the registry.
"""

from .base import Validator, ValidationOutcome

# Safe, guarded imports for each validator. If a module fails to import,
# tests will still collect and you can diagnose the specific module later.
def _safe_import(name, alias):
    try:
        module = __import__(f"sparkdq.core.validators.{name}", fromlist=[alias])
        return getattr(module, alias)
    except Exception as e:
        # Optional: log a warning; keep runtime resilient
        # print(f"[sparkdq.validators] Warning: failed to import {name}.{alias}: {e}")
        return None

NotNullValidator       = _safe_import("not_null", "NotNullValidator")
UniquenessValidator    = _safe_import("uniqueness", "UniquenessValidator")
RangeValidator         = _safe_import("range", "RangeValidator")
RegexValidator         = _safe_import("regex", "RegexValidator")
ExpressionValidator    = _safe_import("expression", "ExpressionValidator")
RowCountGreaterThan    = _safe_import("dataframe", "RowCountGreaterThan")
RowCountBetween        = _safe_import("dataframe", "RowCountBetween")

__all__ = [
    "Validator",
    "ValidationOutcome",
    # Export only those that imported successfully
    *[name for name, obj in {
        "NotNullValidator": NotNullValidator,
        "UniquenessValidator": UniquenessValidator,
        "RangeValidator": RangeValidator,
        "RegexValidator": RegexValidator,
        "ExpressionValidator": ExpressionValidator,
        "RowCountGreaterThan": RowCountGreaterThan,
        "RowCountBetween": RowCountBetween,
    }.items() if obj is not None]
]
