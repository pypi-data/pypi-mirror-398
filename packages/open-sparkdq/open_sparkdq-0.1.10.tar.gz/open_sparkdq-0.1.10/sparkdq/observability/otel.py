from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, Optional


@dataclass
class Span:
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    start_ns: Optional[int] = None
    end_ns: Optional[int] = None
    error: Optional[str] = None

    def __enter__(self) -> "Span":
        self.start_ns = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.end_ns = perf_counter()
        if exc:
            self.error = f"{exc_type.__name__}: {exc}"

        
    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "attributes": self.attributes,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }

    @property
    def duration_ms(self) -> Optional[int]:
        if self.start_ns is None or self.end_ns is None:
            return None
        return int((self.end_ns - self.start_ns) * 1000000)


class Tracer:
    """Minimal tracer stub to be replaced with real OpenTelemetry integration."""

    def start_span(self, name: str, **attrs: Any) -> Span:
        return Span(name=name, attributes=dict(attrs))


class Meter:
    """Minimal meter stub for recording metrics."""

    def record(self, name: str, value: float, **attrs: Any) -> Dict[str, Any]:
        # No-op: return a structured metric record for potential logging
        return {
            'metric': name,
            'value': float(value),
            'attributes': dict(attrs),
        }


class Otel:
    """Global telemetry hooks for SparkDQ. Use this to inject real OTel later."""

    def __init__(self):
        self.enabled = True
        self.tracer = Tracer()
        self.meter = Meter()

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def start_span(self, name: str, **attrs: Any) -> Span:
        if not self.enabled:
            return Span(name=name, attributes=dict(attrs))
        return self.tracer.start_span(name, **attrs)

    def record_metric(self, name: str, value: float, **attrs: Any) -> Dict[str, Any]:
        if not self.enabled:
            return {'metric': name, 'value': float(value), 'attributes': dict(attrs), 'disabled': True}
        return self.meter.record(name, value, **attrs)


otel = Otel()
