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

VERSION = "0.4.0"
LOG = logging.getLogger("dbus-emsesp")
CATEGORIES = ("heating", "dhw", "aux_heater")


class Application:
    def __init__(self, config):
        self.config = config
        self.mode = str(config.get("mode", "rest")).lower()
        self.client = DummyEmsEspClient(config.get("dummy", {})) if self.mode == "dummy" else EmsEspClient(config["ems_esp"])
        self.mapping = config["source_mapping"]
        self.poll_interval = int(config["ems_esp"].get("poll_interval_seconds", 10))
        self.stale_after = int(config["ems_esp"].get("stale_after_seconds", 60))
        self.last_success = 0.0
        self.distributor = PowerDistributor()
        counters = config.get("counters", {})
        self.tracker = ThreeDeviceEnergyTracker(
            counters.get("state_file", "/data/venus-os_dbus-emsesp/state/counters.json"),
            counters.get("save_interval_seconds", 60),
        )
        self.services = {
            category: HeatPumpMeterService(config["devices"][category], config["electrical"], VERSION, category)
            for category in CATEGORIES
        }

    def _extract(self, data):
        return {name: first_value(data, candidates, 0) for name, candidates in self.mapping.items()}

    def poll(self):
        try:
            data, errors = self.client.read_all()
            source = self._extract(data)
            distribution = self.distributor.distribute(
                source["total_power_w"], source["operating_mode"],
                source["aux_heater_power_w"], source["aux_heater_active"],
            )
            values = self.tracker.update(distribution)
            for category in CATEGORIES:
                self.services[category].update(values[category], True, distribution["mode"])
            self.last_success = time.time()
            if errors:
                LOG.warning("Partial endpoint failures: %s", ", ".join(sorted(errors)))
            LOG.info("Updated devices: heating=%.0fW dhw=%.0fW aux=%.0fW",
                     distribution["heating"], distribution["dhw"], distribution["aux_heater"])
        except EmsEspError as exc:
            LOG.error("EMS-ESP poll failed: %s", exc)
            if time.time() - self.last_success >= self.stale_after:
                for service in self.services.values():
                    service.update({"power_w":0,"energy_today_kwh":0,"energy_total_kwh":0,"runtime_today_seconds":0,"runtime_total_seconds":0}, False, "offline", 1)
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
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    DBusGMainLoop(set_as_default=True)
    Application(load_config()).run()


if __name__ == "__main__":
    main()
