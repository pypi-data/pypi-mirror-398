from __future__ import annotations
from typing import Any, Dict, List, Optional
import json


def _fmt_float(x: Optional[float]) -> str:
    return "n/a" if x is None else f"{x:.3f}"

def print_profile(profile: Dict[str, Any], *, label: str = "", top_k: int = 5) -> None:
    """Human-readable profile aligned to DQ decisions."""
    if not isinstance(profile, dict):
        print("[PROFILE] (invalid)")
        return

    title = f"=== Profile{f' ({label})' if label else ''} ==="
    print(title)
    row_count = profile.get("row_count") 
    if row_count in (None, 0) and not cols:
        cols = {}
        print("rows: 0")
        print("\nHints:\n - Dataset empty → consider short-circuiting or low severity for row_count_gt.")
        return
    else:
        print(f"rows: {row_count}") 
        cols = profile.get("columns", {})

    # 1) Show per-column essentials that guide DQ
    for col, info in cols.items():
        dtype   = info.get("type")
        nulls   = info.get("null_count", 0)
        summary = f"  {col} [{dtype}] nulls={nulls}"

        # Numeric stats if present
        if "min" in info or "max" in info or "quantiles" in info:
            summary += (
                f" | min={_fmt_float(info.get('min'))}"
                f" max={_fmt_float(info.get('max'))}"
                f" mean={_fmt_float(info.get('mean'))}"
                f" p50={_fmt_float(info.get('quantiles', {}).get('p50'))}"
                f" p95={_fmt_float(info.get('quantiles', {}).get('p95'))}"
            )

        # Categorical hints: distinct + top-k
        if "distinct_count" in info:
            summary += f" | distinct={info.get('distinct_count')}"
            tk = info.get("top_k", [])[:top_k]
            if tk:
                pairs = ", ".join([f"{entry['value']}({entry['count']})" for entry in tk])
                summary += f" | topK: {pairs}"

        print(summary)

    # 2) Action hints derived from the profile
    #    (these help users decide which checks/severities/thresholds to use)
    print("\nHints:")
    if row_count == 0:
        print(" - Dataset is empty → consider short-circuiting or lower severity for row_count_gt.")
    else:
        # Show quick suggestions for columns with nulls / high max etc.
        for col, info in cols.items():
            nulls = info.get("null_count", 0)
            dtype = info.get("type")
            if nulls > 0:
                print(f" - {col}: {nulls} nulls → consider not_null({col}) or allow_nulls=true, lower severity.")
            if dtype and dtype != "string" and info.get("max") is not None and info.get("min") is not None:
                mn, mx = info.get("min"), info.get("max")
                p95    = info.get("quantiles", {}).get("p95")
                if p95 is not None and mx > p95:
                    print(f" - {col}: max={mx} > p95={p95} → consider between({col}, min={mn}, max≈{p95}).")
            # duplicate hints via topK
            top = info.get("top_k", [])
            if top and any(t["count"] > 1 for t in top):
                print(f" - {col}: duplicates evident in topK → consider uniqueness({col}).")

def print_dq_results(raw: Dict[str, Any], *, label: str = "", show_metrics: bool = True) -> None:
    """Readable DQ output with a quick summary and per-check lines."""
    title = f"=== DQ Results{f' ({label})' if label else ''} ==="
    print(title)
    checks = raw.get("results") or raw.get("checks") or []
    any_failed = raw.get("any_failed", False)

    # Summary
    total = len(checks)
    failed = sum(1 for r in checks if r.get("status") == "FAIL")
    passed = sum(1 for r in checks if r.get("status") == "PASS")
    print(f"summary: checks={total} | passed={passed} | failed={failed}")

    # Per-check lines
    for r in checks:
        name   = r.get("name")
        status = r.get("status")
        sev    = r.get("severity")
        line = f"- {name} [{sev}]: {status}"
        if show_metrics and r.get("metrics"):
            # print compact metrics; avoid huge dict dumps
            metrics = r["metrics"]
            # Extract common metric keys in a stable order
            keys = ("violations","null_or_blank_rows","duplicate_rows","out_of_range_rows",
                    "row_count","threshold","expression","pattern","predicate","bounds","inclusive","total")
            kv = ", ".join([f"{k}={metrics[k]}" for k in keys if k in metrics])
            if kv:
                line += f" | {kv}"
        print(line)

    if any_failed:
        print("→ One or more checks failed: consider routing to DLQ, lowering severity for known exceptions, or fixing source data.")

def print_trace_summary(span_dict: Dict[str, Any], *, label: str = "") -> None:
    """Show a compact span summary (for the stub Otel)."""
    title = f"=== Trace Summary{f' ({label})' if label else ''} ==="
    print(title)
    print(json.dumps(span_dict, indent=2, default=str))

def _default(o: Any):
    # Handle objects with to_dict / __dict__, else fallback to str
    if hasattr(o, "to_dict"):
        return o.to_dict()
    if hasattr(o, "__dict__"):
        return {k: v for k, v in o.__dict__.items() if not k.startswith("_")}
    return str(o)

def to_json(obj: Any, *, indent: int = 2) -> str:
    """
    Safe JSON serialization for suite results / reports.
    Accepts dicts or objects that expose to_dict / __dict__.
    """
    return json.dumps(obj, default=_default, indent=indent, ensure_ascii=False)

def to_dict(obj: Any) -> dict:
    """
    Convert obj to a dict using safe fallbacks.
    """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    # Last-resort: encode to JSON then back to dict (may lose types)
    return json.loads(to_json(obj))
