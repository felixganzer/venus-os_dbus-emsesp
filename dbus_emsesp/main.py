#!/usr/bin/env python3
import json
import logging
import os
import sys
from pathlib import Path
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

APP_DIR = Path(__file__).resolve().parents[1]
for candidate in (APP_DIR / "lib" / "velib_python", Path("/opt/victronenergy/dbus-systemcalc-py/ext/velib_python"), Path("/opt/victronenergy/velib_python"), Path("/data/velib_python")):
    if (candidate / "vedbus.py").exists():
        sys.path.insert(0, str(candidate)); break

from distributor import PowerDistributor
from dummy import DummyEmsEspClient
from emsesp import EmsEspClient, EmsEspError
from energy import ThreeDeviceEnergyTracker
from meter_service import HeatPumpMeterService
from model import EmsEspModelMapper
from source import RestWithDummyFallback

VERSION = "1.0.0"
LOG = logging.getLogger("dbus-emsesp")
CATEGORIES = ("heating", "dhw", "aux_heater")


class Application:
    def __init__(self, config):
        self.config = config
        self.mode = str(config.get("mode", "rest_with_dummy_fallback")).lower()
        self.simulation_enabled = bool(config.get("simulation_control", {}).get("enabled_at_start", True))
        self.mapper = EmsEspModelMapper(config["emsesp_mapping"], config.get("model", {}).get("aux_heater_nominal_power_w", 9000))
        self.dummy = DummyEmsEspClient(config.get("dummy", {}))
        self.rest = EmsEspClient(config["ems_esp"])
        self.fallback = RestWithDummyFallback(self.rest, self.dummy, self.mapper, config.get("fallback", {}))
        self.poll_interval = int(config["ems_esp"].get("poll_interval_seconds", 10))
        self.distributor = PowerDistributor()
        counters = config.get("counters", {})
        self.tracker = ThreeDeviceEnergyTracker(counters.get("state_file", "/data/venus-os_dbus-emsesp/state/counters.json"), counters.get("save_interval_seconds", 60))
        self.services = {}
        for category in CATEGORIES:
            callback = self.set_simulation_enabled if category == "heating" and self.mode in ("dummy", "rest_with_dummy_fallback") else None
            self.services[category] = HeatPumpMeterService(
                config["devices"][category], config["electrical"], VERSION, category,
                simulation_callback=callback, simulation_initial_state=self.simulation_enabled,
                generic_input_defaults=config.get("generic_input_defaults", {}),
                telemetry_display=config.get("telemetry_display", {}),
            )

    def set_simulation_enabled(self, enabled):
        self.simulation_enabled = bool(enabled)
        LOG.warning("Simulation/fallback display changed to %s", self.simulation_enabled)

    def _read_state(self):
        if self.mode == "dummy":
            raw, errors = self.dummy.read_all()
            return self.mapper.map(raw, "dummy"), errors
        if self.mode == "rest":
            raw, errors = self.rest.read_all()
            return self.mapper.map(raw, "rest"), errors
        if self.mode == "rest_with_dummy_fallback":
            state, errors = self.fallback.read_state()
            if state.source == "dummy_fallback" and not self.simulation_enabled:
                raise EmsEspError("REST unavailable and dummy fallback disabled by UI switch")
            return state, errors
        raise ValueError("Unsupported mode: {}".format(self.mode))

    def _distribution(self, state):
        return self.distributor.distribute(state.total_electrical_power_w, state.mode, state.aux_heater_power_w, state.aux_heater_active)

    def _publish(self, state):
        distribution = self._distribution(state)
        tracked = self.tracker.update(distribution)
        direct_totals = {
            "heating": state.electrical_energy_heating_kwh,
            "dhw": state.electrical_energy_dhw_kwh,
            "aux_heater": state.electrical_energy_aux_heater_kwh,
        }
        runtime_minutes = {
            "heating": state.runtime_heating_minutes,
            "dhw": state.runtime_dhw_minutes,
            "aux_heater": None,
        }
        for category in CATEGORIES:
            values = tracked[category]
            if direct_totals[category] is not None:
                values["energy_total_kwh"] = direct_totals[category]
            if runtime_minutes[category] is not None:
                values["runtime_total_seconds"] = int(runtime_minutes[category] * 60)
            self.services[category].update(values, True, state.mode, 0)
        self.services["heating"].update_telemetry({
            "status_code": state.status_code,
            "outside_temperature_c": state.outside_temperature_c,
            "flow_temperature_c": state.flow_temperature_c,
            "return_temperature_c": state.return_temperature_c,
            "dhw_temperature_c": state.dhw_temperature_c,
            "cop": state.cop,
            "compressor_active": state.compressor_active,
            "aux_heater_active": state.aux_heater_active,
        })
        LOG.info("source=%s mode=%s total=%.0fW heat=%.0fW dhw=%.0fW aux=%.0fW", state.source, state.mode, state.total_electrical_power_w, distribution["heating"], distribution["dhw"], distribution["aux_heater"])

    def poll(self):
        try:
            state, errors = self._read_state()
            self._publish(state)
            if errors: LOG.warning("Source warnings: %s", errors)
        except Exception:
            LOG.exception("Polling failed")
        return True

    def run(self):
        self.poll(); GLib.timeout_add_seconds(self.poll_interval, self.poll); GLib.MainLoop().run()


def load_config():
    path = Path(os.environ.get("EMS_ESP_CONFIG", APP_DIR / "config" / "config.json"))
    with path.open("r", encoding="utf-8") as handle: return json.load(handle)


def main():
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    DBusGMainLoop(set_as_default=True); Application(load_config()).run()

if __name__ == "__main__": main()
