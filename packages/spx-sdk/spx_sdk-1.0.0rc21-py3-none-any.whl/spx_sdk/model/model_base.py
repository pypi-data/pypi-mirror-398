# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

import logging
import uuid
from typing import Any, Optional

from spx_sdk.components import SpxComponent, SpxContainer
from spx_sdk.model.polling import SimplePolling
from spx_sdk.model.timer import SimpleTimer
from spx_sdk.registry import register_class


@register_class(name="base_model")
class BaseModel(SpxContainer):
    """
    Base SPX model container. Each instance has a unique `uid`.
    """
    def __init__(
        self,
        name: Optional[str] = None,
        definition: Any = None,
        parent: Optional[SpxComponent] = None
    ):
        # Assign a unique identifier for this model instance
        self.uid = str(uuid.uuid4())
        # Instantiate a logger dedicated to this model instance and its component tree
        model_name = name or self.__class__.__name__
        logger_name = f"{self.__class__.__module__}.{self.__class__.__name__}.{model_name}.{self.uid}"
        self.logger = logging.getLogger(logger_name)

        # Determine model definition dict or use empty
        if isinstance(definition, dict):
            model_def = definition
        else:
            model_def = {}

        # Extract (and remove) any nested 'timer' or 'polling' entries
        timer_def = model_def.pop("timer", {}) or {}
        polling_def = model_def.pop("polling", {}) or {}

        # Initialize base container with the remaining definition
        super().__init__(name=name, definition=model_def, parent=parent, type=SpxContainer)

        # Instantiate Timer and Polling children using their extracted definitions
        SimpleTimer(name="timer", parent=self, definition=timer_def)
        SimplePolling(name="polling", parent=self, definition=polling_def)
