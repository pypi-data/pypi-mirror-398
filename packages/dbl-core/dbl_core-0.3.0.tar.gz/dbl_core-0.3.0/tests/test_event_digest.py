import pytest

from dbl_core import DblEvent, DblEventKind


def test_event_digest_stability():
    event_a = DblEvent(
        DblEventKind.INTENT,
        correlation_id="c1",
        data={"psi": "x"},
        observational={"note": "one"},
    )
    event_b = DblEvent(
        DblEventKind.INTENT,
        correlation_id="c1",
        data={"psi": "x"},
        observational={"note": "two"},
    )
    assert event_a.digest() == event_b.digest()


def test_execution_event_wrong_trace_digest_raises():
    data = {
        "trace": {
            "psi": {"psi_type": "x", "name": "y", "metadata": {}},
            "success": True,
            "failure_code": "OK",
            "exception_type": None,
        },
        "trace_digest": "bad",
    }
    with pytest.raises(TypeError, match="trace_digest mismatch"):
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data=data)


def test_execution_event_missing_core_field_raises():
    data = {
        "trace": {
            "psi": {"psi_type": "x", "name": "y", "metadata": {}},
            "success": True,
            "failure_code": "OK",
        },
        "trace_digest": "x",
    }
    with pytest.raises(TypeError, match="missing required field"):
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data=data)
