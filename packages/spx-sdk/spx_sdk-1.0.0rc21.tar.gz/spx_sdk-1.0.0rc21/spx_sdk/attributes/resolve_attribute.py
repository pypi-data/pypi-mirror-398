# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import re
from typing import Tuple, Any, Optional, Union
from spx_sdk.components import SpxComponent
from spx_sdk.attributes import SpxAttribute
from spx_sdk.attributes.attribute import InternalAttributeWrapper, ExternalAttributeWrapper, StaticAttributeWrapper


# Define regex patterns to match attribute references
ATTRIBUTE_REFERENCE_PATTERN = re.compile(r'[#\$@](attr|internal|external|in|out|ext)\(([^)]+)\)')
# Nested chain references like $(.comp1.comp2.attr) / $(~.foo) / $(..foo), allowing whitespace inside
NESTED_ATTRIBUTE_PATTERN = re.compile(r'\$\(\s*(?:~|\.)[^)]+\)')


def _resolve_base_and_segments(instance: SpxComponent, attribute_string: str) -> tuple[Optional[SpxComponent], list[str]]:
    """
    Interpret leading '~' or dot prefixes and split the path into segments.
    - '~' starts from the root component
    - leading dots: '.' → current component, '..' → one level up, '...' → two levels up, etc.
    Returns the base component to start traversal and the remaining path segments.
    """
    if not isinstance(attribute_string, str):
        return None, []

    current = instance
    path = attribute_string

    # Absolute-from-root: ~.foo.bar
    if path.startswith('~'):
        current = instance.get_root()
        path = path[1:]
        if path.startswith('.'):
            path = path[1:]
    elif path.startswith('.'):
        # Count leading dots: '.' -> stay, '..' -> up 1, '...' -> up 2, etc.
        m = re.match(r'^(\.+)(.*)$', path)
        dots = len(m.group(1))
        path = m.group(2)
        if dots > 1:
            for _ in range(dots - 1):
                current = current.parent if current is not None else None
        if path.startswith('.'):
            path = path[1:]

    segments = path.split('.') if path else []
    return current, segments


def _descend_component(current: SpxComponent, segment: str) -> Optional[SpxComponent]:
    """
    Move from the current component to a named child/instance/component attribute.
    """
    if current is None:
        return None
    # Prefer regular children
    next_comp = current.get(segment, None)
    if next_comp is not None:
        return next_comp
    # Try instances container
    instances_cont = current.get("instances", None)
    if instances_cont and segment in instances_cont:
        return instances_cont.get(segment)
    # Finally, allow plain attributes that are themselves components
    candidate = getattr(current, segment, None)
    if isinstance(candidate, SpxComponent):
        return candidate
    return None


def _resolve_wrapper_in_component(
    component: SpxComponent,
    attr_path: str,
    attr_type: str
) -> Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper, StaticAttributeWrapper]]:
    """
    Resolve an attribute reference within a single component, supporting
    relative ('..') and root ('~') prefixes plus component field fallback.
    """
    base, segments = _resolve_base_and_segments(component, attr_path)
    if base is None or not segments:
        return None

    current = base
    for segment in segments[:-1]:
        current = _descend_component(current, segment)
        if current is None:
            return None

    last_seg = segments[-1]
    attrs_cont = None
    if hasattr(current, "get"):
        try:
            attrs_cont = current.get("attributes", None)
        except TypeError:
            # Some leaf components (e.g., SpxAttribute) expose a value-style get()
            # that doesn't accept (key, default); ignore and continue upward.
            attrs_cont = None
    if attrs_cont is not None:
        attr_obj = attrs_cont.get(last_seg, None)
        if attr_obj is not None:
            return attr_obj.get_wrapper(attr_type)

    if hasattr(current, last_seg):
        return StaticAttributeWrapper(current, last_seg)

    return None


def is_attribute_reference(reference: str) -> Tuple[bool, str, Optional[str]]:
    """
    Check if the reference is an attribute reference and parse it.

    Args:
        reference (str): The reference string to check.

    Returns:
        Tuple[bool, str, Optional[str]]:
            - bool: whether `reference` is an attribute reference.
            - str: the parsed attribute string.
            - Optional[str]: the reference type ('attr', 'internal', or 'external'), or None.
    """
    is_attr = False
    attr_type = None
    attr_string = reference

    if isinstance(reference, str):
        match = ATTRIBUTE_REFERENCE_PATTERN.match(reference)
        if match:
            is_attr = True
            raw_type = match.group(1)
            attr_string = match.group(2)
            # Map to 'external' only if raw_type indicates external
            if raw_type in ("external", "out", "ext"):
                attr_type = "external"
            else:
                attr_type = "internal"
        elif '.' in reference:
            is_attr = True
            attr_type = "internal"
            attr_string = reference

    return is_attr, attr_string, attr_type


def find_attribute(instance: SpxComponent, attribute_string: str) -> Optional[SpxAttribute]:
    """
    Find and return the attribute object based on a simple name or a dot-separated path.

    Delegates:
      - dot-containing strings → nested lookup across children/instances
      - simple names → lookup in the 'attributes' container of the instance
    """
    if '.' in attribute_string:
        return _find_nested_attribute(instance, attribute_string)
    else:
        return _find_simple_attribute(instance, attribute_string)


def _find_simple_attribute(instance: SpxComponent, attr_name: str) -> Optional[SpxAttribute]:
    """
    Lookup an attribute by name in the 'attributes' container of the given instance.
    """
    attrs_cont = instance.get("attributes", None)
    if attrs_cont is None:
        raise ValueError(f"Component '{instance.name}' has no 'attributes' container.")
    return attrs_cont.get(attr_name, None)


def _find_nested_attribute(instance: SpxComponent, attribute_string: str) -> Optional[SpxAttribute]:
    """
    Lookup an attribute via a dot-separated path through component children, falling back
    to an 'instances' container if necessary, and finally in the 'attributes' container.
    """
    base, segments = _resolve_base_and_segments(instance, attribute_string)
    if base is None or not segments:
        return None

    current = base
    for segment in segments[:-1]:
        current = _descend_component(current, segment)
        if current is None:
            return None

    # Final segment should be an attribute name
    attr_name = segments[-1]
    attrs_cont = current.get("attributes", None)
    if attrs_cont is None:
        raise ValueError(f"Component '{current.name}' has no 'attributes' container.")
    return attrs_cont.get(attr_name, None)


def resolve_attribute_reference(
    instance: SpxComponent,
    attribute_name: str
) -> Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper]]:
    """
    Resolve the attribute reference and return the attribute object and its type.

    Args:
        instance: The instance containing the attribute.
        attribute_name (str): The attribute reference string.

    Returns:
        Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper]]:
            A wrapper for the resolved attribute, or None if not an attribute reference.
    """
    is_attr, attr_string, attr_type = is_attribute_reference(attribute_name)
    if not is_attr:
        return None
    wrapper = _resolve_wrapper_in_component(instance, attr_string, attr_type)
    if wrapper is None:
        raise ValueError(f"Attribute '{attr_string}' not found in instance '{instance.name}'.")
    return wrapper


def get_attribute_value(attribute: SpxAttribute, attr_type: str) -> Any:
    """
    Get the value of the attribute based on its type.

    Args:
        attribute (Attribute): The attribute object.
        attr_type (str): The attribute type ('internal' or 'external').

    Returns:
        Any: The attribute value.

    Raises:
        ValueError: If the attribute is None.
    """
    if attribute is None:
        raise ValueError("Attribute cannot be None when getting its value.")
    if attr_type == "internal":
        return attribute.internal_value
    else:
        return attribute.external_value


def set_attribute_value(attribute: SpxAttribute, attr_type: str, value: Any) -> None:
    """
    Set the value of the attribute based on its type.

    Args:
        attribute (Attribute): The attribute object.
        attr_type (str): The attribute type ('internal' or 'external').
        value (Any): The value to set.

    Raises:
        ValueError: If the attribute is None.
    """
    if attribute is None:
        raise ValueError("Attribute cannot be None when setting its value.")
    if attr_type == "internal":
        attribute.internal_value = value
    else:
        attribute.external_value = value


def resolve_reference(instance: SpxComponent, reference: str) -> Any:
    """
    Resolve the reference to its actual value.

    Args:
        instance: The instance containing the reference.
        reference (str): The reference string.

    Returns:
        Any: The resolved value if it was an attribute reference, otherwise the original `reference` string.
    """
    is_attr, attr_string, attr_type = is_attribute_reference(reference)
    if is_attr:
        wrapper = _resolve_wrapper_in_component(instance, attr_string, attr_type)
        if wrapper is None:
            return reference
        return wrapper.get()
    return reference


def resolve_attribute_reference_hierarchical(
    instance: Optional[SpxComponent],
    reference: str
) -> Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper]]:
    """
    Resolve an attribute reference by searching up the component hierarchy.
    Starting from `instance`, traverse parent links until an attributes container
    with the named attribute is found. Returns the corresponding wrapper or None.
    """
    # Parse reference syntax
    is_attr, attr_string, attr_type = is_attribute_reference(reference)
    if not is_attr or attr_type is None:
        return None

    # Walk up from the given instance to root
    current = instance
    while current is not None:
        wrapper = _resolve_wrapper_in_component(current, attr_string, attr_type)
        if wrapper is not None:
            return wrapper
        # Allow dotted component paths to fallback to StaticAttributeWrapper resolution
        try:
            nested_wrapper = resolve_nested_chain_reference(current, f"$({'.' + attr_string})")
        except Exception:
            nested_wrapper = None
        if nested_wrapper is not None:
            return nested_wrapper
        current = current.parent  # move to next parent

    return None


def substitute_attribute_references_hierarchical(
    instance: Optional[SpxComponent],
    text: str
) -> str:
    """
    Replace all attribute reference patterns in `text` with their resolved values.
    Uses hierarchical resolution on `$attr(...)`, `$ext(...)`, etc., and nested
    forms `$(...)` (with '.', '..', '~') starting from `instance`.
    Args:
        instance (SpxComponent): Component context to resolve attribute references.
        text (str): The input string containing reference patterns.

    Returns:
        str: A new string with each reference replaced by repr(value).
    """
    wrappers = extract_attribute_wrappers_hierarchical(instance, text)
    return substitute_with_wrappers(text, wrappers)


def extract_attribute_wrappers_hierarchical(
    instance: SpxComponent,
    text: str
) -> list[tuple[str, Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper, StaticAttributeWrapper]]]]:
    """
    For each attribute reference or nested chain in `text`, resolve its wrapper hierarchically.
    Returns a list of (ref, wrapper) tuples, in order of appearance.
    """
    results = []
    # Patterns to match simple attrs and nested chains
    nested_pattern = NESTED_ATTRIBUTE_PATTERN
    simple_pattern = ATTRIBUTE_REFERENCE_PATTERN

    # Gather all matches with their positions and type
    matches = []
    for m in simple_pattern.finditer(text):
        matches.append((m.start(), m.group(0), 'simple'))
    for m in nested_pattern.finditer(text):
        matches.append((m.start(), m.group(0), 'nested'))

    # Sort by appearance in text
    matches.sort(key=lambda x: x[0])

    for _, ref, kind in matches:
        if kind == 'nested':
            try:
                wrapper = resolve_nested_chain_reference(instance, ref)
            except Exception:
                wrapper = None
        else:
            try:
                wrapper = resolve_attribute_reference_hierarchical(instance, ref)
            except Exception:
                wrapper = None
        results.append((ref, wrapper))
    return results


def substitute_with_wrappers(
    text: str,
    wrappers: list[tuple[str, Optional[Union[InternalAttributeWrapper, ExternalAttributeWrapper]]]]
) -> str:
    """
    Replace all occurrences of each reference in `text` with repr(wrapper.get()) if possible.
    Leaves refs unchanged if wrapper is None or .get() raises.
    """
    result = text
    for ref, wrapper in wrappers:
        if wrapper is not None:
            try:
                value = wrapper.get()
            except Exception:
                continue
            # Replace all exact occurrences of ref with repr(value)
            result = result.replace(ref, repr(value))
    return result


# --- Nested chain reference resolver ---
def resolve_nested_chain_reference(
    instance: SpxComponent,
    reference: str
) -> Any:
    """
    Resolve a nested chain reference of the form '$(.comp1.comp2.attr)', with support for
    '~' (from root) and leading dots inside the parens ('.' current, '..' up 1, '...' up 2, etc.).
    Starts from the resolved base component and follows each dot-separated segment, falling
    back up the hierarchy (parent, parent.parent, ...) if the path is not found at the base.
    Returns a StaticAttributeWrapper for the final attribute/property.
    """
    # Check pattern: must start with '$(' and end with ')'
    if not (isinstance(reference, str) and reference.startswith('$(') and reference.endswith(')')):
        raise ValueError(f"Invalid nested reference syntax: {reference!r}")
    # Extract inner path and ensure it begins with '.'
    path = reference[2:-1].strip()
    base, segments = _resolve_base_and_segments(instance, path)
    if base is None or not segments:
        raise ValueError(f"Cannot resolve nested reference '{reference}'")
    current_base: Any = base

    def _traverse(start):
        current = start
        for seg in segments[:-1]:
            if hasattr(current, 'children') and seg in current.children:
                current = current.children[seg]
            elif hasattr(current, seg):
                current = getattr(current, seg)
            else:
                return None
        last_seg = segments[-1]
        if hasattr(current, last_seg):
            return StaticAttributeWrapper(current, last_seg)
        return None

    while current_base is not None:
        wrapper = _traverse(current_base)
        if wrapper is not None:
            return wrapper
        current_base = getattr(current_base, "parent", None)

    raise ValueError(f"Cannot resolve nested reference '{reference}'")
