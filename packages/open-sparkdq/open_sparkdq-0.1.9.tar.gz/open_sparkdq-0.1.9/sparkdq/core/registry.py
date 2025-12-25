from __future__ import annotations

from typing import Any, Callable, Dict

# Registry mapping a short name to a factory callable (usually a Validator class)
_REGISTRY: Dict[str, Callable[..., Any]] = {}
_DQ_CHECKS: Dict[str, Callable] = {}
_UNIT_TESTS: Dict[str, Callable] = {}


def register_validator(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a validator class or factory under a given name."""
    def _inner(cls_or_factory: Callable[..., Any]) -> Callable[..., Any]:
        key = name.strip().lower()
        if key in _REGISTRY:
            raise ValueError(f"Validator '{name}' is already registered")
        _REGISTRY[key] = cls_or_factory
        return cls_or_factory
    return _inner


def dq_check(name: str) -> Callable[[Callable], Callable]:
    """
    Decorator to register a DQ check function.
    Function signature: fn(df, **kwargs) -> Dict[str, Any]
    Should return dict with keys: passed (bool), metrics/details (optional)
    """
    def _inner(fn: Callable) -> Callable:
        key = name.strip().lower()
        if key in _DQ_CHECKS:
            raise ValueError(f"DQ check '{name}' is already registered")
        _DQ_CHECKS[key] = fn
        return fn
    return _inner


def unit_test(name: str) -> Callable[[Callable], Callable]:
    """
    Decorator to register unit tests.
    Function signature: fn(df, **kwargs) -> None or raise AssertionError
    """
    def _inner(fn: Callable) -> Callable:
        key = name.strip().lower()
        if key in _UNIT_TESTS:
            raise ValueError(f"Unit test '{name}' is already registered")
        _UNIT_TESTS[key] = fn
        return fn
    return _inner


def create_validator(name: str, **kwargs: Any) -> Any:
    key = name.strip().lower()
    factory = _REGISTRY.get(key)
    if not factory:
        raise KeyError(
            f"Validator '{name}' not found in registry. "
            f"Did you import 'sparkdq.core.validators' so built-ins are registered?"
        )
    return factory(**kwargs)


def available_validators() -> Dict[str, Callable[..., Any]]:
    return dict(_REGISTRY)


def get_dq(name: str) -> Callable:
    key = name.strip().lower()
    if key not in _DQ_CHECKS:
        raise KeyError(f"DQ check '{name}' not found. Registered: {list(_DQ_CHECKS.keys())}")
    return _DQ_CHECKS[key]


def get_ut(name: str) -> Callable:
    key = name.strip().lower()
    if key not in _UNIT_TESTS:
        raise KeyError(f"Unit test '{name}' not found. Registered: {list(_UNIT_TESTS.keys())}")
    return _UNIT_TESTS[key]


def resolve_by_path(path: str) -> Callable:
    """
    Dynamically import "package.module:function" and return the callable.
    """
    mod_path, fn_name = path.rsplit(".", 1)
    mod = __import__(mod_path, fromlist=[fn_name])
    fn = getattr(mod, fn_name)
    return fn


def list_dq_checks() -> Dict[str, Callable]:
    return dict(_DQ_CHECKS)


def list_unit_tests() -> Dict[str, Callable]:
    return dict(_UNIT_TESTS)
