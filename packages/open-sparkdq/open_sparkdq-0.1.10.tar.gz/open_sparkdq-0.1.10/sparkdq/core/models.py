
# sparkdq/core/models.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


class Severity(Enum):
    INFO = 10
    WARN = 20
    ERROR = 30
    CRITICAL = 40

    def is_failure(self) -> bool:
        return self.value >= Severity.ERROR.value


class Status(Enum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    ERROR = 'ERROR'
    SKIP = 'SKIP'


@dataclass
class DQCheck:
    name: str
    validator: Any  # instance of Validator
    severity: Severity = Severity.ERROR
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class DQResult:
    check_name: str
    status: Status
    severity: Severity
    passed: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    started_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['status'] = self.status.value
        d['severity'] = self.severity.name
        return d


@dataclass
class DQSuite:
    name: str
    checks: List[DQCheck] = field(default_factory=list)
    fail_fast: bool = False


@dataclass
class DQReport:
    suite_name: str
    results: List[DQResult]

    @property
    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == Status.PASS)
        failed = sum(1 for r in self.results if r.status == Status.FAIL)
        errored = sum(1 for r in self.results if r.status == Status.ERROR)
        by_severity: Dict[str, Dict[str, int]] = {}
        for r in self.results:
            sev = r.severity.name
            by_severity.setdefault(sev, {'PASS': 0, 'FAIL': 0, 'ERROR': 0})
            by_severity[sev][r.status.value] += 1
        return {
            'total_checks': total,
            'passed': passed,
            'failed': failed,
            'errored': errored,
            'by_severity': by_severity,
        }

    def to_json(self, indent: int = 2) -> str:
        payload = {
            'suite': self.suite_name,
            'summary': self.summary,
            'results': [r.to_dict() for r in self.results],
            'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        }
        return json.dumps(payload, ensure_ascii=False, indent=indent)
