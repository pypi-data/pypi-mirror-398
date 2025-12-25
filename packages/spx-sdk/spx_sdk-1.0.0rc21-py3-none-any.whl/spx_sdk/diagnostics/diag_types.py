from __future__ import annotations

"""
Shared lightweight typing helpers for diagnostics.

We keep this module free of imports from `spx_sdk.components` to avoid cycles.
Other diagnostics modules may import from here.
"""

from typing import Any, Optional, Protocol, TypedDict, runtime_checkable


class ComponentLike(TypedDict, total=False):  # pragma: no cover
    """
    Mapping-style representation of a component context.
    Used when we don't want to depend on concrete component classes.
    """
    path: str
    name: str
    class_name: str   # class name (avoid reserved word 'class')
    state: str
    uid: str


class Breadcrumb(TypedDict, total=False):  # pragma: no cover
    """Shape for a single breadcrumb in fault events."""
    when: str
    component: str
    path: str
    action: str


@runtime_checkable  # pragma: no cover
class ComponentObject(Protocol):  # pragma: no cover
    """
    Minimal protocol for object-like components that diagnostics can
    introspect without importing concrete classes.
    """
    name: str
    state: Any
    uid: Optional[str]
    parent: Optional[Any]

    def get_path(self, delimiter: str = "/") -> str: ...


__all__ = ["ComponentLike", "Breadcrumb", "ComponentObject"]
