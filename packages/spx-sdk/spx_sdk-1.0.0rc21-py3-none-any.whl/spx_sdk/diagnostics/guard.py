from __future__ import annotations

"""
Diagnostics guards and helpers.

This module provides:
  - `guard(action, ...)` decorator to wrap component methods (sync/async),
  - `trace(component, action, ...)` context manager for inner blocks,
  - `call(component, action, fn, *args, **kwargs)` helper to wrap any callable,
  - `autoguard_lifecycle(cls, methods=...)` to auto-wrap common lifecycle methods.

It has no hard dependency on SpxComponent. It uses light introspection and the
diagnostics.faults helpers to build rich FaultEvents.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Generator, Iterable, Optional, TypeVar
import functools
import inspect
import json
import logging

from .faults import (
    SpxFault,
    FaultEvent,
    FaultSeverity,
    coerce_component_context,
)

log = logging.getLogger("spx.diagnostics")
T = TypeVar("T")
_COMPONENT_LOG_MARKER = "_spx_component_logged"


def _mark_component_logged(exc: BaseException) -> None:
    try:
        setattr(exc, _COMPONENT_LOG_MARKER, True)
    except Exception:
        pass


def _log_component_exception(component: Any, action: str, exc: BaseException) -> None:
    logger = getattr(component, "logger", None)
    if logger is None:
        return
    if getattr(exc, _COMPONENT_LOG_MARKER, False):
        return

    component_name = getattr(component, "name", component.__class__.__name__)
    path = None
    if hasattr(component, "get_path"):
        try:
            path = component.get_path("/")
        except Exception:
            path = None
    elif hasattr(component, "_get_full_path"):
        try:
            path = getattr(component, "_get_full_path")().replace(".", "/")
        except Exception:
            path = None

    scope = component_name if path is None else f"{component_name} ({path})"
    message = f"Exception during '{action}' in {scope}"
    logger.exception("%s: %s", message, exc)
    _mark_component_logged(exc)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_breadcrumb(component: Any, action: str) -> dict:
    ctx = coerce_component_context(component)
    return {
        "when": _now_iso(),
        "component": (ctx.name if ctx else None),
        "path": (ctx.path if ctx else None),
        "action": action,
    }


def _emit_fault(fault: SpxFault) -> FaultEvent:
    """
    Convert the SpxFault to FaultEvent and emit it via diagnostics.bus.publish
    if available; otherwise log as JSON. Returns the FaultEvent.
    """
    event = fault.to_event()
    # Try optional bus
    try:
        from . import bus  # lazy import; optional
        try:
            bus.publish(event)  # type: ignore[attr-defined]
            return event
        except Exception:
            # Fall through to logging on publish failure
            pass
    except Exception:
        pass
    try:
        log.error("FAULT %s", json.dumps(event.to_dict(), ensure_ascii=False))
    except Exception:
        # Last resort: plain repr
        log.error("FAULT %r", event)
    return event


# ---------------------------------------------------------------------------
# Decorator: guard
# ---------------------------------------------------------------------------
def guard(
    action: Optional[str] = None,
    *,
    prefix: Optional[str] = None,
    severity: FaultSeverity = FaultSeverity.ERROR,
    http_status: Optional[int] = None,
    bubble: bool = True,
    add_breadcrumb: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorate a method to capture exceptions, enrich with component context and
    re-raise as SpxFault (bubble=True) or emit and swallow (bubble=False).

    Works for both sync and async callables.

    If no action is provided, the wrapped function name is used, optionally prefixed with `prefix`.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        is_async = inspect.iscoroutinefunction(fn)

        # Resolve action: explicit > prefix+fn_name > fn_name
        resolved_action = action or (f"{prefix}{fn.__name__}" if prefix else fn.__name__)

        @functools.wraps(fn)
        async def awrapped(self, *args, **kwargs):  # type: ignore[override]
            try:
                return await fn(self, *args, **kwargs)  # type: ignore[misc]
            except SpxFault as sf:
                # Enrich fault in-place
                if add_breadcrumb:
                    sf.breadcrumbs.append(_make_breadcrumb(self, resolved_action))
                if sf.action is None:
                    sf.action = resolved_action
                if sf.component_ctx is None:
                    sf.component_ctx = coerce_component_context(self)
                if http_status and sf.http_status is None:
                    sf.http_status = http_status
                _log_component_exception(self, resolved_action, sf)
                if bubble:
                    raise sf
                _emit_fault(sf)
                return None  # swallowed
            except Exception as e:
                _log_component_exception(self, resolved_action, e)
                sf = SpxFault.from_exc(
                    e,
                    event="operation_failed",
                    action=resolved_action,
                    component=self,
                    severity=severity,
                    http_status=http_status,
                    breadcrumbs=[_make_breadcrumb(self, resolved_action)] if add_breadcrumb else None,
                )
                _mark_component_logged(sf)
                if bubble:
                    raise sf
                _emit_fault(sf)
                return None

        @functools.wraps(fn)
        def swrapped(self, *args, **kwargs):  # type: ignore[override]
            try:
                return fn(self, *args, **kwargs)
            except SpxFault as sf:
                if add_breadcrumb:
                    sf.breadcrumbs.append(_make_breadcrumb(self, resolved_action))
                if sf.action is None:
                    sf.action = resolved_action
                if sf.component_ctx is None:
                    sf.component_ctx = coerce_component_context(self)
                if http_status and sf.http_status is None:
                    sf.http_status = http_status
                _log_component_exception(self, resolved_action, sf)
                if bubble:
                    raise sf
                _emit_fault(sf)
                return None
            except Exception as e:
                _log_component_exception(self, resolved_action, e)
                sf = SpxFault.from_exc(
                    e,
                    event="operation_failed",
                    action=resolved_action,
                    component=self,
                    severity=severity,
                    http_status=http_status,
                    breadcrumbs=[_make_breadcrumb(self, resolved_action)] if add_breadcrumb else None,
                )
                _mark_component_logged(sf)
                if bubble:
                    raise sf
                _emit_fault(sf)
                return None

        wrapped = awrapped if is_async else swrapped
        # Mark as wrapped to avoid double-wrapping by autoguard
        setattr(wrapped, "_spx_guard_wrapped", True)
        setattr(wrapped, "_spx_guard_action", resolved_action)
        return wrapped  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Context manager: trace
# ---------------------------------------------------------------------------
@contextmanager
def trace(
    component: Any,
    *,
    action: str,
    severity: FaultSeverity = FaultSeverity.ERROR,
    http_status: Optional[int] = None,
    bubble: bool = True,
    extra: Optional[dict] = None,
) -> Generator[None, None, None]:
    """
    Use inside a method to capture exceptions from a critical block.

    - bubble=True: raise SpxFault up the stack
    - bubble=False: emit FaultEvent and swallow
    """
    try:
        yield
    except SpxFault as sf:
        sf.breadcrumbs.append(_make_breadcrumb(component, action))
        if sf.action is None:
            sf.action = action
        if sf.component_ctx is None:
            sf.component_ctx = coerce_component_context(component)
        if http_status and sf.http_status is None:
            sf.http_status = http_status
        if extra:
            sf.extra = {**(sf.extra or {}), **extra}
        _log_component_exception(component, action, sf)
        if bubble:
            raise sf
        _emit_fault(sf)
    except Exception as e:
        _log_component_exception(component, action, e)
        sf = SpxFault.from_exc(
            e,
            event="operation_failed",
            action=action,
            component=component,
            severity=severity,
            http_status=http_status,
            breadcrumbs=[_make_breadcrumb(component, action)],
            extra=extra,
        )
        _mark_component_logged(sf)
        if bubble:
            raise sf
        _emit_fault(sf)


# ---------------------------------------------------------------------------
# Helper: call
# ---------------------------------------------------------------------------
def call(
    component: Any,
    action: str,
    fn: Callable[..., T],
    *args: Any,
    severity: FaultSeverity = FaultSeverity.ERROR,
    http_status: Optional[int] = None,
    bubble: bool = True,
    extra: Optional[dict] = None,
    **kwargs: Any,
) -> Optional[T]:
    """
    Call arbitrary function `fn` with exception capture similar to `trace`.
    """
    try:
        return fn(*args, **kwargs)
    except SpxFault as sf:
        sf.breadcrumbs.append(_make_breadcrumb(component, action))
        if sf.action is None:
            sf.action = action
        if sf.component_ctx is None:
            sf.component_ctx = coerce_component_context(component)
        if http_status and sf.http_status is None:
            sf.http_status = http_status
        if extra:
            sf.extra = {**(sf.extra or {}), **extra}
        _log_component_exception(component, action, sf)
        if bubble:
            raise sf
        _emit_fault(sf)
        return None
    except Exception as e:
        _log_component_exception(component, action, e)
        sf = SpxFault.from_exc(
            e,
            event="operation_failed",
            action=action,
            component=component,
            severity=severity,
            http_status=http_status,
            breadcrumbs=[_make_breadcrumb(component, action)],
            extra=extra,
        )
        _mark_component_logged(sf)
        if bubble:
            raise sf
        _emit_fault(sf)
        return None


# ---------------------------------------------------------------------------
# Auto-guard lifecycle
# ---------------------------------------------------------------------------
def autoguard_lifecycle(
    cls: type,
    methods: Optional[Iterable[str]] = None,
    *,
    prefix: str = "lifecycle.",
    severity: FaultSeverity = FaultSeverity.ERROR,
) -> None:
    """
    Wrap common lifecycle methods on a class with `guard`, if present.
    Avoids double-wrapping by checking the `_spx_guard_wrapped` marker.
    """
    if methods is None:
        methods = ("prepare", "start", "run", "pause", "stop", "reset", "destroy")
    for name in methods:
        if not hasattr(cls, name):
            continue
        fn = getattr(cls, name)
        if not callable(fn):
            continue
        if getattr(fn, "_spx_guard_wrapped", False):
            continue
        wrapped = guard(prefix=prefix, severity=severity)(fn)
        setattr(cls, name, wrapped)
