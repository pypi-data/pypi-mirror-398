# SPDX-License-Identifier: MIT
# JSON Schema backend for SPX validation engine (Etap A).
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from jsonschema import Draft202012Validator, validators, exceptions
import re

from .errors import ValidationError, ValidationCode

__all__ = ["validate_with_jsonschema"]


# ------------------------------ helpers ------------------------------

def _schema_for(registry: Any, class_or_name: Any) -> Dict[str, Any]:
    """
    Return JSON Schema dict for a class or class-name from the registry.
    If class has no schema, return an empty schema (accept anything).
    """
    cls = class_or_name if isinstance(class_or_name, type) else registry.get_class(class_or_name)
    schema_attr = getattr(cls, "__spx_definition_schema__", None)
    schema = schema_attr() if callable(schema_attr) else schema_attr
    return schema if isinstance(schema, dict) else {}


def _coerce_inline_child(item: Any, expected_class: str | None = None) -> Tuple[str, Any, str]:
    """
    Recognize allowed child shapes and return (class_name, definition, shape).
    Shapes:
      - {"Child": {...}}                           -> ("Child", {...}, "single-key")  [only if expected_class is None or equals "Child"]
      - {"class": "Child", "definition": {...}}    -> ("Child", {...}, "explicit-def")
      - {"class": "Child", ...inline...}           -> ("Child", {...inline...}, "inline")
    If shape not recognized, return ("", item, "invalid").
    """
    if not isinstance(item, dict):
        return ("", item, "invalid")

    # single-key style: {"Child": {...}}; only accept as wrapper when it matches the expected class (if provided)
    if "class" not in item and len(item) == 1:
        k, v = next(iter(item.items()))
        if expected_class is None or k == expected_class:
            return (k, v, "single-key")
        # Unexpected single-key -> treat as bare definition (invalid wrapper)
        return ("", item, "invalid")

    # explicit class + definition
    if "class" in item and "definition" in item and isinstance(item["definition"], dict):
        return (item.get("class"), item["definition"], "explicit-def")

    # inline class + fields
    if "class" in item:
        data = {k: v for k, v in item.items() if k != "class"}
        return (item.get("class"), data, "inline")

    return ("", item, "invalid")


# ----------------------- validator factory & mapping ----------------------

def _make_validator_class(registry: Any):
    """Create a jsonschema Validator class with SPX custom keywords.

    The `registry` is captured via closure so we don't have to mutate the
    validator instance (which is disallowed by jsonschema's C-extensions in
    some environments).
    """

    def _x_spx_child_class(validator, class_name, instance, schema):
        """Validate that `instance` conforms to the schema of `class_name`.

        Accepted shapes:
          1) bare definition (e.g. { ... } or scalar)          -> validate directly
          2) {"Child": {...}}                                -> enforce Child match, then validate {...}
          3) {"class": "Child", "definition": {...}}       -> enforce Child match, then validate {...}
          4) {"class": "Child", ...inline...}               -> enforce Child match, then validate inline dict
        """
        # Resolve target class schema (and fail clearly if schema refers to unknown class)
        try:
            sub_schema = _schema_for(registry, class_name)
        except Exception:
            err = exceptions.ValidationError(f"unknown class in schema: '{class_name}'")
            err._spx_code = "SCHEMA_VIOLATION"
            yield err
            return

        # Detect inline/single‑key/explicit shapes
        cls_name, subdef, _shape = _coerce_inline_child(instance, expected_class=class_name)

        if cls_name:
            # We have an explicit class on the instance — verify it matches expected
            if cls_name != class_name:
                # Distinguish between unknown class vs. wrong-but-known class
                try:
                    registry.get_class(cls_name)
                    # Known but different → schema violation at current path
                    e = exceptions.ValidationError(
                        f"expected class '{class_name}', got '{cls_name}'"
                    )
                    e._spx_code = "SCHEMA_VIOLATION"
                    yield e
                    # And still validate the provided definition against the *expected* schema
                    # to surface child-level problems (e.g. TYPE_MISMATCH) when present.
                    for e2 in validator.descend(subdef, sub_schema):
                        yield e2
                except Exception:
                    # Unknown class on the instance
                    e = exceptions.ValidationError(f"unknown class '{cls_name}'")
                    e._spx_code = "UNKNOWN_CLASS"
                    yield e
                    # Additionally, validate provided definition against the expected schema
                    # so child-level issues (e.g. type mismatches) are still reported.
                    for e2 in validator.descend(subdef, sub_schema):
                        yield e2
                return

            # Class matches → validate *extracted* definition against the target schema
            for e in validator.descend(subdef, sub_schema):
                yield e
            return

        # No recognizable wrapper → treat `instance` as a bare definition for the expected class
        for e in validator.descend(instance, sub_schema):
            yield e

    def _x_spx_children_of(validator, base_class, instance, schema):
        """Validate mapping: name -> child instance of class `base_class`."""
        expected_schema = _schema_for(registry, base_class)
        if not isinstance(instance, dict):
            yield exceptions.ValidationError("must be object")
            return

        for key, raw in instance.items():
            cls_name, subdef, _shape = _coerce_inline_child(raw)
            # Invalid child shape (neither {"Class": {...}} nor {"class": "Class", ...})
            if not cls_name:
                # Use a schema that also asserts the instance is an object so scalars fail too
                invalid_shape_schema = {"type": "object", "maxProperties": 0}
                for e in validator.descend(raw, invalid_shape_schema, path=key):
                    e._spx_code = "SCHEMA_VIOLATION"
                    e.message = ("invalid child shape: expected "
                                 "{'Class': {...}} or {'class': 'Class', ...}")
                    yield e
                continue

            if cls_name != base_class:
                # Unknown class? -> UNKNOWN_CLASS (path ends with offending key)
                try:
                    registry.get_class(cls_name)
                    # Known class but not the expected base → force a violation at this key
                    for e in validator.descend(raw, {"maxProperties": 0}, path=key):
                        e._spx_code = "SCHEMA_VIOLATION"
                        e.message = f"expected class '{base_class}', got '{cls_name}'"
                        yield e
                    # Also validate the provided definition against the expected schema
                    # to expose nested issues like TYPE_MISMATCH alongside the class mismatch.
                    for e2 in validator.descend(subdef, expected_schema, path=key):
                        yield e2
                except Exception:
                    # Force a failing check just to attach correct path, then tag code
                    for e in validator.descend(raw, {"maxProperties": 0}, path=key):
                        e._spx_code = "UNKNOWN_CLASS"
                        e.message = f"unknown class '{cls_name}'"
                        yield e
                    # Additionally, validate the provided definition against expected schema
                    for e2 in validator.descend(subdef, expected_schema, path=key):
                        yield e2
                continue

            for e in validator.descend(subdef, expected_schema, path=key):
                yield e

    def _x_spx_list_of(validator, base_class, instance, schema):
        """Validate list of child instances of class `base_class`, with same shapes."""
        expected_schema = _schema_for(registry, base_class)
        if not isinstance(instance, list):
            yield exceptions.ValidationError("must be array")
            return

        for idx, raw in enumerate(instance):
            cls_name, subdef, _shape = _coerce_inline_child(raw)
            # Invalid child shape (neither {"Class": {...}} nor {"class": "Class", ...})
            if not cls_name:
                # Use a schema that also asserts the instance is an object so scalars fail too
                invalid_shape_schema = {"type": "object", "maxProperties": 0}
                for e in validator.descend(raw, invalid_shape_schema, path=idx):
                    e._spx_code = "SCHEMA_VIOLATION"
                    e.message = ("invalid child shape: expected "
                                 "{'Class': {...}} or {'class': 'Class', ...}")
                    yield e
                continue

            if cls_name != base_class:
                try:
                    registry.get_class(cls_name)
                    for e in validator.descend(raw, {"maxProperties": 0}, path=idx):
                        e._spx_code = "SCHEMA_VIOLATION"
                        e.message = f"expected class '{base_class}', got '{cls_name}'"
                        yield e
                    # Also validate the provided definition against the expected schema
                    # so nested TYPE_MISMATCH/other errors are surfaced.
                    for e2 in validator.descend(subdef, expected_schema, path=idx):
                        yield e2
                except Exception:
                    for e in validator.descend(raw, {"maxProperties": 0}, path=idx):
                        e._spx_code = "UNKNOWN_CLASS"
                        e.message = f"unknown class '{cls_name}'"
                        yield e
                    # Additionally, validate the provided definition against expected schema
                    for e2 in validator.descend(subdef, expected_schema, path=idx):
                        yield e2
                continue

            for e in validator.descend(subdef, expected_schema, path=idx):
                yield e

    def _x_spx_firstkey_target_pattern(validator, pattern, instance, schema):
        """Validate that the *first* key's value in an object matches a regex pattern.
        Intended for dynamic action items where the first key is an action name
        and its value is the target reference (e.g. $in/$out/$attr/$ext).
        """
        if not isinstance(instance, dict) or not instance:
            err = exceptions.ValidationError("must be object with at least one key")
            err._spx_code = "SCHEMA_VIOLATION"
            yield err
            return
        first_key = next(iter(instance))
        # Build a minimal object schema that anchors the error path to the first key
        sub_schema = {
            "type": "object",
            "required": [str(first_key)],
            "properties": {str(first_key): {"type": "string", "pattern": pattern}},
        }
        for e in validator.descend(instance, sub_schema):
            yield e

    def _x_spx_firstkey_type(validator, expected_type, instance, schema):
        """Validate that the first key's value in an object has the given JSON Schema type.
        Usage in schema: {"x-spx-firstkey-type": "string"}
        """
        if not isinstance(instance, dict) or not instance:
            err = exceptions.ValidationError("must be object with at least one key")
            err._spx_code = "SCHEMA_VIOLATION"
            yield err
            return
        first_key = next(iter(instance))
        # Anchor error path to the first key by validating via a tiny object schema
        sub_schema = {
            "type": "object",
            "required": [str(first_key)],
            "properties": {str(first_key): {"type": str(expected_type)}},
        }
        for e in validator.descend(instance, sub_schema):
            yield e

    return validators.extend(
        Draft202012Validator,
        {
            "x-spx-child-class": _x_spx_child_class,
            "x-spx-children-of": _x_spx_children_of,
            "x-spx-list-of": _x_spx_list_of,
            "x-spx-firstkey-target-pattern": _x_spx_firstkey_target_pattern,
            "x-spx-firstkey-type": _x_spx_firstkey_type,
        },
    )


def _map_error(e: exceptions.ValidationError, base_path: Tuple[Any, ...]) -> ValidationError:
    """Map a jsonschema.ValidationError into our ValidationError.

    Special-cases:
      - `required`: append the missing key to the path
      - `additionalProperties`: append the extra key to the path
      - custom `_spx_code` hints from our keyword handlers
    """
    # Honor explicit SPX codes from custom keywords first
    code_hint = getattr(e, "_spx_code", None)
    if code_hint == "UNKNOWN_CLASS":
        code = ValidationCode.UNKNOWN_CLASS
        path = tuple(base_path) + tuple(e.path)
        return ValidationError(code=code, message=e.message, path=path)
    if code_hint == "SCHEMA_VIOLATION":
        code = ValidationCode.SCHEMA_VIOLATION
        path = tuple(base_path) + tuple(e.path)
        return ValidationError(code=code, message=e.message, path=path)

    # Fine-tuned handling for standard validators where jsonschema
    # doesn't include the problematic property name in `e.path`.
    if e.validator == "required":
        missing = None
        try:
            required_keys = e.validator_value  # list of required keys
            if isinstance(required_keys, (list, tuple)) and isinstance(e.instance, dict):
                # choose the first actually missing key
                for k in required_keys:
                    if k not in e.instance:
                        missing = k
                        break
                if missing is None and required_keys:
                    missing = required_keys[0]
        except Exception:
            pass
        if missing is None:
            # Fallback: parse from message: "'x' is a required property"
            try:
                parts = e.message.split("'")
                if len(parts) >= 3:
                    missing = parts[1]
            except Exception:
                pass
        path = tuple(base_path) + tuple(e.path) + ((missing,) if missing else ())
        return ValidationError(code=ValidationCode.MISSING_REQUIRED, message=e.message, path=path)

    if e.validator == "additionalProperties":
        extra = None
        ap = None
        # Try modern API first
        params = getattr(e, "params", None)
        if isinstance(params, dict):
            ap = params.get("additionalProperties")
        # If unavailable (older jsonschema), try to derive from message (supports 1 or many extras)
        if ap is None:
            try:
                # Extract all quoted tokens – many implementations quote offending keys
                quoted = re.findall(r"'([^']+)'", e.message or "")
                if len(quoted) > 1:
                    ap = quoted  # behave like list-of-extras
                elif len(quoted) == 1:
                    ap = quoted[0]
            except Exception:
                ap = None
        # Map ap -> extra (first offending key for path anchoring)
        if isinstance(ap, (list, tuple)) and ap:
            extra = ap[0]
        elif isinstance(ap, str):
            extra = ap
        # Final fallback: leave extra None (path will end at the object), best-effort
        path = tuple(base_path) + tuple(e.path) + ((extra,) if extra else ())
        return ValidationError(code=ValidationCode.ADDITIONAL_PROPERTY, message=e.message, path=path)

    # Default mapping for the rest
    mapping = {
        "type": ValidationCode.TYPE_MISMATCH,
        "enum": ValidationCode.SCHEMA_VIOLATION,
        "const": ValidationCode.SCHEMA_VIOLATION,
        "pattern": ValidationCode.SCHEMA_VIOLATION,
        "minItems": ValidationCode.SCHEMA_VIOLATION,
        "maxItems": ValidationCode.SCHEMA_VIOLATION,
    }
    code = mapping.get(e.validator, ValidationCode.SCHEMA_VIOLATION)
    path = tuple(base_path) + tuple(e.path)
    return ValidationError(code=code, message=e.message, path=path)


def validate_with_jsonschema(
    instance: Any,
    schema: Dict[str, Any],
    path: Tuple[Any, ...] = (),
    *,
    registry: Any,
) -> List[ValidationError]:
    """
    Validate `instance` against `schema` using our extended JSON Schema validator.
    Returns a list of mapped `ValidationError`s.

    Args:
        instance: The value to validate.
        schema: The JSON Schema to validate against.
        path: Tuple representing the base path in the instance (default is ()).
        registry: (keyword-only) The registry object for class lookups and custom keywords.
    """
    V = _make_validator_class(registry)
    v = V(schema)
    return [_map_error(err, path) for err in v.iter_errors(instance)]
