from dbl_core import DblEvent, DblEventKind, BehaviorV


def test_behavior_t_index():
    e0 = DblEvent(DblEventKind.INTENT, correlation_id="c1", data={})
    e1 = DblEvent(DblEventKind.DECISION, correlation_id="c1", data={"decision": "ALLOW"})
    v = BehaviorV(events=(e0, e1))
    assert v.t_index(e0) == 0
    assert v.t_index(e1) == 1
