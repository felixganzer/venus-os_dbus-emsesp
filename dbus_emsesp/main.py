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

from vedbus import VeDbusService
from emsesp import EmsEspClient, EmsEspError
from dummy import DummyEmsEspClient
from mapping import first_value

VERSION = "0.1.0"
LOG = logging.getLogger("dbus-emsesp")


def fmt(unit, decimals=1):
    def callback(_path, value):
        if value is None:
            return "---"
        if isinstance(value, (int, float)):
            return ("{:." + str(decimals) + "f} " + unit).format(value)
        return str(value)
    return callback


class EmsEspDbusService:
    VALUE_PATHS = {
        "/Temperatures/Outside": ("°C", 1),
        "/Temperatures/Flow": ("°C", 1),
        "/Temperatures/Return": ("°C", 1),
        "/Temperatures/Dhw": ("°C", 1),
        "/HeatPump/Power": ("W", 0),
        "/HeatPump/Cop": ("", 2),
        "/HeatPump/CompressorActive": ("", 0),
        "/HeatPump/Status": ("", 0),
    }

    def __init__(self, config):
        self.config = config
        self.mode = str(config.get("mode", "rest")).strip().lower()
        if self.mode == "dummy":
            self.client = DummyEmsEspClient(config.get("dummy", {}))
        elif self.mode == "rest":
            self.client = EmsEspClient(config["ems_esp"])
        else:
            raise ValueError("Unsupported mode: {} (expected rest or dummy)".format(self.mode))
        self.mapping = config["mapping"]
        self.poll_interval = int(config["ems_esp"].get("poll_interval_seconds", 10))
        self.stale_after = int(config["ems_esp"].get("stale_after_seconds", 60))
        self.last_success = 0.0
        self.update_index = 0

        dbus_cfg = config["dbus"]
        self.service = VeDbusService(dbus_cfg["service_name"], register=False)
        self._add_management_paths(dbus_cfg)
        self._add_value_paths()
        self.service.register()

    def _add_management_paths(self, cfg):
        self.service.add_path("/Mgmt/ProcessName", os.path.abspath(__file__))
        self.service.add_path("/Mgmt/ProcessVersion", VERSION)
        connection = "Dummy data generator" if self.mode == "dummy" else cfg.get("connection", "EMS-ESP REST")
        self.service.add_path("/Mgmt/Connection", connection)
        self.service.add_path("/DeviceInstance", int(cfg["device_instance"]))
        self.service.add_path("/ProductId", int(cfg.get("product_id", 0xFFFF)))
        self.service.add_path("/ProductName", cfg["product_name"])
        self.service.add_path("/CustomName", cfg.get("custom_name", cfg["product_name"]))
        self.service.add_path("/FirmwareVersion", VERSION)
        self.service.add_path("/Connected", 0)
        self.service.add_path("/UpdateIndex", 0)
        self.service.add_path("/Diagnostics/LastSuccess", "never")
        self.service.add_path("/Diagnostics/LastError", "")
        self.service.add_path("/Diagnostics/FailedEndpoints", "")
        self.service.add_path("/Diagnostics/Mode", self.mode)

    def _add_value_paths(self):
        for path, (unit, decimals) in self.VALUE_PATHS.items():
            self.service.add_path(path, None, gettextcallback=fmt(unit, decimals))

    def poll(self):
        try:
            data, errors = self.client.read_all()
            updated = 0
            for dbus_path, candidates in self.mapping.items():
                if dbus_path not in self.VALUE_PATHS:
                    LOG.warning("Ignoring unknown configured D-Bus path: %s", dbus_path)
                    continue
                value = first_value(data, candidates)
                self.service[dbus_path] = value
                updated += int(value is not None)

            now = time.time()
            self.last_success = now
            self.service["/Connected"] = 1
            self.service["/Diagnostics/LastSuccess"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            self.service["/Diagnostics/LastError"] = ""
            self.service["/Diagnostics/FailedEndpoints"] = ", ".join(sorted(errors))
            self.update_index = (self.update_index + 1) % 256
            self.service["/UpdateIndex"] = self.update_index
            LOG.info("Poll successful; %d mapped values updated", updated)
        except EmsEspError as exc:
            self.service["/Diagnostics/LastError"] = str(exc)
            if time.time() - self.last_success >= self.stale_after:
                self.service["/Connected"] = 0
            LOG.error("Poll failed: %s", exc)
        except Exception:
            self.service["/Connected"] = 0
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
    EmsEspDbusService(load_config()).run()


if __name__ == "__main__":
    main()
