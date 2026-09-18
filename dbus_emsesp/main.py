#!/usr/bin/env python3
import json
import logging
import os
import sys
import time
from pathlib import Path

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

APP_DIR = Path(__file__).resolve().parents[1]
for candidate in (
    APP_DIR / "lib" / "velib_python",
    Path("/opt/victronenergy/dbus-systemcalc-py/ext/velib_python"),
    Path("/opt/victronenergy/velib_python"),
    Path("/data/velib_python"),
):
    if (candidate / "vedbus.py").exists():
        sys.path.insert(0, str(candidate))
        break

from distributor import PowerDistributor
from dummy import DummyEmsEspClient
from emsesp import EmsEspClient, EmsEspError
from energy import ThreeDeviceEnergyTracker
from mapping import first_value
from meter_service import HeatPumpMeterService

VERSION = "0.7.0"
LOG = logging.getLogger("dbus-emsesp")
CATEGORIES = ("heating", "dhw", "aux_heater")
STATUS_CODES = {"standby": 0, "heating": 1, "dhw": 2, "defrost": 3}


class Application:
    def __init__(self, config):
        self.config = config
        self.mode = str(config.get("mode", "rest")).strip().lower()
        self.simulation_enabled = bool(
            config.get("simulation_control", {}).get("enabled_at_start", True)
        )
        if self.mode == "dummy":
            self.client = DummyEmsEspClient(config.get("dummy", {}))
        elif self.mode == "rest":
            self.client = EmsEspClient(config["ems_esp"])
        else:
            raise ValueError("Unsupported mode: {}".format(self.mode))

        self.mapping = config["source_mapping"]
        self.telemetry_mapping = config.get("telemetry_mapping", {})
        self.poll_interval = int(config["ems_esp"].get("poll_interval_seconds", 10))
        self.stale_after = int(config["ems_esp"].get("stale_after_seconds", 60))
        self.last_success = 0.0
        self.distributor = PowerDistributor()
        counters = config.get("counters", {})
        self.tracker = ThreeDeviceEnergyTracker(
            counters.get("state_file", "/data/venus-os_dbus-emsesp/state/counters.json"),
            counters.get("save_interval_seconds", 60),
        )

        self.services = {}
        for category in CATEGORIES:
            callback = (
                self.set_simulation_enabled
                if category == "heating" and self.mode == "dummy"
                else None
            )
            self.services[category] = HeatPumpMeterService(
                config["devices"][category],
                config["electrical"],
                VERSION,
                category,
                simulation_callback=callback,
                simulation_initial_state=self.simulation_enabled,

                generic_input_defaults=config.get(
                    "generic_input_defaults",
                    {},
                ),

                telemetry_display=config.get(
                    "telemetry_display",
                    {},
                ),
            )

    def set_simulation_enabled(self, enabled):
        self.simulation_enabled = bool(enabled)
        LOG.warning("Simulation changed to %s", "ON" if enabled else "OFF")
        if not self.simulation_enabled:
            self._publish_zero_values("simulation_off")
            self.services["heating"].update_telemetry(self._offline_telemetry())

    def _extract(self, data):
        return {
            name: first_value(data, candidates, 0)
            for name, candidates in self.mapping.items()
        }

    def _extract_telemetry(self, data, mode, source):
        result = {}
        for name, candidates in self.telemetry_mapping.items():
            result[name] = first_value(data, candidates, None)
        normalized_mode = str(mode or "standby").strip().lower()
        result["status_code"] = int(
            result.get("status_code")
            if result.get("status_code") is not None
            else STATUS_CODES.get(normalized_mode, 0)
        )
        result["compressor_active"] = source.get("compressor_active", 0)
        result["aux_heater_active"] = source.get("aux_heater_active", 0)
        return result

    @staticmethod
    def _offline_telemetry():
        return {
            "status_code": 0,
            "outside_temperature_c": None,
            "flow_temperature_c": None,
            "return_temperature_c": None,
            "dhw_temperature_c": None,
            "cop": None,
            "compressor_active": 0,
            "aux_heater_active": 0,
        }

    @staticmethod
    def _zero_distribution(mode):
        return {
            "heating": 0.0,
            "dhw": 0.0,
            "aux_heater": 0.0,
            "total": 0.0,
            "mode": mode,
        }

    def _publish_distribution(self, distribution, connected=True, error_code=0):
        values = self.tracker.update(distribution)
        for category in CATEGORIES:
            self.services[category].update(
                values[category], connected, distribution["mode"], error_code
            )

    def _publish_zero_values(self, mode):
        self._publish_distribution(self._zero_distribution(mode), connected=True)

    def poll(self):
        try:
            if self.mode == "dummy" and not self.simulation_enabled:
                self._publish_zero_values("simulation_off")
                return True

            data, errors = self.client.read_all()
            source = self._extract(data)
            distribution = self.distributor.distribute(
                source["total_power_w"],
                source["operating_mode"],
                source["aux_heater_power_w"],
                source["aux_heater_active"],
            )
            telemetry = self._extract_telemetry(
                data, distribution["mode"], source
            )
            self._publish_distribution(distribution)
            self.services["heating"].update_telemetry(telemetry)
            self.last_success = time.time()

            if errors:
                LOG.warning("Partial endpoint failures: %s", ", ".join(sorted(errors)))
            LOG.info(
                "Updated: heat=%.0fW dhw=%.0fW aux=%.0fW status=%s flow=%sC",
                distribution["heating"],
                distribution["dhw"],
                distribution["aux_heater"],
                distribution["mode"],
                telemetry.get("flow_temperature_c"),
            )
        except EmsEspError as exc:
            LOG.error("EMS-ESP poll failed: %s", exc)
            if time.time() - self.last_success >= self.stale_after:
                self._publish_distribution(
                    self._zero_distribution("offline"), connected=False, error_code=1
                )
                self.services["heating"].update_telemetry(self._offline_telemetry())
        except Exception:
            LOG.exception("Unexpected polling error")
        return True

    def run(self):
        self.poll()
        GLib.timeout_add_seconds(self.poll_interval, self.poll)
        GLib.MainLoop().run()


def load_config():
    path = Path(os.environ.get("EMS_ESP_CONFIG", APP_DIR / "config" / "config.json"))
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    DBusGMainLoop(set_as_default=True)
    Application(load_config()).run()


if __name__ == "__main__":
    main()
