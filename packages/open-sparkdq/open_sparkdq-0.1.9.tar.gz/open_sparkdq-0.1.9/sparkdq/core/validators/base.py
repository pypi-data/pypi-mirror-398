from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from sparkdq.core.models import Severity

ValidationOutcome = Dict[str, Any]


@dataclass
class Validator:
    """Base class for all validators.

    Concrete validators MUST implement `validate(df)` and return a dict with keys:
      - passed: bool
      - metrics: Dict[str, Any] (optional)

    Notes:
      - `params` allows binding YAML arguments at construction time so runner
        can always call `validate(df)` with no kwargs.
      - `severity` is optional here; DQCheck already carries severity in models,
        but some validators (like pydeequ-backed) may need it for CheckLevel mapping.
    """
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    severity: Optional[Severity] = None

    def validate(self, df: Any) -> ValidationOutcome:
        raise NotImplementedError("Implement in subclass")
