

from __future__ import annotations

"""
SPX SDK diagnostics package.

Public API exports:
  - Fault model: SpxFault, FaultEvent, FaultSeverity, build_fault_event
  - Guards: guard, trace, call, autoguard_lifecycle
  - Context: CORRELATION_ID, get_correlation_id, set_correlation_id, new_correlation_id,
             clear_correlation_id, use_correlation_id, wrap_with_correlation,
             copy_context_with_correlation, CorrelationFilter, fastapi_dependency,
             attach_response_header
  - Types: ComponentLike, Breadcrumb, ComponentObject
"""

# Fault model
from .faults import SpxFault, FaultEvent, FaultSeverity, build_fault_event

# Guards & helpers
from .guard import guard, trace, call, autoguard_lifecycle

# Correlation/context utilities
from .context import (
    CORRELATION_ID,
    get_correlation_id,
    set_correlation_id,
    new_correlation_id,
    clear_correlation_id,
    use_correlation_id,
    wrap_with_correlation,
    copy_context_with_correlation,
    CorrelationFilter,
)

# Shared typing helpers
from .diag_types import ComponentLike, Breadcrumb, ComponentObject

__all__ = [
    # Fault model
    "SpxFault", "FaultEvent", "FaultSeverity", "build_fault_event",
    # Guards
    "guard", "trace", "call", "autoguard_lifecycle",
    # Context
    "CORRELATION_ID", "get_correlation_id", "set_correlation_id",
    "new_correlation_id", "clear_correlation_id", "use_correlation_id",
    "wrap_with_correlation", "copy_context_with_correlation",
    "CorrelationFilter",
    # Types
    "ComponentLike", "Breadcrumb", "ComponentObject",
]
