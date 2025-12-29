from dbl_core import DblEvent, DblEventKind, normalize_trace
from kl_kernel_logic import Kernel, PsiDefinition


def test_kernel_trace_embedding():
    psi = PsiDefinition(psi_type="test", name="op")
    kernel = Kernel(deterministic_mode=True)
    trace = kernel.execute(psi=psi, task=lambda: "ok")

    trace_dict, trace_digest = normalize_trace(trace)
    event = DblEvent(
        DblEventKind.EXECUTION,
        correlation_id="c1",
        data={"trace": trace_dict, "trace_digest": trace_digest},
    )

    event_dict = event.to_dict(include_observational=True)
    assert event_dict["data"]["trace_digest"] == trace_digest
    assert "trace" in event_dict["data"]
