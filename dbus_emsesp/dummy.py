import math
import random
import time


class DummyEmsEspClient:
    def __init__(self, config=None, clock=None):
        self.config = config or {}
        self.clock = clock or time.time
        now = self.clock()
        self.started_at = now - float(self.config.get("start_time_offset_seconds", 0))
        self.last_update = now
        self.duration = max(300.0, float(self.config.get("scenario_duration_seconds", 1800)))
        self.variation = float(self.config.get("power_variation_fraction", 0.18))
        self.seed = int(self.config.get("variation_seed", 5800))
        self.flow = 28.0
        self.ret = 26.0
        self.dhw = 48.0
        self.energy_heat = 0.0
        self.energy_dhw = 0.0
        self.energy_aux = 0.0
        self.thermal_heat = 0.0
        self.thermal_dhw = 0.0
        self.runtime_heat = 0.0
        self.runtime_dhw = 0.0
        self.starts_total = 0
        self.starts_heat = 0
        self.starts_dhw = 0
        self.last_comp_on = False
        self.last_mode = "standby"

    @staticmethod
    def _approach(current, target, elapsed, tau):
        return current + (target - current) * (1.0 - math.exp(-elapsed / tau))

    def _minute_factor(self, elapsed):
        minute = int(elapsed // 60)
        p = (elapsed % 60) / 60.0
        a = random.Random(self.seed + minute).uniform(-1.0, 1.0)
        b = random.Random(self.seed + minute + 1).uniform(-1.0, 1.0)
        return 1.0 + self.variation * (a + (b - a) * p + 0.12 * math.sin(elapsed / 11.0))

    def _state(self, elapsed):
        r = (elapsed % self.duration) / self.duration
        if r < 0.30: return "heating", 1850.0, 0.0
        if r < 0.45: return "heating", 2100.0, 3000.0
        if r < 0.70: return "dhw", 2250.0, 0.0
        if r < 0.82: return "dhw", 2450.0, 3000.0
        if r < 0.94: return "defrost", 2600.0, 0.0
        return "standby", 0.0, 0.0

    def read_all(self):
        now = self.clock()
        elapsed = now - self.started_at
        dt = max(0.0, min(now - self.last_update, 60.0))
        self.last_update = now
        mode, comp_base, aux_base = self._state(elapsed)
        comp = max(0.0, comp_base * self._minute_factor(elapsed))
        aux = max(0.0, aux_base * (1.0 + 0.025 * math.sin(elapsed / 19.0)))
        outside = 8.0 + 4.0 * math.sin(2.0 * math.pi * elapsed / max(3600.0, self.duration * 2.0))

        if mode == "heating":
            flow_target = max(29.0, min(42.0, 31.0 + (10.0 - outside) * 0.38))
            ret_target, dhw_target = flow_target - 4.5, 46.5
        elif mode == "dhw":
            flow_target, ret_target, dhw_target = 52.0, 46.8, 53.0
        elif mode == "defrost":
            flow_target, ret_target, dhw_target = 23.5, 27.0, 48.0
        else:
            flow_target, ret_target, dhw_target = 26.0, 25.0, 47.0
        self.flow = self._approach(self.flow, flow_target, dt, 90.0)
        self.ret = self._approach(self.ret, ret_target, dt, 105.0)
        self.dhw = self._approach(self.dhw, dhw_target, dt, 225.0)

        lift = max(8.0, self.flow - outside)
        cop = 0.0 if mode == "standby" else (1.2 if mode == "defrost" else max(1.2, min(5.2, 5.3 - 0.055 * lift - (0.45 if mode == "dhw" else 0.0) - (0.65 if aux else 0.0))))
        thermal_w = comp * cop
        if mode in ("heating", "defrost"):
            self.energy_heat += comp * dt / 3600000.0
            self.thermal_heat += thermal_w * dt / 3600000.0
            self.runtime_heat += dt / 60.0
        elif mode == "dhw":
            self.energy_dhw += comp * dt / 3600000.0
            self.thermal_dhw += thermal_w * dt / 3600000.0
            self.runtime_dhw += dt / 60.0
        self.energy_aux += aux * dt / 3600000.0

        comp_on = comp > 0.0
        if comp_on and not self.last_comp_on:
            self.starts_total += 1
            if mode == "dhw": self.starts_dhw += 1
            else: self.starts_heat += 1
        self.last_comp_on = comp_on
        self.last_mode = mode

        activity = {"heating":"heating", "dhw":"dhw", "defrost":"defrost", "standby":"none"}[mode]
        boiler = {
            "outdoortemp": round(outside, 1), "curflowtemp": round(self.flow, 1),
            "rettemp": round(self.ret, 1), "hptc0": round(self.ret, 1),
            "hptc1": round(self.flow, 1), "hpcurrpower": round(comp, 1),
            "hppower": round(thermal_w / 1000.0, 2), "hpcompon": comp_on,
            "hpactivity": activity, "heatingactive": mode == "heating",
            "tapwateractive": mode == "dhw", "hpcompspd": round(min(100.0, comp / 30.0), 1),
            "auxheaterlevel": round(aux / 90.0, 1), "syspress": 1.7,
            "pc0flow": 850 if comp_on else 0,
            "metertotal": round(self.energy_heat + self.energy_dhw + self.energy_aux, 3),
            "metercomp": round(self.energy_heat + self.energy_dhw, 3),
            "metereheat": round(self.energy_aux, 3), "meterheat": round(self.energy_heat, 3),
            "nrgtotal": round(self.thermal_heat + self.thermal_dhw, 3),
            "nrgheat": round(self.thermal_heat, 3),
            "uptimetotal": round(elapsed / 60.0, 1),
            "uptimecontrol": round(self.runtime_heat + self.runtime_dhw, 1),
            "uptimecompheating": round(self.runtime_heat, 1),
            "totalcompstarts": self.starts_total, "heatingstarts": self.starts_heat,
            "dhw": {
                "curtemp2": round(self.dhw, 1), "meter": round(self.energy_dhw, 3),
                "nrg": round(self.thermal_dhw, 3), "uptimecomp": round(self.runtime_dhw, 1),
                "startshp": self.starts_dhw, "charging": mode == "dhw"
            }
        }
        return {"boiler": boiler, "heatpump": boiler, "system": {"connected": True, "mode": "dummy"}}, {}
