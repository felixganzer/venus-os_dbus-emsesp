#!/usr/bin/env python3
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "dbus_emsesp"))

from dummy import DummyEmsEspClient


def test_dummy_reader_returns_expected_sections():
    config = json.loads((PROJECT_DIR / "config" / "config.json").read_text(encoding="utf-8"))
    client = DummyEmsEspClient(config.get("dummy", {}))
    data, errors = client.read_all()

    assert isinstance(data, dict)
    assert "boiler" in data
    assert "heatpump" in data
    assert "system" in data
    assert isinstance(errors, dict)
