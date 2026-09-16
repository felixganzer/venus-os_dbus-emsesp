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
from dummy import DummyEmsEspClient
from emsesp import EmsEspClient, EmsEspError
from energy import EnergyRuntimeTracker
from mapping import first_value

VERSION = "0.3.0"
LOG = logging.getLogger("dbus-emsesp")


def fmt(unit, decimals=1):
    def callback(_path, value):
        if value is None:
            return "---"
        if isinstance(value, (int, float)):
            number = ("{:." + str(decimals) + "f}").format(value)
            return number + ((" " + unit) if unit else "")
        return str(value)
    return callback


class EmsEspDbusService:
    SENSOR_PATHS = {
        "/Temperatures/Outside": ("°C", 1),
        "/Temperatures/Flow": ("°C", 1),
        "/Temperatures/Return": ("°C", 1),
        "/Temperatures/Dhw": ("°C", 1),
        "/HeatPump/Power": ("W", 0),
        "/HeatPump/Cop": ("", 2),
        "/HeatPump/CompressorActive": ("", 0),
        "/HeatPump/Status": ("", 0),
        "/HeatPump/AuxHeaterPower": ("W", 0),
        "/HeatPump/AuxHeaterActive": ("", 0),
    }

    COUNTER_PATHS = {
        "/Ac/Power": ("W", 0),
        "/Ac/L1/Power": ("W", 0),
        "/Ac/Energy/Forward": ("kWh", 3),
        "/Ac/L1/Energy/Forward": ("kWh", 3),
        "/HeatPump/Energy/Today": ("kWh", 3),
        "/HeatPump/Energy/Total": ("kWh", 3),
        "/HeatPump/Energy/Heating/Today": ("kWh", 3),
        "/HeatPump/Energy/Heating/Total": ("kWh", 3),
        "/HeatPump/Energy/Dhw/Today": ("kWh", 3),
        "/HeatPump/Energy/Dhw/Total": ("kWh", 3),
        "/HeatPump/Energy/AuxHeater/Today": ("kWh", 3),
        "/HeatPump/Energy/AuxHeater/Total": ("kWh", 3),
        "/HeatPump/Runtime/Today": ("s", 0),
        "/HeatPump/Runtime/Total": ("s", 0),
        "/HeatPump/Runtime/Heating/Today": ("s", 0),
        "/HeatPump/Runtime/Heating/Total": ("s", 0),
        "/HeatPump/Runtime/Dhw/Today": ("s", 0),
        "/HeatPump/Runtime/Dhw/Total": ("s", 0),
        "/HeatPump/Runtime/AuxHeater/Today": ("s", 0),
        "/HeatPump/Runtime/AuxHeater/Total": ("s", 0),
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

        counters = config.get("counters", {})
        self.tracker = EnergyRuntimeTracker(
            counters.get("state_file", "/data/venus-os_dbus-emsesp/state/counters.json"),
            counters.get("save_interval_seconds", 60),
        )

        dbus_cfg = config["dbus"]
        self.service = VeDbusService(dbus_cfg["service_name"], register=False)
        self._add_management_paths(dbus_cfg)
        self._add_sensor_paths()
        self._add_meter_paths(dbus_cfg)
        self.service.register()

    def _add_management_paths(self, cfg):
        connection = "Dummy data generator" if self.mode == "dummy" else cfg.get("connection", "EMS-ESP REST")
        self.service.add_path("/Mgmt/ProcessName", os.path.abspath(__file__))
        self.service.add_path("/Mgmt/ProcessVersion", VERSION)
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

    def _add_sensor_paths(self):
        for path, (unit, decimals) in self.SENSOR_PATHS.items():
            self.service.add_path(path, None, gettextcallback=fmt(unit, decimals))

    def _add_meter_paths(self, cfg):
        for path, (unit, decimals) in self.COUNTER_PATHS.items():
            self.service.add_path(path, 0.0, gettextcallback=fmt(unit, decimals))
        self.service.add_path("/Ac/Energy/Reverse", 0.0, gettextcallback=fmt("kWh", 3))
        self.service.add_path("/Ac/L1/Energy/Reverse", 0.0, gettextcallback=fmt("kWh", 3))
        self.service.add_path("/Position", int(cfg.get("position", 1)))
        self.service.add_path("/PhaseSetting", int(cfg.get("phase_setting", 1)))
        self.service.add_path("/DeviceType", int(cfg.get("device_type", 0)))
        self.service.add_path("/ErrorCode", 0)
        self.service.add_path("/IsGenericEnergyMeter", 1)

    def _publish_counters(self, power, mode, compressor, aux_power, aux_active):
        counters = self.tracker.update(power, mode, compressor, aux_power, aux_active)
        power = float(power or 0.0)
        total = counters["energy_total_total_kwh"]
        self.service["/Ac/Power"] = power
        self.service["/Ac/L1/Power"] = power
        self.service["/Ac/Energy/Forward"] = total
        self.service["/Ac/L1/Energy/Forward"] = total
        self.service["/HeatPump/Energy/Today"] = counters["energy_total_today_kwh"]
        self.service["/HeatPump/Energy/Total"] = total
        self.service["/HeatPump/Energy/Heating/Today"] = counters["energy_heating_today_kwh"]
        self.service["/HeatPump/Energy/Heating/Total"] = counters["energy_heating_total_kwh"]
        self.service["/HeatPump/Energy/Dhw/Today"] = counters["energy_dhw_today_kwh"]
        self.service["/HeatPump/Energy/Dhw/Total"] = counters["energy_dhw_total_kwh"]
        self.service["/HeatPump/Energy/AuxHeater/Today"] = counters["energy_aux_heater_today_kwh"]
        self.service["/HeatPump/Energy/AuxHeater/Total"] = counters["energy_aux_heater_total_kwh"]
        self.service["/HeatPump/Runtime/Today"] = counters["runtime_total_today_seconds"]
        self.service["/HeatPump/Runtime/Total"] = counters["runtime_total_total_seconds"]
        self.service["/HeatPump/Runtime/Heating/Today"] = counters["runtime_heating_today_seconds"]
        self.service["/HeatPump/Runtime/Heating/Total"] = counters["runtime_heating_total_seconds"]
        self.service["/HeatPump/Runtime/Dhw/Today"] = counters["runtime_dhw_today_seconds"]
        self.service["/HeatPump/Runtime/Dhw/Total"] = counters["runtime_dhw_total_seconds"]
        self.service["/HeatPump/Runtime/AuxHeater/Today"] = counters["runtime_aux_heater_today_seconds"]
        self.service["/HeatPump/Runtime/AuxHeater/Total"] = counters["runtime_aux_heater_total_seconds"]

    def poll(self):
        try:
            data, errors = self.client.read_all()
            mapped = {}
            updated = 0
            for dbus_path, candidates in self.mapping.items():
                if dbus_path not in self.SENSOR_PATHS:
                    LOG.warning("Ignoring unknown configured D-Bus path: %s", dbus_path)
                    continue
                value = first_value(data, candidates)
                mapped[dbus_path] = value
                self.service[dbus_path] = value
                updated += int(value is not None)

            self._publish_counters(
                mapped.get("/HeatPump/Power"),
                mapped.get("/HeatPump/Status"),
                mapped.get("/HeatPump/CompressorActive"),
                mapped.get("/HeatPump/AuxHeaterPower"),
                mapped.get("/HeatPump/AuxHeaterActive"),
            )

            self.last_success = time.time()
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
