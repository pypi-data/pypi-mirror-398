# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any

from spx_sdk.registry import register_class, create_instance
from spx_sdk.components import SpxContainer
from spx_sdk.validation.decorators import definition_schema


@definition_schema({
    "type": "object",
    "$defs": {
        # A single hook entry can be just a class name string (e.g., "refresh_model")
        # or a single-key object {"ClassName": { ...definition... }} for advanced cases.
        "HookEntry": {
            "oneOf": [
                {"type": "string"},
                {
                    "type": "object",
                    "minProperties": 1,
                    "maxProperties": 1,
                    "additionalProperties": {"type": "object"}
                }
            ]
        },
        # A hook value per event can be a single entry or a list of entries.
        "HookEntries": {
            "oneOf": [
                {"$ref": "#/$defs/HookEntry"},
                {"type": "array", "items": {"$ref": "#/$defs/HookEntry"}}
            ]
        }
    },
    "properties": {
        "hooks": {
            "type": "object",
            # Any event name (e.g., on_set) maps to single entry or list of entries
            "additionalProperties": {"$ref": "#/$defs/HookEntries"}
        }
    },
    # The parent object (model) may have other properties alongside 'hooks'
    "additionalProperties": True,
}, validation_scope="parent")
@register_class(name="hooks")
@register_class(name="Hooks")
class Hooks(SpxContainer):
    """
    SPX container for hook definitions. Each hook entry is turned into a Hook child.

    Definition must be a dict mapping hook names to:
      - a single attribute reference string, or
      - a list of attribute reference strings.
    """
    def _populate(self, definition: Any) -> None:
        if not isinstance(definition, dict):
            raise ValueError("Hooks definition must be a dict mapping hook names to references")
        for event_name, hook_entries in definition.items():
            # Normalize entries to a list
            if isinstance(hook_entries, (str, dict)):
                entries = [hook_entries]
            elif isinstance(hook_entries, list):
                entries = hook_entries
            else:
                raise ValueError(
                    f"Invalid hook definition for '{event_name}': expected string, dict, or list"
                )

            for idx, entry in enumerate(entries):
                # Determine class name and its specific definition
                if isinstance(entry, str):
                    cls_name = entry
                    entry_def = {}
                elif isinstance(entry, dict) and len(entry) == 1:
                    cls_name, entry_def = next(iter(entry.items()))
                else:
                    raise ValueError(
                        f"Invalid hook entry for '{event_name}': {entry!r}"
                    )

                # Unique instance name: event + class + optional index
                inst_name = cls_name if idx == 0 else f"{cls_name}_{idx}"
                # Instantiate the registered hook class under this container
                hook_inst = create_instance(
                    cls_name,
                    name=inst_name,
                    parent=self,
                    definition=entry_def
                )
                # Register this hook component on the parent under its event name
                if hasattr(self.parent, "register_hook"):
                    self.parent.register_hook(event_name, hook_inst)

    def run(self, *args, **kwargs) -> None:
        # Hooks container itself is a lifecycle child (e.g., under Attribute).
        # Its runtime role is only to register hook components, so run is a no-op.
        return True
