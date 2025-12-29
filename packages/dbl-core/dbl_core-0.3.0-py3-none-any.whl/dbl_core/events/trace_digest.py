from __future__ import annotations

from typing import Any, Mapping

from .canonical import canonicalize_value, json_dumps, digest_bytes


def trace_core_digest(trace_dict: Mapping[str, Any]) -> str:
    required = ("psi", "success", "failure_code", "exception_type")
    for key in required:
        if key not in trace_dict:
            raise ValueError(f"trace missing required field: {key}")
    if not isinstance(trace_dict["psi"], Mapping):
        raise ValueError("trace field psi must be a Mapping")
    core = {
        "psi": trace_dict["psi"],
        "success": trace_dict["success"],
        "failure_code": trace_dict["failure_code"],
        "exception_type": trace_dict["exception_type"],
    }
    return digest_bytes(json_dumps(canonicalize_value(core)))
