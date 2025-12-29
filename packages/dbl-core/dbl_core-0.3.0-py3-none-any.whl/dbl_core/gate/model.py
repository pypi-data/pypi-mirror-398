from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GateDecision:
    decision: str  # "ALLOW" or "DENY"
    reason_code: str
    reason_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.decision not in ("ALLOW", "DENY"):
            raise ValueError("decision must be ALLOW or DENY")
        if not isinstance(self.reason_code, str) or not self.reason_code:
            raise ValueError("reason_code must be a non-empty string")

    def to_dict(self, *, include_observational: bool = True) -> dict[str, object]:
        data: dict[str, object] = {
            "decision": self.decision,
            "reason_code": self.reason_code,
        }
        if include_observational:
            data["reason_message"] = self.reason_message
        return data
