# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any, Optional, Type
from spx_sdk.diagnostics import guard, trace

from spx_sdk.registry import class_registry, create_instance, get_classes_by_base, register_class
from spx_sdk.components import SpxComponent


@register_class()
class SpxContainer(SpxComponent):
    """
    SpxContainer extends SpxComponent by automatically instantiating and organizing
    child components based on a provided definition.

    Two modes of operation:

    1. Filtered mode (when `type` is provided):
       - The definition may be a dict, list, or scalar.
       - For dict/list entries, if the key matches a subclass of `type`, that subclass
         is used; otherwise the base `type` class is used.
       - Scalar definitions are instantiated directly as the base `type`.

    2. Generic mode (when no `type` is provided):
       - Treat each dict key or single-key list node as a class name looked up in the registry.
       - Instantiate each matching class.
       - Other values (e.g. scalars) are ignored in generic mode.

    Child components are created during initialization by passing `definition` to `_populate`.
    """

    def __init__(
        self,
        definition: Any,
        *,
        name: Optional[str] = None,
        parent: Optional[SpxComponent] = None,
        type: Optional[Type[SpxComponent]] = None
    ):
        self._type = type
        # now actually load children
        super().__init__(name=name, parent=parent, definition=definition)

    @guard("config.populate", bubble=True, http_status=422)
    def _populate(self, definition: Any) -> None:
        if self._type:
            self._load_filtered(definition)
        else:
            self._load_generic(definition)
        super()._populate(definition)

    def _resolve_class_or_registry(self, cls_name: str, base_cls, subclasses):
        """Resolve a class name to either:
        - a subclass of the filtered base ("subclass"),
        - any registered class from the registry ("registry"), or
        - fallback to the filtered base class ("base").
        """
        # 1) subclass of the filtered base?
        if cls_name in subclasses:
            return subclasses[cls_name], "subclass"
        # 2) any registered class?
        if cls_name in class_registry:
            return class_registry[cls_name]["class"], "registry"
        # 3) fallback
        return base_cls, "base"

    def _handle_dict_filtered(self, definition: dict, base_cls, subclasses):
        """Instantiate children for dict-based filtered definitions.
        Prefer subclasses of the filter; allow any registered class; otherwise fallback to base.
        """
        for cls_name in list(definition.keys()):
            cfg = definition.pop(cls_name)
            cls, origin = self._resolve_class_or_registry(cls_name, base_cls, subclasses)
            if origin == "registry" and cls_name not in subclasses:
                # not a subclass of the filter, but still a valid registered class
                with trace(self, action="config.create", bubble=True, http_status=422, extra={
                    "origin": origin, "class": cls_name, "child_name": cls_name
                }):
                    create_instance(cls_name, name=cls_name, parent=self, definition=cfg)
            else:
                # subclass of filter or fallback to base class
                with trace(self, action="config.create", bubble=True, http_status=422, extra={
                    "origin": origin, "class": getattr(cls, "__name__", str(cls)), "child_name": cls_name
                }):
                    cls(name=cls_name, parent=self, definition=cfg)

    def _handle_list_filtered(self, definition: list, base_cls, subclasses):
        """Instantiate children for list-based filtered definitions, ensuring unique names.
        Supports entries as single-key dicts, multi-key dicts (root+children), and scalars.
        """
        name_counts: dict[str, int] = {}
        original_len = len(definition)
        for _ in range(original_len):
            node = definition.pop(0)

            if isinstance(node, dict) and len(node) == 1:
                cls_name, cfg = next(iter(node.items()))
                cls, origin = self._resolve_class_or_registry(cls_name, base_cls, subclasses)

                count = name_counts.get(cls_name, 0) + 1
                name_counts[cls_name] = count
                child_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"

                if origin == "registry" and cls_name not in subclasses:
                    with trace(self, action="config.create", bubble=True, http_status=422, extra={
                        "origin": origin, "class": cls_name, "child_name": child_name
                    }):
                        create_instance(cls_name, name=child_name, parent=self, definition=cfg)
                else:
                    with trace(self, action="config.create", bubble=True, http_status=422, extra={
                        "origin": origin, "class": getattr(cls, "__name__", str(cls)), "child_name": child_name
                    }):
                        cls(name=child_name, parent=self, definition=cfg)

            elif isinstance(node, dict) and len(node) > 1:
                it = iter(node.items())
                root_cls_name, root_cfg = next(it)
                root_cls, root_origin = self._resolve_class_or_registry(root_cls_name, base_cls, subclasses)

                count = name_counts.get(root_cls_name, 0) + 1
                name_counts[root_cls_name] = count
                root_name = root_cls_name if count == 1 else f"{root_cls_name}_{count - 1}"

                if root_origin == "registry" and root_cls_name not in subclasses:
                    with trace(self, action="config.create", bubble=True, http_status=422, extra={
                        "origin": root_origin, "class": root_cls_name, "child_name": root_name
                    }):
                        root = create_instance(root_cls_name, name=root_name, parent=self, definition=root_cfg)
                else:
                    with trace(self, action="config.create", bubble=True, http_status=422, extra={
                        "origin": root_origin, "class": getattr(root_cls, "__name__", str(root_cls)), "child_name": root_name
                    }):
                        root = root_cls(name=root_name, parent=self, definition=root_cfg)

                for sub_name, sub_cfg in it:
                    sub_cls, sub_origin = self._resolve_class_or_registry(sub_name, base_cls, subclasses)
                    if sub_origin == "registry" and sub_name not in subclasses:
                        with trace(self, action="config.create", bubble=True, http_status=422, extra={
                            "origin": sub_origin, "class": sub_name, "child_name": sub_name
                        }):
                            create_instance(sub_name, name=sub_name, parent=root, definition=sub_cfg)
                    else:
                        with trace(self, action="config.create", bubble=True, http_status=422, extra={
                            "origin": sub_origin, "class": getattr(sub_cls, "__name__", str(sub_cls)), "child_name": sub_name
                        }):
                            sub_cls(name=sub_name, parent=root, definition=sub_cfg)

            else:
                # Scalar or unsupported dict form
                if isinstance(node, str) and node in class_registry:
                    # string refers to a registered class – instantiate it
                    cls_name = node
                    count = name_counts.get(cls_name, 0) + 1
                    name_counts[cls_name] = count
                    child_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"
                    with trace(self, action="config.create", bubble=True, http_status=422, extra={
                        "origin": "registry", "class": cls_name, "child_name": child_name
                    }):
                        create_instance(cls_name, name=child_name, parent=self, definition=None)
                else:
                    # fallback to base class
                    name = base_cls.__name__ if not isinstance(node, str) else node
                    cfg = None if isinstance(node, str) else node
                    count = name_counts.get(name, 0) + 1
                    name_counts[name] = count
                    child_name = name if count == 1 else f"{name}_{count - 1}"
                    with trace(self, action="config.create", bubble=True, http_status=422, extra={
                        "origin": "base", "class": getattr(base_cls, "__name__", str(base_cls)), "child_name": child_name
                    }):
                        base_cls(name=child_name, parent=self, definition=cfg)

    def _handle_scalar_filtered(self, definition: Any, base_name: str, base_cls):
        """Instantiate a single child for scalar filtered definitions.
        If the scalar is a registered class name, instantiate that; otherwise use the base class.
        """
        if isinstance(definition, str) and definition in class_registry:
            with trace(self, action="config.create", bubble=True, http_status=422, extra={
                "origin": "registry", "class": definition, "child_name": definition
            }):
                create_instance(definition, name=definition, parent=self, definition=None)
            return
        with trace(self, action="config.create", bubble=True, http_status=422, extra={
            "origin": "base", "class": getattr(base_cls, "__name__", str(base_cls)), "child_name": base_name
        }):
            base_cls(name=base_name, parent=self, definition=definition)

    # Filtered mode: instantiate children using the specified type filter

    @guard("config.load_filtered", bubble=True, http_status=422)
    def _load_filtered(self, definition: Any) -> None:
        base_name = self._type.__name__
        subclasses = get_classes_by_base(base_name) or {}
        base_entry = class_registry.get(base_name)
        base_cls = base_entry["class"] if base_entry else self._type

        if isinstance(definition, dict):
            self._handle_dict_filtered(definition, base_cls, subclasses)
        elif isinstance(definition, list):
            self._handle_list_filtered(definition, base_cls, subclasses)
        else:
            self._handle_scalar_filtered(definition, base_name, base_cls)

    # Generic mode: instantiate children by registry lookup without type filter

    def _handle_dict_generic(self, definition: dict) -> None:
        """Instantiate children for generic dict definitions."""
        # Iterate over a static list of keys to avoid modifying while iterating
        for cls_name in list(definition.keys()):
            # Unknown keys in mixed config dicts should be ignored, unless it's a pure single-key mapping.
            if cls_name not in class_registry:
                if len(definition) == 1:
                    # Treat as class mapping only when the value looks like a component config (dict),
                    # otherwise it's likely a plain setting like {"name": "..."} which we should ignore.
                    val = definition[cls_name]
                    if isinstance(val, dict):
                        with trace(self, action="config.resolve", bubble=True, http_status=422, extra={
                            "origin": "registry", "class": cls_name, "child_name": cls_name, "index": None
                        }):
                            raise ValueError(f"Class '{cls_name}' not found in registry")
                # Mixed config dict or scalar value → ignore unknown key
                continue

            # Known class: pop config and create the instance under config.create
            cfg = definition.pop(cls_name)
            with trace(self, action="config.create", bubble=True, http_status=422, extra={
                "origin": "registry", "class": cls_name, "child_name": cls_name, "index": None
            }):
                create_instance(
                    cls_name,
                    name=cls_name,
                    parent=self,
                    definition=cfg
                )

    def _handle_list_generic(self, definition: list) -> None:
        """Instantiate children for generic list definitions."""
        # Process each element by popping from the front until empty,
        # ensure unique child names for duplicate class entries
        name_counts: dict[str, int] = {}
        original_len = len(definition)
        for idx in range(original_len):
            node = definition.pop(0)
            if isinstance(node, dict) and len(node) == 1:
                cls_name, cfg = next(iter(node.items()))
                with trace(self, action="config.resolve", bubble=True, http_status=422, extra={
                    "origin": "registry", "class": cls_name, "index": idx
                }):
                    if cls_name not in class_registry:
                        raise ValueError(f"Class '{cls_name}' not found in registry")
                # determine unique child name
                count = name_counts.get(cls_name, 0) + 1
                name_counts[cls_name] = count
                child_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"
                with trace(self, action="config.create", bubble=True, http_status=422, extra={
                    "origin": "registry", "class": cls_name, "child_name": child_name, "index": idx
                }):
                    create_instance(
                        cls_name,
                        name=child_name,
                        parent=self,
                        definition=cfg
                    )
            elif isinstance(node, dict) and len(node) > 1:
                it = iter(node.items())
                cls_name, cfg = next(it)
                with trace(self, action="config.resolve", bubble=True, http_status=422, extra={
                    "origin": "registry", "class": cls_name, "index": idx
                }):
                    if cls_name not in class_registry:
                        raise ValueError(f"Class '{cls_name}' not found in registry")
                # determine unique root name
                count = name_counts.get(cls_name, 0) + 1
                name_counts[cls_name] = count
                root_name = cls_name if count == 1 else f"{cls_name}_{count - 1}"
                with trace(self, action="config.create", bubble=True, http_status=422, extra={
                    "origin": "registry", "class": cls_name, "child_name": root_name, "index": idx
                }):
                    root = create_instance(
                        cls_name,
                        name=root_name,
                        parent=self,
                        definition=cfg
                    )
                for sub_name, sub_cfg in it:
                    with trace(self, action="config.resolve", bubble=True, http_status=422, extra={
                        "origin": "registry", "class": sub_name, "index": idx
                    }):
                        if sub_name not in class_registry:
                            raise ValueError(f"Class '{sub_name}' not found in registry")
                    # direct child under root; use sub_name (assuming no duplicates at this level)
                    with trace(self, action="config.create", bubble=True, http_status=422, extra={
                        "origin": "registry", "class": sub_name, "child_name": sub_name, "index": idx
                    }):
                        create_instance(
                            sub_name,
                            name=sub_name,
                            parent=root,
                            definition=sub_cfg
                        )
            # ignore non-dict nodes

    @guard("config.load_generic", bubble=True, http_status=422)
    def _load_generic(self, definition: Any) -> None:
        """
        Generic loading mode: treat each entry in a dict definition as
        class_name → configuration, or each node in a list as a single-key dict.
        Raises ValueError if a referenced class is not registered.
        """
        if isinstance(definition, dict):
            self._handle_dict_generic(definition)
        elif isinstance(definition, list):
            self._handle_list_generic(definition)
        else:
            # Scalar definitions are not loaded in generic mode
            return
