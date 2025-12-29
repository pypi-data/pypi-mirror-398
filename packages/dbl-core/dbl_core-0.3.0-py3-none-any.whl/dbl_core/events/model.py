from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Mapping, Optional

from .canonical import canonicalize_value, freeze_value, json_dumps, digest_bytes
from ..gate.model import GateDecision
from .trace_digest import trace_core_digest


class DblEventKind(str, Enum):
    INTENT = "INTENT"
    DECISION = "DECISION"
    EXECUTION = "EXECUTION"
    PROOF = "PROOF"


@dataclass(frozen=True)
class DblEvent:
    event_kind: DblEventKind
    correlation_id: str
    data: Any = field(default_factory=dict)
    observational: Optional[Mapping[str, Any]] = None

    DETERMINISTIC_FIELDS: ClassVar[tuple[str, ...]] = (
        "event_kind",
        "correlation_id",
        "data",
    )
    OBSERVATIONAL_FIELDS: ClassVar[tuple[str, ...]] = (
        "observational",
    )

    def __post_init__(self) -> None:
        if self.event_kind == DblEventKind.EXECUTION:
            if not isinstance(self.data, Mapping):
                raise TypeError("EXECUTION event data must be a Mapping")
            if "trace_digest" not in self.data or not isinstance(self.data["trace_digest"], str):
                raise TypeError("EXECUTION event data requires trace_digest: str")
            if "trace" not in self.data or not isinstance(self.data["trace"], Mapping):
                raise TypeError("EXECUTION event data requires trace: Mapping")
            trace = self.data["trace"]
            try:
                core_digest = trace_core_digest(trace)
            except ValueError as exc:
                raise TypeError(str(exc)) from exc
            if core_digest != self.data["trace_digest"]:
                raise TypeError("EXECUTION event trace_digest mismatch")
        object.__setattr__(self, "data", freeze_value(self.data))
        if self.observational is not None:
            object.__setattr__(self, "observational", freeze_value(self.observational))

    def _data_for_dict(self, *, include_observational: bool) -> Any:
        if isinstance(self.data, GateDecision):
            return self.data.to_dict(include_observational=include_observational)
        if isinstance(self.data, Mapping):
            data = canonicalize_value(self.data)
            if (
                self.event_kind == DblEventKind.EXECUTION
                and not include_observational
                and isinstance(data, Mapping)
                and "trace" in data
            ):
                filtered = dict(data)
                filtered.pop("trace", None)
                return filtered
            return data
        return canonicalize_value(self.data)

    def to_dict(self, *, include_observational: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_kind": self.event_kind.value,
            "correlation_id": self.correlation_id,
            "data": self._data_for_dict(include_observational=include_observational),
        }
        if include_observational and self.observational is not None:
            payload["observational"] = canonicalize_value(self.observational)
        return payload

    def to_json(self, *, include_observational: bool = True) -> str:
        return json_dumps(self.to_dict(include_observational=include_observational))

    def digest(self) -> str:
        return digest_bytes(self.to_json(include_observational=False))
