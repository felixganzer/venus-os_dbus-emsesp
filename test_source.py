import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dbus_emsesp"))

from emsesp import EmsEspError
from source import RestWithDummyFallback


class FakeRest:
    def __init__(self, exc=None):
        self.exc = exc

    def read_all(self):
        if self.exc is not None:
            raise self.exc
        return {"boiler": {"status": "ok"}}, {}


class FakeDummy:
    def read_all(self):
        return {"boiler": {"status": "dummy"}}, {}


class FakeMapper:
    def map(self, raw, source="rest"):
        class State:
            def __init__(self, source):
                self.source = source

        return State(source)


def test_generic_rest_exception_activates_fallback():
    fallback = RestWithDummyFallback(
        FakeRest(RuntimeError("socket reset")),
        FakeDummy(),
        FakeMapper(),
        {"enabled": True, "after_consecutive_failures": 1, "rest_retry_seconds": 30},
        clock=lambda: 1000.0,
    )

    state, errors = fallback.read_state()

    assert state.source == "dummy_fallback"
    assert "fallback" in errors
    assert fallback.using_fallback is True


def test_status_reports_current_data_source():
    fallback = RestWithDummyFallback(
        FakeRest(),
        FakeDummy(),
        FakeMapper(),
        {"enabled": True, "after_consecutive_failures": 1, "rest_retry_seconds": 30},
        clock=lambda: 1000.0,
    )

    state, _ = fallback.read_state()

    assert state.source == "rest"
    assert fallback.status() == "rest"
