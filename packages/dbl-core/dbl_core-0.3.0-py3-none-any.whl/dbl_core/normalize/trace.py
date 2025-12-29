from __future__ import annotations

from typing import Any, Mapping, Tuple

from kl_kernel_logic import ExecutionTrace

from ..events.canonical import canonicalize_value
from ..events.trace_digest import trace_core_digest


def normalize_trace(trace: ExecutionTrace | Mapping[str, Any]) -> Tuple[dict[str, Any], str]:
    """Normalize a kernel trace or a raw trace mapping with a provided trace_digest."""
    if isinstance(trace, ExecutionTrace):
        trace_dict = canonicalize_value(trace.to_dict(include_observational=True))
        return trace_dict, trace_core_digest(trace_dict)
    if isinstance(trace, Mapping):
        trace_mapping = trace
        trace_dict = canonicalize_value(trace_mapping)
        provided_digest = trace_mapping.get("trace_digest")
        if not isinstance(provided_digest, str):
            raise ValueError("trace_digest is required when providing raw trace dict")
        return trace_dict, provided_digest
    raise TypeError("trace must be ExecutionTrace or Mapping")
