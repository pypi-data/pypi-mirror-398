from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Tuple

from ..events.canonical import json_dumps, digest_bytes
from ..events.model import DblEvent


@dataclass(frozen=True)
class BehaviorV:
    events: Tuple[DblEvent, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))

    def t_index(self, event: DblEvent) -> int:
        for idx, item in enumerate(self.events):
            if item == event:
                return idx
        raise ValueError("Event not in behavior stream")

    def to_dict(self) -> dict[str, object]:
        return {
            "events": [e.to_dict(include_observational=False) for e in self.events],
        }

    def to_json(self) -> str:
        return json_dumps(self.to_dict())

    def digest(self) -> str:
        event_digests = [e.digest() for e in self.events]
        return digest_bytes(json_dumps({"event_digests": event_digests}))
