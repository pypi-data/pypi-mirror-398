from dbl_core import DblEvent, DblEventKind, normalize_trace
from kl_kernel_logic import Kernel, PsiDefinition


def test_observational_ignored_in_digest():
    psi = PsiDefinition(psi_type="test", name="op")
    kernel = Kernel(deterministic_mode=True)
    trace = kernel.execute(psi=psi, task=lambda: "ok")
    trace_dict, trace_digest = normalize_trace(trace)

    base = {"trace": trace_dict, "trace_digest": trace_digest}
    event_a = DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data=base)
    event_b = DblEvent(
        DblEventKind.EXECUTION,
        correlation_id="c1",
        data={"trace": {**trace_dict, "error": "changed"}, "trace_digest": trace_digest},
    )
    assert event_a.digest() == event_b.digest()
