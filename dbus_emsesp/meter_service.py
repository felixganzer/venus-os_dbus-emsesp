import os

import dbus
from vedbus import VeDbusService


PHASES = ("L1", "L2", "L3")


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
    """Ein dreiphasiges virtuelles Waermepumpen-Energiemessgeraet."""

    def __init__(self, config, electrical, version, category):
        self.category = category
        self.voltage = float(electrical.get("voltage_v", 230.0))
        self.update_index = 0

        # Jeder VeDbusService benoetigt seine eigene Verbindung, wenn mehrere
        # Services in demselben Prozess registriert werden.
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

        # Gesamtwerte aller drei Phasen.
        add("/Ac/Power", 0.0, gettextcallback=fmt("W", 0))
        add("/Ac/Current", 0.0, gettextcallback=fmt("A", 2))
        add("/Ac/Voltage", self.voltage, gettextcallback=fmt("V", 1))
        add("/Ac/PowerFactor", 1.0)
        add("/Ac/Energy/Forward", 0.0, gettextcallback=fmt("kWh", 3))
        add("/Ac/Energy/Reverse", 0.0, gettextcallback=fmt("kWh", 3))

        # Alle drei Phasen werden identisch belastet. Leistung und Energie
        # jedes Devices werden exakt durch drei geteilt.
        for phase in PHASES:
            base = "/Ac/{}/".format(phase)
            add(base + "Power", 0.0, gettextcallback=fmt("W", 0))
            add(base + "Current", 0.0, gettextcallback=fmt("A", 2))
            add(base + "Voltage", self.voltage, gettextcallback=fmt("V", 1))
            add(base + "PowerFactor", 1.0)
            add(base + "Energy/Forward", 0.0, gettextcallback=fmt("kWh", 3))
            add(base + "Energy/Reverse", 0.0, gettextcallback=fmt("kWh", 3))

        # Gesamtenergie bleibt der Gesamtzaehler des Devices.
        add("/Energy/Today", 0.0, gettextcallback=fmt("kWh", 3))
        add("/Runtime/Today", 0, gettextcallback=fmt("s", 0))
        add("/Runtime/Total", 0, gettextcallback=fmt("s", 0))
        add("/Position", int(electrical.get("position", 0)))
        add("/NrOfPhases", 3)
        add("/DeviceType", 0)
        add("/ErrorCode", 0)
        add("/IsGenericEnergyMeter", 1)
        add("/OperatingMode", "unknown")
        self.service.register()

    def update(self, values, connected, mode, error_code=0):
        total_power = max(0.0, float(values["power_w"] or 0.0))
        total_energy = max(0.0, float(values["energy_total_kwh"] or 0.0))
        phase_power = total_power / 3.0
        phase_energy = total_energy / 3.0
        phase_current = phase_power / self.voltage if self.voltage > 0 else 0.0
        total_current = phase_current * 3.0

        self.service["/Ac/Power"] = total_power
        self.service["/Ac/Current"] = total_current
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
