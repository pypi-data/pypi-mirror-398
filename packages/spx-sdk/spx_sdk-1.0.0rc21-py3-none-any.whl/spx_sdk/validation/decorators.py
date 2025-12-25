# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from __future__ import annotations

from typing import Any, Callable, TypeVar, Dict, Union, List

__all__ = [
    "definition_schema",
    "definition_validator",
]

T = TypeVar("T", bound=type)


def definition_schema(
    schema: Union[
        Dict[str, Any],
        List[Any],
        Callable[[], Union[Dict[str, Any], List[Any]]],
    ],
    *,
    replace: bool = True,
    validation_scope: str | None = None,
) -> Callable[[T], T]:
    """
    Class decorator that attaches a **JSON Schema** describing the expected
    structure of the class `definition` (dict passed to `_populate`). The schema
    can be a dict or a callable returning a dict.

    Usage:
        >>> @definition_schema({
        ...     "type": "object",
        ...     "properties": {"default": {"type": ["number", "string", "boolean", "null"]}},
        ...     "additionalProperties": True,
        ... })
        ... class SpxAttribute(...):
        ...     pass

        List (array) schema:
            >>> @definition_schema([
            ...     {"type": "object", "properties": {"name": {"type": "string"}}}
            ... ])
            ... class SomeListContainer(...):
            ...     pass

        Lazy (callable) schema:
            >>> def _schema():
            ...     return {
            ...         "type": "object",
            ...         "properties": {"default": {"type": "number"}},
            ...         "additionalProperties": False,
            ...     }
            >>> @definition_schema(_schema)
            ... class SpxAttribute(...):
            ...     pass

    The schema is stored on the class under the attribute
    `__spx_definition_schema__`. A validation engine can later retrieve it
    and validate raw dicts *before* instantiation.

    Parameters
    ----------
    schema:
        A Python **dict** (object schema) or **list** (array schema) following JSON Schema (draft‑2020‑12 in our backend),
        or a **callable** returning such a dict/list. The schema may use SPX extensions like
        `x-spx-child-class`, `x-spx-children-of`, or `x-spx-list-of` handled by the JSON Schema backend.
    replace:
        If False and the class already defines a schema, keep the original and
        do not overwrite. Defaults to True.
    validation_scope:
        Optional scope for validation target. When set to "parent", a validation engine may
        validate the **parent mapping** (e.g., the full action object containing this field)
        instead of just the field value. Supported values:
        - "value" (default): validate the field value itself
        - "parent": validate the parent mapping that contains this field
    """
    if not (isinstance(schema, (dict, list)) or callable(schema)):
        raise TypeError("definition_schema() expects a dict/list or a callable returning a dict/list")

    def _decorate(cls: T) -> T:
        if not replace and hasattr(cls, "__spx_definition_schema__"):
            return cls
        # If callable provided, store as staticmethod to avoid accidental binding.
        value = staticmethod(schema) if callable(schema) else schema
        setattr(cls, "__spx_definition_schema__", value)
        # Optionally set validation scope ("value" or "parent")
        if validation_scope is not None:
            if validation_scope not in ("value", "parent"):
                raise ValueError("validation_scope must be 'value' or 'parent'")
            if not (hasattr(cls, "__spx_validation_scope__") and not replace):
                setattr(cls, "__spx_validation_scope__", validation_scope)
        return cls

    return _decorate


def definition_validator(validator: Callable[..., Any], *, replace: bool = True) -> Callable[[T], T]:
    """
    Class decorator that attaches a **custom validator callable** to the class.

    The callable signature is intentionally loose to avoid hard deps:
        validator(cls, definition, registry, path) -> List[ValidationError]

    Where:
      - `cls` is the class being validated,
      - `definition` is the raw dict to validate,
      - `registry` is a registry-like object (or None) used to resolve classes,
      - `path` is a tuple representing the current JSON path (for error paths).

      The validator may return a single `ValidationError`, an iterable of `ValidationError`,
      or a `ValidationResult`. The validation engine normalizes these forms internally.

    The validator is stored as a `staticmethod` under the attribute
    `__spx_definition_validator__` and can be invoked by the validation engine
    without instantiating the class.

    Usage:
        >>> def _validate_attribute(cls, definition, registry, path):
        ...     return []  # return a list of ValidationError
        ...
        >>> @definition_validator(_validate_attribute)
        ... class SpxAttribute(...):
        ...     pass
    """
    if not callable(validator):
        raise TypeError("definition_validator() expects a callable")

    def _decorate(cls: T) -> T:
        if not replace and hasattr(cls, "__spx_definition_validator__"):
            return cls
        # store as staticmethod to avoid accidental binding
        setattr(cls, "__spx_definition_validator__", staticmethod(validator))
        return cls

    return _decorate
