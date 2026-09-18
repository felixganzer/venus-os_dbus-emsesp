import math
import random
import time


class DummyEmsEspClient:
    """Stateful thermal simulation for display and VRM development."""

    STATUS_CODES = {
        "standby": 0,
        "heating": 1,
        "dhw": 2,
        "defrost": 3,
    }

    def __init__(self, config=None, clock=None):
        self.config = config or {}
        self.clock = clock or time.time
        now = self.clock()
        self.started_at = now - float(
            self.config.get("start_time_offset_seconds", 0)
        )
        self.last_update = now
        self.duration = max(
            300.0,
            float(self.config.get("scenario_duration_seconds", 1800)),
        )
        self.variation = max(
            0.0,
            min(0.45, float(self.config.get("power_variation_fraction", 0.18))),
        )
        self.seed = int(self.config.get("variation_seed", 5800))
        self.thermal_time_constant = max(
            20.0,
            float(self.config.get("thermal_time_constant_seconds", 90)),
        )

        self.flow_temp = float(self.config.get("initial_flow_temperature_c", 28.0))
        self.return_temp = float(self.config.get("initial_return_temperature_c", 26.0))
        self.dhw_temp = float(self.config.get("initial_dhw_temperature_c", 48.0))

    @staticmethod
    def _clamp(value, minimum, maximum):
        return max(minimum, min(maximum, value))

    @staticmethod
    def _approach(current, target, elapsed, time_constant):
        if elapsed <= 0.0:
            return current
        factor = 1.0 - math.exp(-elapsed / time_constant)
        return current + (target - current) * factor

    def _minute_factor(self, elapsed):
        """New deterministic load target each minute with smooth interpolation."""
        minute = int(elapsed // 60)
        progress = (elapsed % 60) / 60.0
        current = random.Random(self.seed + minute).uniform(-1.0, 1.0)
        following = random.Random(self.seed + minute + 1).uniform(-1.0, 1.0)
        interpolated = current + (following - current) * progress
        ripple = 0.12 * math.sin(elapsed / 11.0)
        return 1.0 + self.variation * (interpolated + ripple)

    def _state(self, elapsed):
        ratio = (elapsed % self.duration) / self.duration
        if ratio < 0.30:
            return "heating", 1850.0, 0.0
        if ratio < 0.45:
            return "heating", 2100.0, 3000.0
        if ratio < 0.70:
            return "dhw", 2250.0, 0.0
        if ratio < 0.82:
            return "dhw", 2450.0, 3000.0
        if ratio < 0.94:
            return "defrost", 2600.0, 0.0
        return "standby", 0.0, 0.0

    def _outside_temperature(self, elapsed):
        base = float(self.config.get("outside_temperature_base_c", 8.0))
        amplitude = float(self.config.get("outside_temperature_amplitude_c", 4.0))
        slow_cycle = math.sin(2.0 * math.pi * elapsed / max(self.duration * 2.0, 3600.0))
        weather_wave = 0.45 * math.sin(elapsed / 173.0)
        return base + amplitude * slow_cycle + weather_wave

    def _thermal_targets(self, mode, outside, elapsed):
        if mode == "heating":
            # Colder outside air raises the simulated heating-curve target.
            flow_target = self._clamp(31.0 + (10.0 - outside) * 0.38, 29.0, 42.0)
            return_target = flow_target - (4.0 + 0.5 * math.sin(elapsed / 47.0))
            dhw_target = 46.5
        elif mode == "dhw":
            flow_target = 52.0 + 1.2 * math.sin(elapsed / 41.0)
            return_target = flow_target - 5.2
            dhw_target = 53.0
        elif mode == "defrost":
            flow_target = 23.5
            return_target = 27.0
            dhw_target = 48.0
        else:
            flow_target = 26.0
            return_target = 25.0
            dhw_target = 47.0
        return flow_target, return_target, dhw_target

    def _cop(self, mode, outside, flow, aux_active):
        if mode == "standby":
            return 0.0
        if mode == "defrost":
            return 1.2
        lift = max(8.0, flow - outside)
        base = 5.3 - 0.055 * lift
        if mode == "dhw":
            base -= 0.45
        if aux_active:
            base -= 0.65
        return round(self._clamp(base, 1.2, 5.2), 2)

    def read_all(self):
        now = self.clock()
        elapsed = now - self.started_at
        delta = max(0.0, min(now - self.last_update, 60.0))
        self.last_update = now

        mode, compressor_base, aux_base = self._state(elapsed)
        compressor = max(0.0, compressor_base * self._minute_factor(elapsed))
        aux_factor = 1.0 + 0.025 * math.sin(elapsed / 19.0)
        aux = max(0.0, aux_base * aux_factor)
        total = compressor + aux

        outside = self._outside_temperature(elapsed)
        flow_target, return_target, dhw_target = self._thermal_targets(
            mode, outside, elapsed
        )
        self.flow_temp = self._approach(
            self.flow_temp, flow_target, delta, self.thermal_time_constant
        )
        self.return_temp = self._approach(
            self.return_temp, return_target, delta, self.thermal_time_constant * 1.15
        )
        self.dhw_temp = self._approach(
            self.dhw_temp, dhw_target, delta, self.thermal_time_constant * 2.5
        )
        cop = self._cop(mode, outside, self.flow_temp, aux > 0.0)

        return {
            "heatpump": {
                "power": round(total, 1),
                "status": mode,
                "statuscode": self.STATUS_CODES[mode],
                "compressor": int(compressor > 0.0),
                "auxheaterpower": round(aux, 1),
                "auxheateractive": int(aux > 0.0),
                "outdoortemp": round(outside, 1),
                "flowtemp": round(self.flow_temp, 1),
                "returntemp": round(self.return_temp, 1),
                "dhwtemp": round(self.dhw_temp, 1),
                "cop": cop,
            },
            "boiler": {
                "status": mode,
                "outdoortemp": round(outside, 1),
                "curflowtemp": round(self.flow_temp, 1),
                "returntemp": round(self.return_temp, 1),
                "dhwtemp": round(self.dhw_temp, 1),
            },
            "system": {"connected": True, "mode": "dummy"},
        }, {}
