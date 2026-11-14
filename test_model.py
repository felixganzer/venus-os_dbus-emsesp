#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dbus_emsesp"))

from dummy import DummyEmsEspClient
from model import EmsEspModelMapper


def test_dummy_payload_maps_to_valid_heatpump_state():
    config = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
    raw, _ = DummyEmsEspClient(config["dummy"]).read_all()
    state = EmsEspModelMapper(config["emsesp_mapping"], 9000).map(raw, "dummy-test")

    assert state.outside_temperature_c is not None
    assert state.electrical_energy_total_kwh is not None
    assert state.mode in ("standby", "heating", "dhw", "defrost", "cooling")
    assert state.total_electrical_power_w >= 0.0
    assert state.aux_heater_power_w >= 0.0
    assert state.compressor_electrical_power_w >= 0.0
