#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dbus_emsesp"))

from dummy import DummyEmsEspClient
from meter_service import HeatPumpMeterService
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


def test_mapper_accepts_common_emsesp_alias_variants():
    config = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
    raw = {
        "boiler": {
            "outside_temp": 8.4,
            "cur_flow_temp": 31.5,
            "return_temp": 26.3,
            "dhw": {"cur_temp": 49.2},
            "hp_activity": "heating",
            "heating_active": True,
            "tapwater_active": False,
            "hp_comp_on": True,
            "hp_comp_speed": 52.0,
            "hp_current_power": 1200.0,
            "hp_power": 3.9,
            "auxheaterpower": 900.0,
            "meter_total": 5.5,
            "meter_comp": 3.2,
            "meter_heat": 2.9,
            "nrg_total": 12.5,
            "nrg_heat": 11.2,
            "uptime_total": 1800.0,
            "uptime_comp_heating": 1200.0,
            "total_comp_starts": 24,
            "heating_starts": 18,
        },
        "heatpump": {"outside_temp": 8.4},
    }

    state = EmsEspModelMapper(config["emsesp_mapping"], 9000).map(raw, "alias-test")

    assert state.outside_temperature_c == 8.4
    assert state.flow_temperature_c == 31.5
    assert state.return_temperature_c == 26.3
    assert state.dhw_temperature_c == 49.2
    assert state.mode == "heating"


def test_heatpump_meter_service_exposes_venus_monitoring_paths():
    class FakeDbusBus:
        def __init__(self, *args, **kwargs):
            pass

    class FakeVeDbusService:
        def __init__(self, service_name, bus=None, register=False):
            self.service_name = service_name
            self.values = {}

        def add_path(self, path, value=None, **kwargs):
            self.values[path] = value
            return value

        def __setitem__(self, path, value):
            self.values[path] = value

        def __getitem__(self, path):
            return self.values[path]

        def register(self):
            return None

    import dbus_emsesp.meter_service as meter_service_module

    original_dbus = meter_service_module.dbus
    original_vedbus = meter_service_module.VeDbusService
    meter_service_module.dbus = type("FakeDbusModule", (), {"SessionBus": lambda *a, **k: FakeDbusBus(), "SystemBus": lambda *a, **k: FakeDbusBus()})
    meter_service_module.VeDbusService = FakeVeDbusService

    try:
        service = meter_service_module.HeatPumpMeterService(
            {"service_name": "com.victronenergy.heatpump.venus_test", "device_instance": 280, "custom_name": "Test", "product_name": "Test", "product_id": 65535},
            {"voltage_v": 230.0, "position": 0},
            "1.0.0",
            "heating",
        )
        service.update({"power_w": 2100.0, "energy_total_kwh": 12.5, "energy_today_kwh": 0.5, "runtime_total_seconds": 3600, "runtime_today_seconds": 1800}, True, "heating", 0, temperature=31.5, target_temperature=35.0, state_value=3)
        assert service.service["/State"] == 3
        assert service.service["/Temperature"] == 31.5
        assert service.service["/TargetTemperature"] == 35.0
        service.update({"power_w": 0.0, "energy_total_kwh": 12.5, "energy_today_kwh": 0.5, "runtime_total_seconds": 3600, "runtime_today_seconds": 1800}, True, "standby", 0, temperature=None, target_temperature=None, state_value=0)
        assert service.service["/Temperature"] is None
    finally:
        meter_service_module.dbus = original_dbus
        meter_service_module.VeDbusService = original_vedbus
