# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from spx_sdk.registry import register_class, load_module_from_path
from spx_sdk.components import SpxComponent
from spx_sdk.attributes import SpxAttribute
from spx_sdk.attributes.resolve_attribute import (
    ATTRIBUTE_REFERENCE_PATTERN,
    extract_attribute_wrappers_hierarchical,
    substitute_with_wrappers,
)
from spx_sdk.validation.decorators import definition_schema


@register_class(name="python_file")
@register_class(name="import")
@definition_schema({
    "type": "object",
    "description": "Mapping of Python file paths to import specifications.",
    "$defs": {
        "AnyJSON": {
            "anyOf": [
                {"type": "null"},
                {"type": "boolean"},
                {"type": "number"},
                {"type": "string"},
                {"type": "array"},
                {"type": "object"}
            ]
        },
        "Args": {"type": "array", "items": {"$ref": "#/$defs/AnyJSON"}},
        "Kwargs": {"type": "object"},
        "MethodObject": {
            "type": "object",
            "required": ["method"],
            "properties": {
                "method": {"type": "string"},
                "args": {"$ref": "#/$defs/Args"},
                "kwargs": {"$ref": "#/$defs/Kwargs"}
            },
            "additionalProperties": False
        },
        "MethodBinding": {
            "oneOf": [
                {"type": "string"},
                {"$ref": "#/$defs/MethodObject"}
            ]
        },
        "MethodsMap": {
            "type": "object",
            "description": "Lifecycle bindings for start/run/pause/stop.",
            "patternProperties": {
                "^(start|run|pause|stop)$": {"$ref": "#/$defs/MethodBinding"}
            },
            "additionalProperties": False
        },
        "AttrProperty": {
            "type": "object",
            "required": ["property"],
            "properties": {"property": {"type": "string"}},
            "additionalProperties": False
        },
        "AttrGetter": {
            "type": "object",
            "required": ["getter"],
            "properties": {"getter": {"type": "string"}, "setter": {"type": "string"}},
            "additionalProperties": False
        },
        "AttrBinding": {"oneOf": [{"$ref": "#/$defs/AttrProperty"}, {"$ref": "#/$defs/AttrGetter"}]},
        "AttributesMap": {"type": "object", "additionalProperties": {"$ref": "#/$defs/AttrBinding"}},
        "InitSpec": {
            "type": "object",
            "properties": {"args": {"$ref": "#/$defs/Args"}, "kwargs": {"$ref": "#/$defs/Kwargs"}},
            "additionalProperties": False
        },
        "ImportSpec": {
            "type": "object",
            "required": ["class", "attributes"],
            "properties": {
                "class": {"type": "string", "description": "Name of the class to import from the module."},
                "init": {"$ref": "#/$defs/InitSpec"},
                "methods": {"$ref": "#/$defs/MethodsMap"},
                "attributes": {"$ref": "#/$defs/AttributesMap"}
            },
            "additionalProperties": False
        }
    },
    "patternProperties": {
        r".+\.py$": {"$ref": "#/$defs/ImportSpec"}
    },
    "additionalProperties": False
})
class PythonFile(SpxComponent):
    """
    PythonFile component for dynamic loading and lifecycle management of Python classes from files.

    Extended definition schema supports an optional "methods" mapping per class, allowing you to bind
    lifecycle events ("start", "run", "pause", "stop") to arbitrary class methods, with optional arguments/kwargs.

    Example definition:
    {
        "path/to/file.py": {
            "class": "MyClass",
            "init": { ... },
            "methods": {
                "start": "custom_start",              # Shorthand: just method name
                "run": { "method": "custom_run", "args": [1], "kwargs": {"foo": "bar"} },   # Verbose form
                "pause": { "method": "custom_pause" },
                "stop": { "method": "cleanup" }
            },
            ...
        }
    }

    Supported lifecycle names: "start", "run", "pause", "stop"
    - Each can be mapped to a method on the class, with optional "args" (list) and "kwargs" (dict).
    - If not specified, lifecycle methods fallback to calling instance.start(), instance.run(), etc. if present.
    - The binding is normalized so all entries have: "method" (str), "args" (list), "kwargs" (dict).
    - Args/kwargs in "methods" may include attribute references (e.g., "$attr(foo)" or expressions like
      "$attr(a) + 3"). These are resolved at call time hierarchically, analogous to Action.
    """

    def _populate(self, definition: dict) -> None:
        # Holds class_name: instance
        self.class_instances = {}
        # Holds lifecycle: list of binding dicts
        self._method_bindings = {"start": [], "run": [], "pause": [], "stop": []}
        for module_path, params in definition.items():
            params["path"] = module_path
            class_instance = self.create_instance_from_module(params)
            class_name = params["class"]
            self.class_instances[class_name] = class_instance

            # Parse optional "methods" mapping for lifecycle bindings
            methods_map = params.get("methods", {})
            for lifecycle in ("start", "run", "pause", "stop"):
                binding_entry = methods_map.get(lifecycle, None)
                if binding_entry is None:
                    continue
                # Normalize to dict form
                if isinstance(binding_entry, str):
                    binding = {"method": binding_entry}
                elif isinstance(binding_entry, dict):
                    binding = dict(binding_entry)  # shallow copy
                else:
                    continue  # skip invalid
                # Ensure keys: method (str), args (list), kwargs (dict)
                binding["method"] = binding.get("method") or ""
                binding["args"] = list(binding.get("args", []))
                binding["kwargs"] = dict(binding.get("kwargs", {}))
                self._method_bindings[lifecycle].append({
                    "instance_key": class_name,
                    "instance": class_instance,
                    "method": binding["method"],
                    # Raw copies (strings/literals) for wrapper-based substitution
                    "raw_args": list(binding["args"]),
                    "raw_kwargs": dict(binding["kwargs"]),
                    # Wrapper caches (filled in prepare())
                    "arg_wrappers": {},   # index -> list[Tuple[ref, wrapper]]
                    "kwarg_wrappers": {},  # key   -> list[Tuple[ref, wrapper]]
                    # Working copies for static values (pre-evaluated)
                    "args": list(binding["args"]),
                    "kwargs": dict(binding["kwargs"]),
                })

    def _invoke_bound(self, lifecycle: str, *extra_args, **extra_kwargs):
        """
        Invoke all methods bound to the given lifecycle, passing extra_args/kwargs after binding's own.
        Returns a list of results or error dicts.
        """
        results = []
        bindings = self._method_bindings.get(lifecycle, [])
        for binding in bindings:
            method_name = binding["method"]
            instance = binding["instance"]
            func = getattr(instance, method_name, None)
            if not callable(func):
                continue
            # Resolve dynamic args/kwargs (attribute refs) + merge call-site params
            args, kwargs = self._resolve_binding_args_kwargs(binding, extra_args, extra_kwargs)
            try:
                res = func(*args, **kwargs)
                results.append(res)
            except Exception as e:
                results.append({"error": str(e), "method": method_name})
        return results

    def _fallback_invoke(self, lifecycle: str, *extra_args, **extra_kwargs):
        """
        If no bound methods are configured, call <lifecycle>() directly on each instance if present.
        Returns a list of results.
        """
        results = []
        for instance in self.class_instances.values():
            func = getattr(instance, lifecycle, None)
            if callable(func):
                try:
                    res = func(*extra_args, **extra_kwargs)
                    results.append(res)
                except Exception as e:
                    results.append({"error": str(e), "method": lifecycle})
        return results

    def _normalize_literal(self, value):
        """
        Evaluate simple Python literals from strings (e.g., "2", "true" -> True). Fallback to original value.
        Mirrors Action.resolve_param normalization.
        """
        if not isinstance(value, str):
            return value
        expr = value.replace("true", "True").replace("false", "False")
        try:
            return eval(expr)
        except Exception:
            return expr

    def _prepare_binding_wrappers(self, binding: dict) -> None:
        """
        For each arg/kwarg, extract wrappers if raw contains attribute refs; otherwise pre-evaluate static literals
        into working slots so resolution at runtime is cheap.
        """
        # Args
        arg_wrappers = {}
        for idx, raw in enumerate(binding.get("raw_args", [])):
            if isinstance(raw, str) and ATTRIBUTE_REFERENCE_PATTERN.search(raw or ""):
                wrappers = extract_attribute_wrappers_hierarchical(self.parent, raw)
                arg_wrappers[idx] = wrappers
            else:
                binding["args"][idx] = self._normalize_literal(raw)
        binding["arg_wrappers"] = arg_wrappers

        # Kwargs
        kwarg_wrappers = {}
        for key, raw in binding.get("raw_kwargs", {}).items():
            if isinstance(raw, str) and ATTRIBUTE_REFERENCE_PATTERN.search(raw or ""):
                wrappers = extract_attribute_wrappers_hierarchical(self.parent, raw)
                kwarg_wrappers[key] = wrappers
            else:
                binding["kwargs"][key] = self._normalize_literal(raw)
        binding["kwarg_wrappers"] = kwarg_wrappers

    def _resolve_binding_args_kwargs(self, binding: dict, extra_args, extra_kwargs):
        """
        Build final (args, kwargs) by applying wrappers to raw values where present, and using
        pre-evaluated static values otherwise. Then append/merge call-site parameters.
        """
        # Resolve args
        resolved_args = []
        for idx, raw in enumerate(binding.get("raw_args", [])):
            if idx in binding.get("arg_wrappers", {}):
                substituted = substitute_with_wrappers(raw, binding["arg_wrappers"][idx])
                resolved_args.append(self._normalize_literal(substituted))
            else:
                resolved_args.append(binding["args"][idx])
        # Append any extra positional args
        resolved_args.extend(list(extra_args) if extra_args else [])

        # Resolve kwargs
        resolved_kwargs = {}
        for key, raw in binding.get("raw_kwargs", {}).items():
            if key in binding.get("kwarg_wrappers", {}):
                substituted = substitute_with_wrappers(raw, binding["kwarg_wrappers"][key])
                resolved_kwargs[key] = self._normalize_literal(substituted)
            else:
                resolved_kwargs[key] = binding["kwargs"][key]
        # Merge call-site kwargs (caller wins)
        if extra_kwargs:
            resolved_kwargs.update(extra_kwargs)
        return resolved_args, resolved_kwargs

    def start(self, *args, **kwargs):
        """
        Call all configured start methods (or fallback to instance.start()).
        Returns list of results.
        """
        results = self._invoke_bound("start", *args, **kwargs)
        if not results:
            results = self._fallback_invoke("start", *args, **kwargs)
        return results

    def run(self, *args, **kwargs):
        """
        Call all configured run methods (or fallback to instance.run()).
        Returns list of results.
        """
        results = self._invoke_bound("run", *args, **kwargs)
        if not results:
            results = self._fallback_invoke("run", *args, **kwargs)
        return results

    def pause(self, *args, **kwargs):
        """
        Call all configured pause methods (or fallback to instance.pause()).
        Returns list of results.
        """
        results = self._invoke_bound("pause", *args, **kwargs)
        if not results:
            results = self._fallback_invoke("pause", *args, **kwargs)
        return results

    def stop(self, *args, **kwargs):
        """
        Call all configured stop methods (or fallback to instance.stop()).
        Returns list of results.
        """
        results = self._invoke_bound("stop", *args, **kwargs)
        if not results:
            results = self._fallback_invoke("stop", *args, **kwargs)
        return results

    def create_instance_from_module(self, module_info: dict):
        file_path = module_info["path"]
        class_name = module_info["class"]
        module = load_module_from_path(file_path)
        cls = getattr(module, class_name)

        # Extract custom init parameters if provided
        init_info = module_info.get("init", {})
        init_args = init_info.get("args", [])
        init_kwargs = init_info.get("kwargs", {})

        if SpxComponent in cls.__bases__:
            # Prepend root and definition for Item subclasses
            args = [self.get_root(), self.definition] + init_args
            class_instance = cls(*args, **init_kwargs)
        else:
            # Instantiate plain classes with provided args/kwargs
            class_instance = cls(*init_args, **init_kwargs)
        return class_instance

    def prepare(self):
        # Pre-extract wrappers and pre-evaluate static literals for bound method params
        for lifecycle in ("start", "run", "pause", "stop"):
            for binding in self._method_bindings.get(lifecycle, []):
                self._prepare_binding_wrappers(binding)

        # Attribute linking logic remains unchanged
        if isinstance(self.definition, dict):
            for module_path, params in self.definition.items():
                for attr, methods in params["attributes"].items():
                    class_name = params["class"]
                    attribute: SpxAttribute = self.get_root().get("attributes").get(attr)
                    if "property" in methods:
                        attribute.link_to_internal_property(self.class_instances[class_name], methods["property"])
                    elif "getter" in methods:
                        getter_name = methods["getter"]
                        setter_name = methods.get("setter", None)
                        attribute.link_to_internal_func(self.class_instances[class_name], getter_name, setter_name)

    def reset(self):
        # Attribute unlinking logic remains unchanged
        for module_path, params in self.definition.items():
            for attr, methods in params["attributes"].items():
                attribute: SpxAttribute = self.get_root().get("attributes").get(attr)
                attribute.unlink_internal_property()
