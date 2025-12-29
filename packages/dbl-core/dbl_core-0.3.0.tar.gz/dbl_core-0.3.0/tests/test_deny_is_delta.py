from dbl_core import DblEvent, DblEventKind, BehaviorV, GateDecision


def test_deny_is_delta():
    decision = GateDecision(decision="DENY", reason_code="BLOCKED")
    deny_event = DblEvent(DblEventKind.DECISION, correlation_id="c1", data=decision)
    v = BehaviorV(events=(deny_event,))
    assert v.t_index(deny_event) == 0
