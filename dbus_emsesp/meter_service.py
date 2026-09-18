import json
import os

import dbus
from vedbus import VeDbusService


PHASES = ("L1", "L2", "L3")
SIMULATION_CHANNEL = "/SwitchableOutput/Simulation"

# Config key -> D-Bus key -> telemetry dictionary key
TELEMETRY_BINDINGS = (
    ("operating_status", "OperatingStatus", "status_code"),
    ("outside_temperature", "OutsideTemperature", "outside_temperature_c"),
    ("flow_temperature", "FlowTemperature", "flow_temperature_c"),
    ("return_temperature", "ReturnTemperature", "return_temperature_c"),
    ("dhw_temperature", "DhwTemperature", "dhw_temperature_c"),
    ("cop", "Cop", "cop"),
    ("compressor", "Compressor", "compressor_active"),
    ("aux_heater", "AuxHeater", "aux_heater_active"),
)


def fmt(unit, decimals=1):
    def callback(_path, value):
        if value is None:
            return "---"
        if isinstance(value, (int, float)):
            number = ("{:." + str(decimals) + "f}").format(value)
            return number + ((" " + unit) if unit else "")
        return str(value)
    return callback


class HeatPumpMeterService:
    def __init__(
        self,
        config,
        electrical,
        version,
        category,
        simulation_callback=None,
        simulation_initial_state=True,
        generic_input_defaults=None,
        telemetry_display=None,
    ):
        self.category = category
        self.voltage = float(electrical.get("voltage_v", 230.0))
        self.update_index = 0
        self.simulation_callback = simulation_callback
        self.has_telemetry_panel = category == "heating"
        self.generic_input_defaults = generic_input_defaults or {}
        self.telemetry_display = telemetry_display or {}
        self.telemetry_paths = {}

        self.dbus_connection = (
            dbus.SessionBus()
            if "DBUS_SESSION_BUS_ADDRESS" in os.environ
            else dbus.SystemBus(private=True)
        )
        self.service = VeDbusService(
            config["service_name"],
            bus=self.dbus_connection,
            register=False,
        )
        add = self.service.add_path

        add("/Mgmt/ProcessName", os.path.abspath(__file__))
        add("/Mgmt/ProcessVersion", version)
        add("/Mgmt/Connection", "EMS-ESP shared REST bridge")
        add("/DeviceInstance", int(config["device_instance"]))
        add("/ProductId", int(config.get("product_id", 0xFFFF)))
        add("/ProductName", config["product_name"])
        add("/CustomName", config["custom_name"])
        add("/FirmwareVersion", version)
        add("/Serial", "emsesp-{}".format(category))
        add("/Connected", 0)
        add("/UpdateIndex", 0)

        add("/Ac/Power", 0.0, gettextcallback=fmt("W", 0))
        add("/Ac/Current", 0.0, gettextcallback=fmt("A", 2))
        add("/Ac/Voltage", self.voltage, gettextcallback=fmt("V", 1))
        add("/Ac/PowerFactor", 1.0)
        add("/Ac/Energy/Forward", 0.0, gettextcallback=fmt("kWh", 3))
        add("/Ac/Energy/Reverse", 0.0, gettextcallback=fmt("kWh", 3))

        for phase in PHASES:
            base = "/Ac/{}/".format(phase)
            add(base + "Power", 0.0, gettextcallback=fmt("W", 0))
            add(base + "Current", 0.0, gettextcallback=fmt("A", 2))
            add(base + "Voltage", self.voltage, gettextcallback=fmt("V", 1))
            add(base + "PowerFactor", 1.0)
            add(base + "Energy/Forward", 0.0, gettextcallback=fmt("kWh", 3))
            add(base + "Energy/Reverse", 0.0, gettextcallback=fmt("kWh", 3))

        add("/Energy/Today", 0.0, gettextcallback=fmt("kWh", 3))
        add("/Runtime/Today", 0, gettextcallback=fmt("s", 0))
        add("/Runtime/Total", 0, gettextcallback=fmt("s", 0))
        add("/Position", int(electrical.get("position", 0)))
        add("/NrOfPhases", 3)
        add("/DeviceType", 0)
        add("/ErrorCode", 0)
        add("/IsGenericEnergyMeter", 1)
        add("/OperatingMode", "unknown")

        if self.simulation_callback is not None:
            self._add_simulation_switch(bool(simulation_initial_state))

        if self.has_telemetry_panel:
            self._add_telemetry_inputs_from_config()

        self.service.register()

    def _add_simulation_switch(self, initial_state):
        add = self.service.add_path
        initial = int(initial_state)
        add("/SwitchableOutput/Capabilities", 0)
        add("/Channel/Simulation/Direction", 0)
        add(
            SIMULATION_CHANNEL + "/State",
            initial,
            writeable=True,
            onchangecallback=self._handle_simulation_state,
        )
        add(SIMULATION_CHANNEL + "/Name", "Simulation aktiv")
        add(SIMULATION_CHANNEL + "/Status", 0x09 if initial else 0x00)
        add(SIMULATION_CHANNEL + "/Auto", 0)
        add(SIMULATION_CHANNEL + "/Settings/Adjustable", 0)
        add(SIMULATION_CHANNEL + "/Settings/Group", "Bosch 5800i")
        add(SIMULATION_CHANNEL + "/Settings/CustomName", "Simulation aktiv")
        add(SIMULATION_CHANNEL + "/Settings/ShowUIControl", 1)
        add(SIMULATION_CHANNEL + "/Settings/Type", 1)
        add(SIMULATION_CHANNEL + "/Settings/ValidTypes", 2)
        add(SIMULATION_CHANNEL + "/Settings/Function", 2)
        add(SIMULATION_CHANNEL + "/Settings/ValidFunctions", 4)

    @staticmethod
    def _int_setting(settings, key, default):
        try:
            return int(settings.get(key, default))
        except (TypeError, ValueError):
            return int(default)

    def _add_generic_input(self, dbus_key, settings):
        add = self.service.add_path
        base = "/GenericInput/{}".format(dbus_key)
        input_type = self._int_setting(settings, "type", 1)
        if input_type not in (0, 1, 2, 3):
            raise ValueError(
                "Invalid GenericInput type {} for {}".format(input_type, dbus_key)
            )

        name = str(settings.get("name", dbus_key))
        group = str(
            settings.get(
                "group",
                self.generic_input_defaults.get("group", "Bosch 5800i Status"),
            )
        )
        show_ui_input = self._int_setting(
            settings,
            "show_ui_input",
            self.generic_input_defaults.get("show_ui_input", 6),
        )
        decimals = self._int_setting(settings, "decimals", 0 if input_type == 0 else 1)
        initial = settings.get("initial", 0)

        add(base + "/Value", initial)
        add(base + "/Status", 0x00)
        add(base + "/Name", name)
        add(base + "/Settings/Group", group)
        add(base + "/Settings/CustomName", name)
        add(base + "/Settings/ShowUIInput", show_ui_input)
        add(base + "/Settings/Type", input_type)
        add(base + "/Settings/ValidTypes", 1 << input_type)
        add(base + "/Settings/PrimaryLabel", name)
        add(base + "/Settings/Decimals", decimals)

        if "unit" in settings:
            add(base + "/Settings/Unit", str(settings["unit"]))
        if "labels" in settings:
            labels = settings["labels"]
            if not isinstance(labels, list):
                raise ValueError("labels for {} must be a list".format(dbus_key))
            add(base + "/Settings/Labels", json.dumps(labels, ensure_ascii=False))
        if "range_min" in settings:
            add(base + "/Settings/RangeMin", float(settings["range_min"]))
        if "range_max" in settings:
            add(base + "/Settings/RangeMax", float(settings["range_max"]))

        self.telemetry_paths[dbus_key] = base + "/Value"

    def _add_telemetry_inputs_from_config(self):
        for config_key, dbus_key, _telemetry_key in TELEMETRY_BINDINGS:
            settings = self.telemetry_display.get(config_key)
            if settings is None:
                continue
            if not isinstance(settings, dict):
                raise ValueError(
                    "telemetry_display.{} must be an object".format(config_key)
                )
            if settings.get("enabled", True):
                self._add_generic_input(dbus_key, settings)

    def _handle_simulation_state(self, _path, value):
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return False
        if normalized not in (0, 1):
            return False
        enabled = bool(normalized)
        self.service[SIMULATION_CHANNEL + "/Status"] = 0x09 if enabled else 0x00
        self.simulation_callback(enabled)
        return True

    def update_telemetry(self, telemetry):
        if not self.has_telemetry_panel:
            return
        for _config_key, dbus_key, telemetry_key in TELEMETRY_BINDINGS:
            path = self.telemetry_paths.get(dbus_key)
            if path is None:
                continue
            value = telemetry.get(telemetry_key)
            if telemetry_key in ("compressor_active", "aux_heater_active"):
                value = int(bool(value))
            self.service[path] = value

    def update(self, values, connected, mode, error_code=0):
        total_power = max(0.0, float(values["power_w"] or 0.0))
        total_energy = max(0.0, float(values["energy_total_kwh"] or 0.0))
        phase_power = total_power / 3.0
        phase_energy = total_energy / 3.0
        phase_current = phase_power / self.voltage if self.voltage > 0 else 0.0

        self.service["/Ac/Power"] = total_power
        self.service["/Ac/Current"] = phase_current * 3.0
        self.service["/Ac/Energy/Forward"] = total_energy
        for phase in PHASES:
            base = "/Ac/{}/".format(phase)
            self.service[base + "Power"] = phase_power
            self.service[base + "Current"] = phase_current
            self.service[base + "Energy/Forward"] = phase_energy

        self.service["/Energy/Today"] = values["energy_today_kwh"]
        self.service["/Runtime/Today"] = values["runtime_today_seconds"]
        self.service["/Runtime/Total"] = values["runtime_total_seconds"]
        self.service["/OperatingMode"] = mode
        self.service["/Connected"] = int(bool(connected))
        self.service["/ErrorCode"] = int(error_code)
        self.update_index = (self.update_index + 1) % 256
        self.service["/UpdateIndex"] = self.update_index
