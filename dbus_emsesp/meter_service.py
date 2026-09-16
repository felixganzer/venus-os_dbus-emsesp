import os

import dbus
from vedbus import VeDbusService


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
    ):
        self.category = category
        self.voltage = float(
            electrical.get("voltage_v", 230.0)
        )
        self.update_index = 0

        # Für jedes virtuelle Gerät eine eigene D-Bus-Verbindung.
        # Das ermöglicht mehrere VeDbusService-Instanzen
        # innerhalb desselben Python-Prozesses.
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

        add(
            "/Mgmt/ProcessName",
            os.path.abspath(__file__),
        )
        add(
            "/Mgmt/ProcessVersion",
            version,
        )
        add(
            "/Mgmt/Connection",
            "EMS-ESP shared REST bridge",
        )

        add(
            "/DeviceInstance",
            int(config["device_instance"]),
        )
        add(
            "/ProductId",
            int(config.get("product_id", 0xFFFF)),
        )
        add(
            "/ProductName",
            config["product_name"],
        )
        add(
            "/CustomName",
            config["custom_name"],
        )
        add(
            "/FirmwareVersion",
            version,
        )
        add(
            "/Serial",
            "emsesp-{}".format(category),
        )

        add("/Connected", 0)
        add("/UpdateIndex", 0)

        add(
            "/Ac/Power",
            0.0,
            gettextcallback=fmt("W", 0),
        )
        add(
            "/Ac/L1/Power",
            0.0,
            gettextcallback=fmt("W", 0),
        )

        add(
            "/Ac/Voltage",
            self.voltage,
            gettextcallback=fmt("V", 1),
        )
        add(
            "/Ac/L1/Voltage",
            self.voltage,
            gettextcallback=fmt("V", 1),
        )

        add(
            "/Ac/Current",
            0.0,
            gettextcallback=fmt("A", 2),
        )
        add(
            "/Ac/L1/Current",
            0.0,
            gettextcallback=fmt("A", 2),
        )

        add("/Ac/PowerFactor", 1.0)
        add("/Ac/L1/PowerFactor", 1.0)

        add(
            "/Ac/Energy/Forward",
            0.0,
            gettextcallback=fmt("kWh", 3),
        )
        add(
            "/Ac/L1/Energy/Forward",
            0.0,
            gettextcallback=fmt("kWh", 3),
        )
        add(
            "/Ac/Energy/Reverse",
            0.0,
            gettextcallback=fmt("kWh", 3),
        )
        add(
            "/Ac/L1/Energy/Reverse",
            0.0,
            gettextcallback=fmt("kWh", 3),
        )

        add(
            "/Energy/Today",
            0.0,
            gettextcallback=fmt("kWh", 3),
        )
        add(
            "/Runtime/Today",
            0,
            gettextcallback=fmt("s", 0),
        )
        add(
            "/Runtime/Total",
            0,
            gettextcallback=fmt("s", 0),
        )

        add(
            "/Position",
            int(electrical.get("position", 1)),
        )
        add(
            "/PhaseSetting",
            int(electrical.get("phase_setting", 1)),
        )

        add("/DeviceType", 0)
        add("/ErrorCode", 0)
        add("/IsGenericEnergyMeter", 1)
        add("/OperatingMode", "unknown")

        self.service.register()

    def update(self, values, connected, mode, error_code=0):
        power = float(values["power_w"])
        current = power / self.voltage if self.voltage > 0 else 0.0
        for path in ("/Ac/Power", "/Ac/L1/Power"):
            self.service[path] = power
        for path in ("/Ac/Current", "/Ac/L1/Current"):
            self.service[path] = current
        self.service["/Ac/Energy/Forward"] = values["energy_total_kwh"]
        self.service["/Ac/L1/Energy/Forward"] = values["energy_total_kwh"]
        self.service["/Energy/Today"] = values["energy_today_kwh"]
        self.service["/Runtime/Today"] = values["runtime_today_seconds"]
        self.service["/Runtime/Total"] = values["runtime_total_seconds"]
        self.service["/OperatingMode"] = mode
        self.service["/Connected"] = int(bool(connected))
        self.service["/ErrorCode"] = int(error_code)
        self.update_index = (self.update_index + 1) % 256
        self.service["/UpdateIndex"] = self.update_index
