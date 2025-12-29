from dbl_core import DblEvent, DblEventKind, BehaviorV, GateDecision, normalize_trace
from kl_kernel_logic import Kernel, PsiDefinition


def test_contract_smoke():
    psi = PsiDefinition(psi_type="test", name="op")
    kernel = Kernel(deterministic_mode=True)
    trace = kernel.execute(psi=psi, task=lambda: "ok")
    trace_dict, trace_digest = normalize_trace(trace)

    decision = GateDecision(decision="ALLOW", reason_code="OK")
    events = (
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": psi.describe()}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=decision),
        DblEvent(
            DblEventKind.EXECUTION,
            correlation_id="c1",
            data={"trace": trace_dict, "trace_digest": trace_digest},
        ),
    )

    behavior = BehaviorV(events=events)
    assert behavior.t_index(events[0]) == 0
    assert behavior.t_index(events[2]) == 2
