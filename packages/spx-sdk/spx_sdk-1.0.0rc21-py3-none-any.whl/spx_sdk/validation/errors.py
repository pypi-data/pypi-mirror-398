# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

__all__ = [
    "ValidationCode",
    "ValidationError",
    "ValidationResult",
    "PathType",
    "pretty_path",
    "err",
    "merge_results",
    "success",
    "failure",
    "prepend_path",
    "compact_errors",
    "errors_summary",
]


class ValidationCode(str, Enum):
    """Canonical error codes used by the validation engine.

    Keep the set compact and stable – codes are part of the API and can be
    surfaced to clients (e.g. in HTTP 422 bodies). These codes are also used
    by the JSON Schema backend when mapping validator failures to engine errors.
    """

    # Registry / class resolution
    UNKNOWN_CLASS = "unknown_class"
    REGISTRY_NOT_FOUND = "registry_not_found"

    # Shape / type issues
    INVALID_SHAPE = "invalid_shape"
    TYPE_MISMATCH = "type_mismatch"
    INVALID_ENUM = "invalid_enum"

    # Object constraints
    MISSING_REQUIRED = "missing_required"
    ADDITIONAL_PROPERTY = "additional_property"

    # Collection helpers
    LIST_ITEM_ERROR = "list_item_error"
    DICT_KEY_ERROR = "dict_key_error"

    # Generic catch‑all for schema failures when no better code fits
    SCHEMA_VIOLATION = "schema_violation"


# Type alias for paths within a definition (e.g. ("models", "Temperature", "actions", 0, "set"))
PathType = Tuple[Union[str, int], ...]


# Helper to produce canonical string for code (enum or str)
def _code_string(code: Union["ValidationCode", str]) -> str:
    """Return a stable string for a code which may be an Enum or a plain string.
    Ensures API payloads expose canonical lowercase strings like 'type_mismatch'.
    """
    try:
        if isinstance(code, Enum):
            return str(code.value)
    except Exception:
        pass
    return str(code)


def pretty_path(path: Sequence[Union[str, int]]) -> str:
    """Render a human‑readable path like models.Temperature.actions[0].

    Works with tuples mixing dict keys (str) and list indices (int). This format
    is also used in diagnostics payloads to make 422 responses easier to read.
    """
    parts: List[str] = []
    for p in path:
        if isinstance(p, int):
            parts.append(f"[{p}]")
        else:
            if not parts:
                parts.append(str(p))
            else:
                parts.append("." + str(p))
    return "".join(parts) or "$"


@dataclass
class ValidationError:
    """Single validation issue with optional expected/actual payloads.

    - ``code`` should be one of :class:`ValidationCode`, but is left open to
      custom strings for forward compatibility.
    - ``path`` is a tuple forming the JSON pointer within the definition dict.
    - ``context`` allows attaching small structured details (e.g. field name,
      allowed types, enum values) without bloating ``message``.

    This is the standard error carrier used by both the JSON Schema backend and
    any custom ``@definition_validator`` hooks.
    """

    code: Union[ValidationCode, str]
    message: str
    path: PathType
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": _code_string(self.code),
            "message": self.message,
            "path": list(self.path),
            "path_str": pretty_path(self.path),
            "expected": self.expected,
            "actual": self.actual,
            "context": self.context,
        }


@dataclass
class ValidationResult:
    """Aggregate result for a validation pass."""

    ok: bool
    errors: List[ValidationError]

    @classmethod
    def from_errors(cls, errors: Iterable[ValidationError]) -> "ValidationResult":
        errs = list(errors)
        return cls(ok=(len(errs) == 0), errors=errs)

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "errors": [e.to_dict() for e in self.errors]}

    def first(self) -> Optional["ValidationError"]:
        """Return the first error or None."""
        return self.errors[0] if self.errors else None

    def to_compact_list(
        self,
        *,
        include_expected_actual: bool = False,
        include_context: bool = True,
        include_path_str: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Serialize errors into a compact list of dicts suitable for API payloads.

        By default includes: code, message, path (list) and path_str. You can opt‑in
        to include expected/actual and/or the context mapping.
        """
        out: List[Dict[str, Any]] = []
        for e in self.errors:
            item: Dict[str, Any] = {
                "code": _code_string(e.code),
                "message": e.message,
                "path": list(e.path),
            }
            if include_path_str:
                item["path_str"] = pretty_path(e.path)
            if include_expected_actual:
                item["expected"] = e.expected
                item["actual"] = e.actual
            if include_context:
                item["context"] = e.context
            out.append(item)
        return out


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def err(
    code: Union[ValidationCode, str],
    message: str,
    path: Sequence[Union[str, int]] = (),
    *,
    expected: Optional[Any] = None,
    actual: Optional[Any] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ValidationError:
    """Create a :class:`ValidationError` with minimal typing noise."""
    return ValidationError(
        code=code,
        message=message,
        path=tuple(path),
        expected=expected,
        actual=actual,
        context=context,
    )


def merge_results(results: Iterable[ValidationResult]) -> ValidationResult:
    """Merge many results into one."""
    merged: List[ValidationError] = []
    ok = True
    for r in results:
        if not r.ok:
            ok = False
        merged.extend(r.errors)
    return ValidationResult(ok=ok, errors=merged)


def success() -> ValidationResult:
    return ValidationResult(ok=True, errors=[])


def failure(errors: Iterable[ValidationError]) -> ValidationResult:
    return ValidationResult.from_errors(errors)


def prepend_path(
    errors: Iterable[ValidationError],
    prefix: Sequence[Union[str, int]]
) -> List[ValidationError]:
    """
    Return a new list of ValidationError with `prefix` prepended to each path.
    Useful when nesting results under a higher-level location (e.g. "models").
    """
    pfx = tuple(prefix)
    out: List[ValidationError] = []
    for e in errors:
        out.append(ValidationError(
            code=e.code,
            message=e.message,
            path=tuple(pfx + e.path),
            expected=e.expected,
            actual=e.actual,
            context=e.context,
        ))
    return out


def compact_errors(
    errors: Iterable[ValidationError],
    *,
    include_expected_actual: bool = False,
    include_context: bool = True,
    include_path_str: bool = True,
) -> List[Dict[str, Any]]:
    """
    Serialize an iterable of ValidationError into a compact list of dicts.
    Mirrors ValidationResult.to_compact_list for callers that don't have a result.
    """
    res = ValidationResult.from_errors(errors)
    return res.to_compact_list(
        include_expected_actual=include_expected_actual,
        include_context=include_context,
        include_path_str=include_path_str,
    )


def errors_summary(errors: Iterable[ValidationError]) -> str:
    """
    Build a short, human-readable one-line summary for logs/diagnostics.
    Example: "3 errors: missing_required at models.sensor, type_mismatch at instances[0]"
    """
    errs = list(errors)
    if not errs:
        return "0 errors"
    parts: List[str] = []
    for e in errs[:3]:
        parts.append(f"{_code_string(e.code)} at {pretty_path(e.path)}")
    more = f", +{len(errs)-3} more" if len(errs) > 3 else ""
    return f"{len(errs)} errors: " + ", ".join(parts) + more
