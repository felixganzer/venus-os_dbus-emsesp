import math
import time


class DummyEmsEspClient:
    """Erzeugt realistisch veränderliche EMS-ESP-Daten ohne Netzwerkzugriff."""

    def __init__(self, config=None, clock=None):
        self.config = config or {}
        self.clock = clock or time.time
        self.started_at = self.clock() - float(
            self.config.get("start_time_offset_seconds", 0)
        )
        self.scenario_duration = max(
            300.0, float(self.config.get("scenario_duration_seconds", 1800))
        )
        self.outside_base = float(
            self.config.get("outside_temperature_base_c", 8.0)
        )
        self.outside_amplitude = float(
            self.config.get("outside_temperature_amplitude_c", 4.0)
        )

    def _state(self, elapsed):
        phase = elapsed % self.scenario_duration
        ratio = phase / self.scenario_duration

        # 0-10 % Abtauen, 10-65 % Heizen, 65-80 % Warmwasser, 80-100 % Standby
        if ratio < 0.10:
            return "defrost", 1, 2600.0, 2.0
        if ratio < 0.65:
            return "heating", 1, 1850.0, 4.2
        if ratio < 0.80:
            return "dhw", 1, 2250.0, 3.4
        return "standby", 0, 0.0, 0.0

    def read_all(self):
        elapsed = self.clock() - self.started_at
        status, compressor, power, cop = self._state(elapsed)

        slow_wave = math.sin(elapsed / 300.0)
        fast_wave = math.sin(elapsed / 45.0)
        outside = self.outside_base + self.outside_amplitude * slow_wave

        if status == "defrost":
            flow = 25.0 + fast_wave
            return_temp = flow + 2.5
            dhw = 47.0
        elif status == "heating":
            flow = 34.0 + 2.0 * fast_wave
            return_temp = flow - 4.5
            dhw = 47.0 + 0.4 * slow_wave
        elif status == "dhw":
            flow = 51.0 + 1.5 * fast_wave
            return_temp = flow - 5.0
            dhw = 48.0 + 2.0 * min(1.0, (elapsed % self.scenario_duration) / 270.0)
        else:
            flow = 27.0 + 0.5 * fast_wave
            return_temp = flow - 1.0
            dhw = 49.0 - 0.3 * slow_wave

        data = {
            "boiler": {
                "outdoortemp": round(outside, 1),
                "curflowtemp": round(flow, 1),
                "returntemp": round(return_temp, 1),
                "dhwtemp": round(dhw, 1),
                "status": status,
            },
            "thermostat": {
                "outdoortemp": round(outside, 1),
            },
            "heatpump": {
                "outdoortemp": round(outside, 1),
                "flowtemp": round(flow, 1),
                "returntemp": round(return_temp, 1),
                "power": power,
                "cop": cop,
                "compressor": compressor,
                "status": status,
            },
            "system": {
                "connected": True,
                "mode": "dummy",
            },
        }
        return data, {}
