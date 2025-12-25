# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

from typing import Any
from spx_sdk.registry import register_class
from spx_sdk.attributes import (
    substitute_attribute_references_hierarchical,
    extract_attribute_wrappers_hierarchical,
    substitute_with_wrappers,
)
from spx_sdk.components import SpxContainer, SpxComponentState
from spx_sdk.validation.decorators import definition_schema


# Conditions container schema
@definition_schema({
    "type": "object",
    "properties": {
        "conditions": {
            "type": "array",
            "items": {
                "type": "object",
                "minProperties": 1,
                # pierwszy klucz (np. "if") ma wartość typu string – wyrażenie warunku
                "x-spx-firstkey-type": "string",
            }
        }
    },
    "additionalProperties": True,
}, validation_scope="parent")
@register_class(name="conditions")
@register_class(name="cases")
@register_class()
class Conditions(SpxContainer):
    """
    SPX container for a list of conditions. Definition must be a list of dicts:
      - <condition_name>: "<condition_ref>"
        <action_1>: ...
        <action_2>: ...
        <actions>: ...
        ...
    Each dict is turned into a Condition child component.
    """
    pass


# IfChain container schema (bez wymuszania typu dla pierwszego klucza – dopuszcza też `else` z obiektem)
@definition_schema({
    "type": "object",
    "properties": {
        "if_chain": {
            "type": "array",
            "items": {
                "type": "object",
                "minProperties": 1
            }
        }
    },
    "additionalProperties": True,
}, validation_scope="parent")
@register_class(name="if_chain")
class IfChain(SpxContainer):
    """
    A container for a chain of conditions. It runs the first condition that evaluates to true.
    Definition must be a list of dicts, each representing a condition.
    Example:
    [
        {"if": "condition1", "then": "action1"},
        {"if": "condition2", "then": "action2"},
        {"else": "default_action"}
    ]
    Each dict is turned into a Condition child component.
    """
    def _populate(self, definition: Any) -> None:
        super()._populate(definition)

    def run(self, *args, **kwargs) -> bool:
        self.state = SpxComponentState.RUNNING
        context = kwargs.get("context", {})
        for child in self.children.values():
            if child.run(context=context):
                break
        self.state = SpxComponentState.STOPPED
        return True

    def prepare(self, *args, **kwargs) -> bool:
        self.state = SpxComponentState.PREPARING
        context = kwargs.get("context", {})
        prepared = False
        for child in self.children.values():
            prepared = child.prepare(context=context) or prepared
        self.state = SpxComponentState.PREPARED
        return prepared


@definition_schema({"type": "string"})
@register_class(name="if")
@register_class(name="when")
@register_class(name="case")
@register_class(name="ifelse")
@register_class(name="if_else")
@register_class(name="else_if")
@register_class(name="elseif")
@register_class(name="condition")
@register_class()
class Condition(SpxContainer):

    def evaluate(self, condition: str) -> bool:
        # Replace #attr, #internal, and #external references with their actual values
        resolved_condition = substitute_attribute_references_hierarchical(self.parent, condition)
        # Resolve nested $(...) chains if present
        try:
            wrappers = extract_attribute_wrappers_hierarchical(self.parent, resolved_condition)
            if wrappers:
                resolved_condition = substitute_with_wrappers(resolved_condition, wrappers)
        except Exception:
            pass
        resolved_condition = resolved_condition.replace("true", "True").replace("false", "False")

        try:
            return eval(resolved_condition)
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {resolved_condition}")
            self.logger.exception(e)
            return False

    """
    A condition that runs its children if the condition is met.
    """
    def run(self, *args, **kwargs) -> bool:
        if not self.evaluate(self.definition):
            return False
        return super().run(*args, **kwargs)

    def prepare(self, *args, **kwargs) -> bool:
        # Always prepare children so actions are ready even if the condition is currently false.
        should_run = self.evaluate(self.definition)
        super().prepare(*args, **kwargs)
        return should_run


@definition_schema({"type": "object"})
@register_class(name="else")
@register_class()
class Else(SpxContainer):
    def run(self, *args, **kwargs) -> bool:
        return super().run(*args, **kwargs)
