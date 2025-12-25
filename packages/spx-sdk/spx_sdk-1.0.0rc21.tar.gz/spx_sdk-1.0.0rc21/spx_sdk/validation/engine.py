# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from .errors import (
    ValidationCode,
    ValidationError,
    ValidationResult,
    err,
    success,
    failure,
)
from ._jsonschema_backend import validate_with_jsonschema

__all__ = [
    "ValidationEngine",
    "validate_component_definition",
    "validate_definition_for",
    "validate_document",
]

JsonPath = Tuple[Union[str, int], ...]


# ---------------------------------------------------------------------------
# Registry adapter helpers
# ---------------------------------------------------------------------------

def _registry_get_class(registry: Optional[Any], class_name: str) -> Optional[type]:
    """Resolve class by name using a registry-like object or global registry.

    The adapter supports either:
      - an object exposing `get_class(name: str) -> type`, or
      - falling back to `spx_sdk.registry.get_class` if importable.
    """
    # 1) External registry object
    if registry is not None and hasattr(registry, "get_class"):
        try:
            cls = registry.get_class(class_name)  # type: ignore[attr-defined]
            return cls
        except Exception:
            return None
    # 2) Global registry fallback
    try:  # pragma: no cover - thin adapter; behaviour tested via engine paths
        from spx_sdk.registry import get_class as _get_class  # lazy import

        try:
            return _get_class(class_name)
        except Exception:
            return None
    except Exception:
        return None


def _registry_get_base_name(registry: Optional[Any], class_name: str) -> Optional[str]:
    """Resolve base-class name for a registered class via registry; fallback to MRO."""
    # Prefer explicit registry API if available
    if registry is not None and hasattr(registry, "get_class_base"):
        try:
            return registry.get_class_base(class_name)  # type: ignore[attr-defined]
        except Exception:
            pass
    # Fallback to global registry helper if importable
    try:  # pragma: no cover - thin adapter; behaviour tested via engine paths
        from spx_sdk.registry import get_class_base as _get_class_base  # lazy import
        try:
            return _get_class_base(class_name)
        except Exception:
            pass
    except Exception:
        pass
    # Last resort: inspect the class directly
    cls = _registry_get_class(registry, class_name)
    try:
        bases = getattr(cls, "__bases__", ()) if cls is not None else ()
        if bases:
            return bases[0].__name__
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Utility: normalize custom validator results
# ---------------------------------------------------------------------------
def _as_error_list(result: Any) -> List[ValidationError]:
    """Accept list/iterable of ValidationError, single ValidationError, or ValidationResult."""
    if result is None:
        return []
    if isinstance(result, ValidationError):
        return [result]
    if isinstance(result, ValidationResult):
        return list(result.errors)
    # Accept any iterable and filter to ValidationError items
    try:
        return [e for e in result if isinstance(e, ValidationError)]
    except TypeError:
        # Not iterable / unsupported shape
        return []


# ---------------------------------------------------------------------------
# Validation engine
# ---------------------------------------------------------------------------
class ValidationEngine:
    """High-level validator for SPX component definitions.

    - Validates a raw ``definition`` dict against a class' JSON Schema
      (if provided via ``@definition_schema`` as a dict **or a callable returning a dict**),
      including SPX extensions handled by the JSON Schema backend.
    - Executes a class-level custom validator attached via
      ``@definition_validator`` when present.
    - Recurses into nested children by delegating SPX extensions to an
      internal handler bound to a registry adapter.
    """

    def __init__(self, registry: Optional[Any] = None) -> None:
        self.registry = registry

    # ---- public API -----------------------------------------------------
    def validate_for(self, class_or_name: Union[str, Type[Any]], definition: Any, path: Sequence[Union[str, int]] = ()) -> ValidationResult:
        return self._validate(class_or_name, definition, tuple(path))

    # ---- internals ------------------------------------------------------
    def _validate(self, class_or_name: Union[str, Type[Any]], definition: Any, path: JsonPath) -> ValidationResult:
        # Resolve class
        if isinstance(class_or_name, str):
            cls = _registry_get_class(self.registry, class_or_name)
            if cls is None:
                return failure([
                    err(
                        ValidationCode.UNKNOWN_CLASS,
                        f"Class '{class_or_name}' not found",
                        path,
                        expected="registered class",
                        actual=class_or_name,
                    )
                ])
        else:
            cls = class_or_name

        # Schema validation (if class exposes a schema; accept dict or callable returning dict)
        errors: List[ValidationError] = []
        schema_attr = getattr(cls, "__spx_definition_schema__", None)
        resolved_schema: Optional[Dict[str, Any]] = None
        if callable(schema_attr):
            try:
                maybe = schema_attr()
                if isinstance(maybe, dict):
                    resolved_schema = maybe
                else:
                    errors.append(
                        err(
                            ValidationCode.SCHEMA_VIOLATION,
                            f"definition_schema for {getattr(cls, '__name__', str(cls))} must return dict, got {type(maybe).__name__}",
                            path,
                        )
                    )
            except Exception as ex:
                errors.append(
                    err(
                        ValidationCode.SCHEMA_VIOLATION,
                        f"definition_schema callable for {getattr(cls, '__name__', str(cls))} raised: {ex}",
                        path,
                    )
                )
        elif isinstance(schema_attr, dict):
            resolved_schema = schema_attr
        elif schema_attr is not None:
            errors.append(
                err(
                    ValidationCode.SCHEMA_VIOLATION,
                    f"definition_schema for {getattr(cls, '__name__', str(cls))} must be dict or callable, got {type(schema_attr).__name__}",
                    path,
                )
            )

        if isinstance(resolved_schema, dict):
            errors.extend(
                validate_with_jsonschema(definition, resolved_schema, path, registry=self.registry)
            )

        # Custom validator (optional)
        validator = getattr(cls, "__spx_definition_validator__", None)
        if callable(validator):
            try:
                custom = validator(cls, definition, self.registry, path)  # type: ignore[misc]
                errors.extend(_as_error_list(custom))
            except Exception as ex:  # be defensive: validator bugs shouldn't crash engine
                errors.append(
                    err(
                        ValidationCode.SCHEMA_VIOLATION,
                        f"Validator for {getattr(cls, '__name__', str(cls))} raised: {ex}",
                        path,
                    )
                )

        return success() if not errors else failure(errors)


# ---------------------------------------------------------------------------
# Functional helpers (simple façade over ValidationEngine)
# ---------------------------------------------------------------------------
def validate_component_definition(
    class_or_name: Union[str, Type[Any]],
    definition: Any,
    *,
    registry: Optional[Any] = None,
    path: Sequence[Union[str, int]] = (),
) -> ValidationResult:
    """Validate a single component definition for a given class or class name.

    Example:
        >>> res = validate_component_definition("SpxAttribute", {"default": 1.0})
        >>> assert res.ok
    """
    engine = ValidationEngine(registry)
    return engine.validate_for(class_or_name, definition, path)


# Alias
validate_definition_for = validate_component_definition


# ---------------------------------------------------------------------------
# Document-level validation orchestrator
# ---------------------------------------------------------------------------
def validate_document(
    definition: Any,
    *,
    registry: Optional[Any] = None,
    root_class: Optional[Union[str, Type[Any]]] = None,
) -> ValidationResult:
    """Validate a full SPX document (dict) without constructing models.

    Generic behavior:
    - Depth‑first traversal over dicts/lists with no knowledge of section names.
    - At each mapping key, try to resolve the key as a registered class name.
    - If the class exposes a definition schema (dict or callable), validate the node
      against that schema using the standard component validator.
    - If the class has no schema, do nothing at this node and continue traversal.
    - Missing classes are tolerated; we still traverse into the subtree.
    """
    # Defensive: document must be a mapping
    if not isinstance(definition, dict):
        return failure([
            err(
                ValidationCode.SCHEMA_VIOLATION,
                f"validate_document expects a dict, got {type(definition).__name__}",
                (),
                expected="dict",
                actual=type(definition).__name__,
            )
        ])

    # Optional: validate the root object against a declared root class schema
    if root_class is not None:
        # Resolve class by name if needed
        cls: Optional[Type[Any]] = None
        if isinstance(root_class, str):
            cls = _registry_get_class(registry, root_class)
        else:
            cls = root_class

        if cls is not None:
            schema_attr = getattr(cls, "__spx_definition_schema__", None)
            has_schema = callable(schema_attr) or isinstance(schema_attr, dict)
            if has_schema:
                res = validate_component_definition(cls, definition, registry=registry, path=())
                if not res.ok:
                    return res
            else:
                # Try base-class schema fallback at the root level
                base_cls: Optional[Type[Any]] = None
                if isinstance(root_class, str):
                    base_name = _registry_get_base_name(registry, root_class)
                    if base_name:
                        base_cls = _registry_get_class(registry, base_name)
                else:
                    bases = getattr(cls, "__bases__", ())
                    if bases:
                        base_cls = bases[0]

                if base_cls is not None:
                    base_schema_attr = getattr(base_cls, "__spx_definition_schema__", None)
                    try:
                        base_schema = base_schema_attr() if callable(base_schema_attr) else (
                            base_schema_attr if isinstance(base_schema_attr, dict) else None
                        )
                    except Exception:
                        base_schema = None
                    if isinstance(base_schema, dict):
                        base_errors = validate_with_jsonschema(definition, base_schema, (), registry=registry)
                        if base_errors:
                            return failure(base_errors)

    errors: List[ValidationError] = []

    def _walk(node: Any, path: JsonPath) -> None:
        """Depth-first traversal over dicts/lists; validate when a key matches a registered class.
        The traversal is intentionally generic: no knowledge of section names or shapes.
        """
        if isinstance(node, dict):
            for k, v in node.items():
                cls = _registry_get_class(registry, str(k))
                if cls is not None:
                    schema_attr = getattr(cls, "__spx_definition_schema__", None)
                    has_schema = callable(schema_attr) or isinstance(schema_attr, dict)

                    # Scope control: "value" (default) or "parent"
                    scope = getattr(cls, "__spx_validation_scope__", "value")
                    target_node = node if scope == "parent" else v
                    # Special-case: parent scope but the node is a single-key wrapper
                    if (
                        scope == "parent"
                        and isinstance(node, dict)
                        and len(node) == 1
                        and isinstance(v, dict)
                        and "hooks" in path  # limit unwrapping to hook wrapper contexts
                    ):
                        target_node = v

                    if has_schema:
                        res = validate_component_definition(cls, target_node, registry=registry, path=path + (k,))
                        if not res.ok:
                            errors.extend(res.errors)
                    else:
                        # No schema on this class — try base-class schema fallback
                        base_name = _registry_get_base_name(registry, str(k))
                        if base_name:
                            base_cls = _registry_get_class(registry, base_name)
                            if base_cls is not None:
                                base_schema_attr = getattr(base_cls, "__spx_definition_schema__", None)
                                try:
                                    base_schema = base_schema_attr() if callable(base_schema_attr) else (
                                        base_schema_attr if isinstance(base_schema_attr, dict) else None
                                    )
                                except Exception:
                                    base_schema = None
                                if isinstance(base_schema, dict):
                                    base_errors = validate_with_jsonschema(target_node, base_schema, path + (k,), registry=registry)
                                    if base_errors:
                                        errors.extend(base_errors)
                # 2) Recurse regardless (schemas may or may not validate inner nodes)
                _walk(v, path + (k,))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                _walk(item, path + (i,))
        else:
            # primitives: nothing to walk
            return
    _walk(definition, ())

    return success() if not errors else failure(errors)
