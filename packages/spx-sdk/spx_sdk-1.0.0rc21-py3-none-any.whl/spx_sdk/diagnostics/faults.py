from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union, TypedDict
from datetime import datetime, timezone
from contextvars import ContextVar
import traceback as _tb
import types as _types

# --- Optional correlation id (filled by diagnostics.context if available) ---
try:
    from .context import CORRELATION_ID  # type: ignore
    if not isinstance(CORRELATION_ID, ContextVar):
        # Defensive: ensure correct type even if user defines wrong object
        CORRELATION_ID = ContextVar("CORRELATION_ID", default=None)  # type: ignore
except Exception:
    CORRELATION_ID = ContextVar("CORRELATION_ID", default=None)  # type: ignore


# ---------- Light protocol-like context (no import from components) ----------
class ComponentLike(TypedDict, total=False):
    path: str
    name: str
    class_name: str
    state: str
    uid: str


# ------------------------------ Severity enum ------------------------------
class FaultSeverity(str, Enum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"


# ----------------------------- Trace structures ----------------------------
@dataclass
class TraceFrame:
    file: str
    line: int
    func: str
    code: Optional[str] = None


@dataclass
class TracebackInfo:
    frames: List[TraceFrame] = field(default_factory=list)
    summary: Optional[str] = None


# ------------------------------ Error payload ------------------------------
@dataclass
class ErrorInfo:
    type: str
    message: str
    repr: str
    traceback: Optional[TracebackInfo] = None
    caused_by: Optional["ErrorInfo"] = None


# --------------------------- Component descriptor --------------------------
@dataclass
class ComponentContext:
    path: Optional[str] = None
    name: Optional[str] = None
    class_name: Optional[str] = None
    state: Optional[str] = None
    uid: Optional[str] = None


# ------------------------------- Fault event -------------------------------
@dataclass
class FaultEvent:
    """
    Canonical, serializable description of a runtime fault.
    This is the primary structure you should log/emit/return via API.
    """
    type: str
    event: str
    severity: FaultSeverity
    when: str
    correlation_id: Optional[str] = None
    action: Optional[str] = None
    http_status: Optional[int] = None
    component: Optional[ComponentContext] = None
    breadcrumbs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[ErrorInfo] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        def _coerce(obj: Any) -> Any:
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, datetime):
                return obj.isoformat()
            if dataclass_isinstance(obj):
                return {k: _coerce(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [_coerce(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _coerce(v) for k, v in obj.items()}
            return obj

        return _coerce(self)  # type: ignore

    # Compatibility helper: convert to the "HeadPoint" shaped dict used by API
    def to_headpoint(self) -> Dict[str, Any]:
        hp = {
            "type": "headpoint",
            "kind": "error",
            "event": self.event,
            "when": self.when,
            "http_status": self.http_status,
            "path": getattr(self.component, "path", None) if self.component else None,
            "action": self.action,
            "component": {
                "name": getattr(self.component, "name", None) if self.component else None,
                "class": getattr(self.component, "class_name", None) if self.component else None,
                "state": getattr(self.component, "state", None) if self.component else None,
                "uid": getattr(self.component, "uid", None) if self.component else None,
            } if self.component else None,
            "error": self.error_to_dict(),
            "extra": self.extra,
            "correlation_id": self.correlation_id,
            "severity": self.severity.value,
        }
        # remove None entries
        return {k: v for k, v in hp.items() if v is not None}

    def error_to_dict(self) -> Optional[Dict[str, Any]]:
        if not self.error:
            return None

        def _err_to_dict(err: ErrorInfo) -> Dict[str, Any]:
            d = {
                "type": err.type,
                "message": err.message,
                "repr": err.repr,
                "traceback": None,
                "caused_by": None,
            }
            if err.traceback:
                d["traceback"] = {
                    "summary": err.traceback.summary,
                    "frames": [asdict(f) for f in err.traceback.frames],
                }
            if err.caused_by:
                d["caused_by"] = _err_to_dict(err.caused_by)
            return {k: v for k, v in d.items() if v is not None}

        return _err_to_dict(self.error)


# ------------------------------- SpxFault ----------------------------------
class SpxFault(Exception):
    """
    Exception class that carries enough context to build a FaultEvent.
    Always prefer `raise SpxFault(... ) from e` to preserve the cause chain.
    """

    def __init__(
        self,
        *,
        event: str,
        action: Optional[str] = None,
        component: Optional[Union[ComponentContext, ComponentLike, Any]] = None,
        severity: FaultSeverity = FaultSeverity.ERROR,
        extra: Optional[Dict[str, Any]] = None,
        http_status: Optional[int] = None,
        breadcrumbs: Optional[List[Dict[str, Any]]] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(event)
        self.event = event
        self.action = action
        self.component_ctx = coerce_component_context(component)
        self.severity = severity
        self.extra = extra or None
        self.http_status = http_status
        self.breadcrumbs = list(breadcrumbs or [])
        self.__cause__ = cause or getattr(self, "__cause__", None)

    def to_event(self) -> FaultEvent:
        now_iso = datetime.now(timezone.utc).isoformat()
        corr = CORRELATION_ID.get()
        error_info = build_error_info(self.__cause__ or self)
        return FaultEvent(
            type="fault",
            event=self.event,
            severity=self.severity,
            when=now_iso,
            correlation_id=str(corr) if corr is not None else None,
            action=self.action,
            http_status=self.http_status,
            component=self.component_ctx,
            breadcrumbs=self.breadcrumbs,
            error=error_info,
            extra=self.extra,
        )

    @staticmethod
    def from_exc(
        exc: BaseException,
        *,
        event: str,
        action: Optional[str] = None,
        component: Optional[Union[ComponentContext, ComponentLike, Any]] = None,
        severity: FaultSeverity = FaultSeverity.ERROR,
        extra: Optional[Dict[str, Any]] = None,
        http_status: Optional[int] = None,
        breadcrumbs: Optional[List[Dict[str, Any]]] = None,
    ) -> "SpxFault":
        return SpxFault(
            event=event,
            action=action,
            component=component,
            severity=severity,
            extra=extra,
            http_status=http_status,
            breadcrumbs=breadcrumbs,
            cause=exc,
        )


# ----------------------------- Helper functions ----------------------------
def dataclass_isinstance(obj: Any) -> bool:
    try:
        from dataclasses import is_dataclass
        return is_dataclass(obj)
    except Exception:
        return False


def coerce_component_context(obj: Optional[Union[ComponentContext, ComponentLike, Any]]) -> Optional[ComponentContext]:
    if obj is None:
        return None
    if isinstance(obj, ComponentContext):
        return obj
    # Mapping-like (e.g., TypedDict)
    if isinstance(obj, dict):
        return ComponentContext(
            path=_safe_str(obj.get("path")),
            name=_safe_str(obj.get("name")),
            class_name=_safe_str(obj.get("class_name") or obj.get("class")),
            state=_safe_str(obj.get("state")),
            uid=_safe_str(obj.get("uid")),
        )
    # Rich python object – introspect common attributes
    path = None
    if hasattr(obj, "get_path"):
        try:
            path = str(obj.get_path("/"))
        except Exception:
            path = None
    elif hasattr(obj, "_get_full_path"):
        try:
            path = str(getattr(obj, "_get_full_path")()).replace(".", "/")
        except Exception:
            path = None
    return ComponentContext(
        path=path,
        name=_safe_str(getattr(obj, "name", None)),
        class_name=_safe_str(obj.__class__.__name__ if hasattr(obj, "__class__") else None),
        state=_safe_str(getattr(obj, "state", None)),
        uid=_safe_str(getattr(obj, "uid", None)),
    )


def build_error_info(exc: BaseException) -> ErrorInfo:
    """
    Construct ErrorInfo with traceback and cause chain.
    """
    tbi = format_trace(exc)
    caused = None
    # Prefer __cause__ (explicit) over __context__ (implicit) if available
    cause_exc = getattr(exc, "__cause__", None) or getattr(exc, "__context__", None)
    if isinstance(cause_exc, BaseException):
        caused = build_error_info(cause_exc)
    return ErrorInfo(
        type=exc.__class__.__name__,
        message=_safe_str(str(exc)),
        repr=_safe_str(repr(exc)),
        traceback=tbi,
        caused_by=caused,
    )


def format_trace(exc: BaseException, *, max_frames: int = 50) -> TracebackInfo:
    """
    Extract frames (file, line, func, code) and produce a short summary string.
    """
    frames: List[TraceFrame] = []
    tb: Optional[_types.TracebackType] = exc.__traceback__ if hasattr(exc, "__traceback__") else None
    # Walk the traceback chain safely
    extracted: Sequence[_tb.FrameSummary] = []
    try:
        extracted = _tb.extract_tb(tb, limit=max_frames) if tb else []
    except Exception:
        extracted = []
    for fs in extracted:
        frames.append(TraceFrame(file=_safe_str(fs.filename), line=int(fs.lineno), func=_safe_str(fs.name), code=_safe_str(fs.line)))
    # Build summary with last 1–3 frames for quick glance
    summary = None
    if frames:
        tail = frames[-3:]
        summary = " → ".join(f"{_basename(f.file)}:{f.line} in {f.func}" for f in tail)
    return TracebackInfo(frames=frames, summary=summary)


def build_fault_event(
    exc: BaseException | SpxFault,
    *,
    event: Optional[str] = None,
    action: Optional[str] = None,
    component: Optional[Union[ComponentContext, ComponentLike, Any]] = None,
    severity: Optional[FaultSeverity] = None,
    extra: Optional[Dict[str, Any]] = None,
    http_status: Optional[int] = None,
    breadcrumbs: Optional[List[Dict[str, Any]]] = None,
) -> FaultEvent:
    """
    Convenience: produce FaultEvent from any exception.
    If `exc` is SpxFault, use its embedded metadata as defaults.
    """
    if isinstance(exc, SpxFault):
        event = event or exc.event
        action = action or exc.action
        component = component or exc.component_ctx
        severity = severity or exc.severity
        extra = {**(exc.extra or {}), **(extra or {})} if exc.extra or extra else (exc.extra or extra)
        http_status = http_status or exc.http_status
        breadcrumbs = (exc.breadcrumbs or []) + (breadcrumbs or [])
        cause = exc.__cause__ or exc
    else:
        cause = exc
        if severity is None:
            severity = FaultSeverity.ERROR
        component = coerce_component_context(component)

    now_iso = datetime.now(timezone.utc).isoformat()
    corr = CORRELATION_ID.get()
    return FaultEvent(
        type="fault",
        event=event or exc.__class__.__name__,
        severity=severity or FaultSeverity.ERROR,
        when=now_iso,
        correlation_id=str(corr) if corr is not None else None,
        action=action,
        http_status=http_status,
        component=coerce_component_context(component),
        breadcrumbs=list(breadcrumbs or []),
        error=build_error_info(cause),
        extra=extra,
    )


# ------------------------------ Small utilities ----------------------------
def _safe_str(x: Any, *, max_len: int = 10_000) -> Optional[str]:
    if x is None:
        return None
    try:
        s = str(x)
        if len(s) > max_len:
            return s[: max_len - 1] + "…"
        return s
    except Exception:
        try:
            r = repr(x)
            return r if len(r) <= max_len else r[: max_len - 1] + "…"
        except Exception:
            return None


def _basename(path: str) -> str:
    try:
        import os
        return os.path.basename(path)
    except Exception:
        return path
