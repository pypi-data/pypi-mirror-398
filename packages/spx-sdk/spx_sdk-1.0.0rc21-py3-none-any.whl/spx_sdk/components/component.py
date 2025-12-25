# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import logging
import dataclasses
from spx_sdk.registry import register_class
from typing import Optional, Any, List, Dict, Union
from enum import Enum, auto
from contextlib import AbstractContextManager
from spx_sdk.diagnostics import guard, trace


class SpxComponentState(Enum):
    INITIALIZED = auto()
    PREPARING = auto()
    PREPARED = auto()
    STARTING = auto()
#    STARTED = auto()  # Deprecated: treat as equivalent to RUNNING; start() sets RUNNING directly
    RUNNING = auto()
    STARTED = RUNNING
    PAUSING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    DESTROYING = auto()
    DESTROYED = auto()
    RESETTING = auto()
    RESET = auto()
    FAULT = auto()
    UNKNOWN = auto()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


@register_class()
class SpxComponent(AbstractContextManager):
    """
    SpxComponent represents a node in a hierarchical component tree.

    Attributes:
        name (str): Unique name of this component instance.
        parent (Optional[SpxComponent]): Parent component in the hierarchy.
        children (Dict[str, SpxComponent]): Mapping of child component names to instances.
        definition (Any): Configuration data used to populate this component.
        description (Optional[str]): Human-readable description extracted from the definition.
        state (SpxComponentState): Current lifecycle state of the component.

    This class provides methods to manage child components, control the component’s lifecycle
    (prepare, run, start, pause, stop, reset, destroy/close/release), and navigate the component tree.
    It supports dict-like access (`component['child']`), containment checks
    (`'child' in component`), and length queries (`len(component)`).
    """
    def __init__(
            self,
            name: Optional[str] = None,
            parent: Optional["SpxComponent"] = None,
            definition: Optional[Any] = None
            ):
        self.name = name if name is not None else self.__class__.__name__
        self.parent = parent
        self.definition: Any = definition
        self.children: Dict[str, SpxComponent] = {}
        self.state = SpxComponentState.INITIALIZED
        # Component enabled flag: when False, lifecycle methods do nothing
        self._enabled: bool = True
        # Hook registry: event name → list of hook components
        self.hooks: Dict[str, List[SpxComponent]] = {}
        # Cleanup flags
        self._destroyed: bool = False
        self._destroying: bool = False
        self.description: Optional[str] = None
        self.display_name: Optional[str] = None
        if parent is not None and hasattr(parent, "logger"):
            self.logger = parent.logger
        elif not hasattr(self, "logger"):
            self.logger = logging.getLogger(
                f"{__name__}.{self.__class__.__name__}.{self.name}"
            )
        self._apply_identity_overrides(definition)
        self._extract_description(definition)
        if parent is not None:
            parent.add_child(self)

        self._populate(self.definition)
        self.logger.debug(f"Created {self.__class__.__name__}(name={self.name}, definition={self.definition!r})")

    @guard("config.add_child", bubble=True, http_status=422)
    def add_child(self, child: "SpxComponent"):
        """Prevent adding itself as a child"""
        if child is self:
            raise ValueError(f"Cannot add {self.name} as its own child.")
        if not isinstance(child, SpxComponent):
            raise ValueError("Only SpxComponent instances can be added as children.")
        if child.name in self.children:
            to_remove = self.children[child.name]
            self.delete_child(to_remove)
        # add or replace child by its name
        self.children[child.name] = child
        child.parent = self

    def remove_child(self, child: "SpxComponent"):
        # Detach child from parent, but does not destroy resources. Prefer delete_child() for teardown.
        if child.name in self.children:
            self.children.pop(child.name)
            child.parent = None

    @guard("config.delete_child", bubble=True, http_status=422)
    def delete_child(self, child: "SpxComponent"):
        """Destroy and remove a child component by reference."""
        if not isinstance(child, SpxComponent):
            raise ValueError("delete_child expects a SpxComponent")
        try:
            with trace(self, action="child.destroy", bubble=False, http_status=500, extra={"child": getattr(child, "name", None)}):
                child.destroy()
        finally:
            self.remove_child(child)

    def get_children(self) -> Dict[str, "SpxComponent"]:
        """Return the internal dict of children keyed by name."""
        return self.children

    def get_children_list(self) -> List["SpxComponent"]:
        """Return a list of child components."""
        return list(self.children.values())

    def get_parent(self):
        return self.parent

    def get_hierarchy(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "children": [child.get_hierarchy() for child in self.children.values()],
        }

    def get_root(self) -> Optional["SpxComponent"]:
        if self.parent is None:
            return self
        return self.parent.get_root()

    def get_path(self, delimiter: str = "/") -> str:
        """
        Public path helper used by diagnostics: returns the component path with a chosen delimiter.
        Default delimiter is '/', e.g. 'root/child/grandchild'.
        """
        return self._get_full_path().replace(".", delimiter)

    @property
    def destroyed(self) -> bool:
        """Whether this component has been destroyed and released."""
        return self._destroyed

    @guard(prefix="lifecycle.", http_status=500)
    def prepare(self, *args, **kwargs) -> bool:
        """Prepare the component and propagate to children."""
        if not self._enabled:
            # Trigger on_prepare hooks
            self.trigger_hooks("on_event", *args, **kwargs)
            self.trigger_hooks("on_prepare", *args, **kwargs)
            self.logger.debug(f"Component {self.name} is disabled; skipping prepare")
            return False
        # Trigger on_prepare hooks
        self.trigger_hooks("on_event", *args, **kwargs)
        self.trigger_hooks("on_prepare", *args, **kwargs)
        self.logger.debug(f"Preparing {self.name}")
        self.state = SpxComponentState.PREPARING
        for child in self.children.values():
            child.prepare(*args, **kwargs)
        self.state = SpxComponentState.PREPARED
        return True

    @guard(prefix="lifecycle.", http_status=500)
    def run(self, *args, **kwargs) -> bool:
        """Run the component and propagate to children."""
        if not self._enabled:
            # Trigger on_run hooks
            self.trigger_hooks("on_event", *args, **kwargs)
            self.trigger_hooks("on_run", *args, **kwargs)
            self.logger.debug(f"Component {self.name} is disabled; skipping run")
            return False
        # Trigger on_run hooks
        self.trigger_hooks("on_event", *args, **kwargs)
        self.trigger_hooks("on_run", *args, **kwargs)
        self.logger.debug(f"Running {self.name}")
        self.state = SpxComponentState.RUNNING
        for child in self.children.values():
            child.run(*args, **kwargs)
        # Stay in RUNNING until pause() or stop()
        return True

    @guard(prefix="lifecycle.", http_status=500)
    def start(self, *args, **kwargs) -> bool:
        """Start the component and propagate to children."""
        if not self._enabled:
            self.logger.debug(f"Component {self.name} is disabled; skipping start")
            return False
        # Trigger on_start hooks
        self.trigger_hooks("on_event", *args, **kwargs)
        self.trigger_hooks("on_start", *args, **kwargs)
        self.logger.debug(f"Starting {self.name}")
        self.state = SpxComponentState.STARTING
        for child in self.children.values():
            child.start(*args, **kwargs)
        self.state = SpxComponentState.RUNNING
        return True

    @guard(prefix="lifecycle.", http_status=500)
    def pause(self, *args, **kwargs) -> bool:
        """Pause the component and propagate to children."""
        self.logger.debug(f"Pausing {self.name}")
        self.state = SpxComponentState.PAUSING
        for child in self.children.values():
            child.pause(*args, **kwargs)
        self.state = SpxComponentState.PAUSED
        return True

    @guard(prefix="lifecycle.", http_status=500)
    def stop(self, *args, **kwargs) -> bool:
        """Stop the component and propagate to children."""
        if not self._enabled:
            self.logger.debug(f"Component {self.name} is disabled; skipping stop")
            return False
        self.logger.debug(f"Stopping {self.name}")
        self.state = SpxComponentState.STOPPING
        for child in self.children.values():
            child.stop(*args, **kwargs)
        self.state = SpxComponentState.STOPPED
        return True

    @guard(prefix="lifecycle.", http_status=500)
    def reset(self, *args, **kwargs) -> bool:
        """Reset the component and propagate to children."""
        self.logger.debug(f"Reset {self.name}")
        self.state = SpxComponentState.RESETTING
        for child in self.children.values():
            child.reset(*args, **kwargs)
        self.state = SpxComponentState.RESET
        return True

    @guard(prefix="lifecycle.", http_status=500)
    def destroy(self, *args, **kwargs) -> bool:
        """Deep-destroy the component and all descendants.

        This method is idempotent:
        - Subsequent calls after the first successful destroy() are no-ops.
        Cleanup order:
        1) Transition → DESTROYING
        2) Stop this component (best-effort) and trigger on_destroy hooks
        3) Recursively destroy children (snapshot to avoid mutation while iterating)
        4) Detach from parent
        5) Call release() hook
        6) Clear hooks/children references
        7) Transition → DESTROYED
        """
        if self._destroyed:
            # Idempotent: already destroyed → success
            return True
        if self._destroying:
            # A concurrent destroy in progress; signal no work done
            return False
        self._destroying = True
        self.logger.debug(f"Destroying {self.name}")
        # Best-effort stop before teardown (emit diagnostics on failure but do not abort)
        with trace(self, action="lifecycle.destroy.stop", bubble=False, http_status=500, extra={"component": self.name}):
            self.stop(*args, **kwargs)

        # Trigger on_destroy hooks
        self.trigger_hooks("on_event", *args, **kwargs)
        self.trigger_hooks("on_destroy", *args, **kwargs)

        self.state = SpxComponentState.DESTROYING

        # Snapshot children to avoid concurrent modification
        for child in list(self.children.values()):
            # Capture failures but continue teardown
            with trace(self, action="lifecycle.destroy.child", bubble=False, http_status=500, extra={"child": getattr(child, "name", None)}):
                child.destroy(*args, **kwargs)

        # Detach from parent
        if self.parent is not None:
            try:
                # Let parent forget us without calling our destroy again
                if self.name in self.parent.children:
                    self.parent.children.pop(self.name, None)
            finally:
                self.parent = None

        # Allow subclasses to release external resources once
        with trace(self, action="lifecycle.release", bubble=False, http_status=500, extra={"component": self.name}):
            self.release()

        # Clear hooks/children
        self.hooks.clear()
        self.children.clear()

        self.state = SpxComponentState.DESTROYED
        self._destroyed = True
        self._destroying = False
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            with trace(self, action="context.__exit__.destroy", bubble=False, http_status=500, extra={"component": self.name}):
                self.destroy()
        except Exception:
            # Never raise from destructor-like context
            pass
        return False

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', state={self.state.name}, parent={self.parent.__class__.__name__ if self.parent else None}, children={len(self.children)})"

    def _apply_identity_overrides(self, definition: Any) -> None:
        """
        Extract optional component_id/display_name metadata from the definition.
        Mutates the definition mapping to remove these reserved keys so subclasses
        don't treat them as regular configuration.
        """
        if not isinstance(definition, dict):
            return
        component_id = definition.pop("component_id", None)
        if component_id is None:
            component_id = definition.pop("id", None)
        display_name = definition.pop("display_name", None)
        legacy_name = definition.pop("name", None)

        if component_id is not None:
            self.name = str(component_id)

        if display_name is None:
            display_name = legacy_name

        if display_name is not None:
            self.display_name = display_name

    def _extract_description(self, definition: Any) -> None:
        """
        Safely extract a textual description from the provided definition when available.
        Accepts string-like values and ignores missing or non-convertible entries.
        """
        if not isinstance(definition, dict) or "description" not in definition:
            return

        raw_description = definition.get("description")
        if raw_description is None or isinstance(raw_description, str):
            self.description = raw_description
            return

        try:
            self.description = str(raw_description)
        except Exception:
            # Non-stringable description, keep the field unset but avoid raising.
            self.logger.debug(
                "Ignoring description for component '%s': unable to convert value of type %s",
                self.name,
                type(raw_description).__name__,
            )

    @guard("config.populate", bubble=True, http_status=422)
    def _populate(self, definition: Any) -> None:
        """
        Generic hook to populate instance attributes from a definition mapping.
        By default, this will set each key in definition as an attribute.
        Subclasses can override to customize behavior.

        Non-dict definitions (e.g. lists) are ignored by default to preserve
        previous behavior where _populate only acts on dicts.
        """
        if isinstance(definition, dict):
            if dataclasses.is_dataclass(self):
                field_names = {field.name for field in dataclasses.fields(self)}
                for key, value in definition.items():
                    if key == "description":
                        continue
                    if key in field_names:
                        setattr(self, key, value)
                    else:
                        path = self._get_full_path()
                        raise AttributeError(
                            f"Cannot set undefined dataclass field '{key}' on '{path}'"
                        )
            else:
                for key, value in definition.items():
                    if key == "description":
                        continue
                    if hasattr(self, key):
                        setattr(self, key, value)
                    else:
                        path = self._get_full_path()
                        raise AttributeError(
                            f"Cannot set undefined attribute '{key}' on '{path}'"
                        )

    def _get_full_path(self) -> str:
        """
        Construct the full component path by joining all parent names with dots.
        Returns a string like 'root.child.grandchild'.
        """
        path = self.name
        node = self.parent
        while node:
            path = f"{node.name}.{path}"
            node = node.parent
        return path

    def __getitem__(self, key: str) -> "SpxComponent":
        """
        If this component has children, retrieve a child by name.
        If no children exist, treat the key as an attribute name on this instance.
        Raises KeyError if neither a child nor an attribute with that name exists.
        """
        if len(self.children) > 0:
            # Normal child lookup
            try:
                return self.children[key]
            except KeyError:
                raise KeyError(f"No child named '{key}' in component '{self.name}'.")
        else:
            # Leaf: try to return attribute
            if hasattr(self, key):
                return getattr(self, key)
            raise KeyError(f"Component '{self.name}' has no child or attribute named '{key}'.")

    @guard("config.update", bubble=True, http_status=422)
    def update(self, cfg: Union[Dict, List]) -> None:
        """Forwards to the subclass hook _populate."""
        self._extract_description(cfg)
        self.definition = cfg if isinstance(cfg, (dict, list)) else self.definition
        self._populate(cfg)

    @guard("config.add", bubble=True, http_status=422)
    def add(self, inst_name: str, cfg: Any) -> Optional["SpxComponent"]:
        """
        Dynamically add a new instance at runtime, mirroring _populate logic for a single entry.
        Returns the newly created component (or existing if already present).
        """
        if inst_name in self.children:
            # Already exists, update its configuration instead
            self.delete_child(self.children[inst_name])
        # Reuse _populate logic by feeding a single-entry list
        self._populate({inst_name: cfg})
        # Return the newly added instance
        return self.children.get(inst_name)

    @guard("config.setitem", bubble=True, http_status=422)
    def __setitem__(self, key: str, value: Any) -> None:
        if isinstance(value, SpxComponent):
            # Assign a child component
            old = self.children.get(key)
            if old is not None:
                old.parent = None
            self.children[key] = value
            value.parent = self
            return
        if key in self.children:
            # Update existing child component's configuration
            self.children[key].update(value)
            return
        # Override existing attribute if present
        if hasattr(self, key):
            cls_attr = getattr(self.__class__, key, None)
            if isinstance(cls_attr, property):
                # Property: ensure it has a setter
                if cls_attr.fset is None:
                    raise AttributeError(f"Property '{key}' on component '{self.name}' is read-only")
                setattr(self, key, value)
            else:
                setattr(self, key, value)
            return
        # For dict or string values, delegate to add()
        if isinstance(value, (dict, str)):
            self.add(key, value)
            return
        # Otherwise, cannot handle this type
        raise ValueError(f"Cannot set item {key!r} with value of type {type(value).__name__}")

    def remove(self, inst_name: str) -> None:
        """
        Remove the instance with the given name.

        Backward compatible:
        - If the child defines a destroy() method (all SpxComponents do), we call it
          to ensure resources are freed, then detach it.
        """
        child = self.children.get(inst_name)
        if child is not None:
            # Best-effort deep destroy to avoid leaks
            self.delete_child(child)

    def __delitem__(self, key: str) -> None:
        """
        Allow dict-style deletion of instances.
        """
        self.remove(key)

    def get(self, key: str, default=None) -> Optional["SpxComponent"]:
        """
        Get a child component by name, returning a default if not found.

        Args:
            key (str): Name of the child component.
            default (Any): Value to return if the child is not found.

        Returns:
            Optional[SpxComponent]: The child component or the default.
        """
        return self.children.get(key, default)

    def __contains__(self, key: str) -> bool:
        """
        Check if a child component exists by name.

        Args:
            key (str): Name to check.

        Returns:
            bool: True if a child with the given name exists, False otherwise.
        """
        return key in self.children

    def __len__(self) -> int:
        """
        Return the number of child components.

        This allows using len(component) to retrieve the count of children.

        Returns:
            int: Number of child components.
        """
        return len(self.children)

    def __bool__(self) -> bool:
        """
        Always return True to ensure component truthiness is independent of child count.
        """
        return True

    def enable(self) -> None:
        """
        Enable the component. Lifecycle methods (prepare, run, start, stop)
        will execute when this component is enabled.
        """
        self._enabled = True
        # Trigger enable hooks
        self.trigger_hooks("on_event")
        self.trigger_hooks("on_enable")

    def disable(self) -> None:
        """
        Disable the component. Lifecycle methods (prepare, run, start, stop)
        become no-ops when the component is disabled.
        """
        self._enabled = False
        # Trigger disable hooks
        self.trigger_hooks("on_event")
        self.trigger_hooks("on_disable")

    @property
    def enabled(self) -> bool:
        """
        Whether the component is enabled. If False, prepare/run/start/stop
        will not execute.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """
        Setter for enabled flag. Allows toggling via assignment:
            component.enabled = False  # equivalent to component.disable()
        """
        if value:
            self.enable()
        else:
            self.disable()

    def register_hook(self, event: str, hook_component: "SpxComponent") -> None:
        """
        Register a hook component to be triggered on the given event.
        Prevents duplicate registrations of the same hook for the same event.
        """
        hooks_list = self.hooks.setdefault(event, [])
        if hook_component not in hooks_list:
            hooks_list.append(hook_component)

    def get_hooks(self, event: str) -> List["SpxComponent"]:
        """
        Get all registered hook components for the given event name.
        """
        return list(self.hooks.get(event, []))

    def trigger_hooks(self, event: str, *args, **kwargs) -> None:
        """
        Invoke all hooks registered under the given event.
        Failures are emitted as diagnostics (bubble=False) and do not break lifecycle.
        """
        for hook in self.hooks.get(event, []):
            with trace(self, action=f"hooks.{event}", bubble=False, http_status=500, extra={
                "hook": getattr(hook, "name", hook.__class__.__name__),
                "event": event,
            }):
                hook.run(*args, **kwargs)

    def __del__(self):
        # Avoid raising in GC; best-effort
        if getattr(self, "_destroyed", True):
            return
        try:
            with trace(self, action="gc.__del__.destroy", bubble=False, http_status=500, extra={"component": getattr(self, "name", None)}):
                self.destroy()
        except Exception:
            pass

    def release(self) -> bool:
        """Hook for subclasses to free external resources (sockets, threads, files, etc.).
        Called exactly once by `destroy()` before children/hooks are cleared.
        Default implementation does nothing and returns True.
        Subclasses should override and return True when cleanup succeeds.
        """
        return True

    def close(self, *args, **kwargs) -> bool:
        """Convenience alias for destroy() to support 'with' or resource idioms."""
        return self.destroy(*args, **kwargs)
