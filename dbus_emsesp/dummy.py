import math
import time


class DummyEmsEspClient:
    def __init__(self, config=None, clock=None):
        self.config = config or {}
        self.clock = clock or time.time
        self.started_at = self.clock() - float(self.config.get("start_time_offset_seconds", 0))
        self.duration = max(120.0, float(self.config.get("scenario_duration_seconds", 600)))

    def read_all(self):
        elapsed = self.clock() - self.started_at
        ratio = (elapsed % self.duration) / self.duration
        if ratio < 0.35:
            mode, compressor, aux = "heating", 1850.0, 0.0
        elif ratio < 0.50:
            mode, compressor, aux = "heating", 1850.0, 3000.0
        elif ratio < 0.75:
            mode, compressor, aux = "dhw", 2250.0, 0.0
        elif ratio < 0.85:
            mode, compressor, aux = "dhw", 2250.0, 3000.0
        elif ratio < 0.95:
            mode, compressor, aux = "defrost", 2600.0, 0.0
        else:
            mode, compressor, aux = "standby", 0.0, 0.0
        total = compressor + aux
        return {
            "heatpump": {
                "power": total,
                "status": mode,
                "compressor": int(compressor > 0),
                "auxheaterpower": aux,
                "auxheateractive": int(aux > 0),
                "outdoortemp": round(8.0 + 4.0 * math.sin(elapsed / 120.0), 1),
            },
            "boiler": {"status": mode},
            "system": {"connected": True, "mode": "dummy"},
        }, {}
