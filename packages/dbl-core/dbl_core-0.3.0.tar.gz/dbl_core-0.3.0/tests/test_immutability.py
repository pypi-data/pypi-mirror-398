import pytest
from dataclasses import FrozenInstanceError

from dbl_core import DblEvent, DblEventKind, BehaviorV


def test_immutability():
    event = DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"a": 1})
    v = BehaviorV(events=(event,))

    with pytest.raises(TypeError):
        event.data["a"] = 2  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        v.events += (event,)  # type: ignore[operator]
