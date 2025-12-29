import dbl_core


def test_public_api_exports():
    expected = {
        "DblEvent",
        "DblEventKind",
        "BehaviorV",
        "GateDecision",
        "normalize_trace",
    }
    assert set(dbl_core.__all__) == expected
