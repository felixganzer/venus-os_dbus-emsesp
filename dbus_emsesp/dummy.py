import math
import random
import time


class DummyEmsEspClient:
    """Simulation mit Betriebsphasen und neuer Leistungsvariation je Minute."""

    def __init__(self, config=None, clock=None):
        self.config = config or {}
        self.clock = clock or time.time
        self.started_at = self.clock() - float(
            self.config.get("start_time_offset_seconds", 0)
        )
        self.duration = max(
            300.0,
            float(self.config.get("scenario_duration_seconds", 1800)),
        )
        self.variation = max(
            0.0,
            min(0.45, float(self.config.get("power_variation_fraction", 0.18))),
        )
        self.seed = int(self.config.get("variation_seed", 5800))

    def _minute_factor(self, elapsed):
        """Erzeugt pro Minute ein neues Ziel und interpoliert weich dorthin."""
        minute = int(elapsed // 60)
        progress = (elapsed % 60) / 60.0
        current = random.Random(self.seed + minute).uniform(-1.0, 1.0)
        following = random.Random(self.seed + minute + 1).uniform(-1.0, 1.0)
        interpolated = current + (following - current) * progress
        # Kleine schnellere Modulation verhindert vollkommen gerade Rampen.
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

    def read_all(self):
        elapsed = self.clock() - self.started_at
        mode, compressor_base, aux_base = self._state(elapsed)
        factor = self._minute_factor(elapsed)

        # Verdichter moduliert kontinuierlich. Der Heizstab bleibt stufig,
        # bekommt aber eine kleine realistische Leistungsabweichung.
        compressor = max(0.0, compressor_base * factor)
        aux_factor = 1.0 + 0.025 * math.sin(elapsed / 19.0)
        aux = max(0.0, aux_base * aux_factor)
        total = compressor + aux

        outside = 8.0 + 4.0 * math.sin(elapsed / 300.0)
        return {
            "heatpump": {
                "power": round(total, 1),
                "status": mode,
                "compressor": int(compressor > 0.0),
                "auxheaterpower": round(aux, 1),
                "auxheateractive": int(aux > 0.0),
                "outdoortemp": round(outside, 1),
            },
            "boiler": {"status": mode},
            "system": {"connected": True, "mode": "dummy"},
        }, {}
