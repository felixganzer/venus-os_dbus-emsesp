#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dbus_emsesp"))
from distributor import PowerDistributor
from dummy import DummyEmsEspClient


def test_three_device_distribution_matches_total_power():
    config = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
    client = DummyEmsEspClient(config.get("dummy", {}))
    distributor = PowerDistributor()
    data, _ = client.read_all()
    hp = data["heatpump"]
    result = distributor.distribute(
        hp.get("power", 0.0),
        hp.get("status", "standby"),
        hp.get("auxheaterpower", 0.0),
        hp.get("auxheateractive", False),
    )
    assert abs(result["heating"] + result["dhw"] + result["aux_heater"] - result["total"]) < 0.001


def test_dummy_payload_matches_current_and_legacy_contract():
    config = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
    client = DummyEmsEspClient(config.get("dummy", {}))
    data, _ = client.read_all()
    boiler = data["boiler"]
    heatpump = data["heatpump"]
    assert "hpcurrpower" in boiler
    assert "auxheaterpower" in boiler
    assert "auxheateractive" in boiler
    assert "power" in heatpump
    assert "status" in heatpump
    assert "auxheaterpower" in heatpump
    assert "auxheateractive" in heatpump
