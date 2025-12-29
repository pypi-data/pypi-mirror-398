from dbl_core import DblEvent, DblEventKind


def test_event_canonicalization():
    data = {"b": 2, "a": 1}
    event = DblEvent(DblEventKind.INTENT, correlation_id="c1", data=data)
    j1 = event.to_json()
    j2 = event.to_json()
    assert j1 == j2
