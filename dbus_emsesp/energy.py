import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

LOG = logging.getLogger("dbus-emsesp.energy")
CATEGORIES = ("heating", "dhw", "aux_heater")


class ThreeDeviceEnergyTracker:
    def __init__(self, state_file, save_interval_seconds=60, clock=None):
        self.state_file = Path(state_file)
        self.save_interval = max(10, int(save_interval_seconds))
        self.clock = clock or time.time
        now = self.clock()
        self.state = {"date": self._date(now), "last_update_epoch": now}
        for category in CATEGORIES:
            self.state[category] = {
                "energy_today_kwh": 0.0,
                "energy_total_kwh": 0.0,
                "runtime_today_seconds": 0.0,
                "runtime_total_seconds": 0.0,
            }
        self._last_save = 0.0
        self._load()
        self.state["last_update_epoch"] = now

    @staticmethod
    def _date(epoch):
        return datetime.fromtimestamp(epoch).date().isoformat()

    def _load(self):
        try:
            with self.state_file.open("r", encoding="utf-8") as handle:
                stored = json.load(handle)
            if isinstance(stored, dict):
                self.state.update({k: v for k, v in stored.items() if k in self.state})
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as exc:
            LOG.warning("Could not load counters: %s", exc)

    def _roll_day(self, now):
        today = self._date(now)
        if self.state.get("date") == today:
            return
        self.state["date"] = today
        for category in CATEGORIES:
            self.state[category]["energy_today_kwh"] = 0.0
            self.state[category]["runtime_today_seconds"] = 0.0
        self._save(now, force=True)

    def update(self, powers, now=None):
        now = self.clock() if now is None else float(now)
        self._roll_day(now)
        previous = float(self.state.get("last_update_epoch", now))
        elapsed = max(0.0, min(now - previous, 300.0))
        self.state["last_update_epoch"] = now
        result = {}
        for category in CATEGORIES:
            power = max(0.0, float(powers.get(category, 0.0) or 0.0))
            delta = power * elapsed / 3600000.0
            counter = self.state[category]
            counter["energy_today_kwh"] += delta
            counter["energy_total_kwh"] += delta
            if power > 0.0:
                counter["runtime_today_seconds"] += elapsed
                counter["runtime_total_seconds"] += elapsed
            result[category] = {
                "power_w": power,
                "energy_today_kwh": round(counter["energy_today_kwh"], 4),
                "energy_total_kwh": round(counter["energy_total_kwh"], 4),
                "runtime_today_seconds": int(counter["runtime_today_seconds"]),
                "runtime_total_seconds": int(counter["runtime_total_seconds"]),
            }
        self._save(now)
        return result

    def _save(self, now, force=False):
        if not force and now - self._last_save < self.save_interval:
            return
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_file.with_suffix(".tmp")
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(self.state, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state_file)
            self._last_save = now
        except OSError as exc:
            LOG.warning("Could not persist counters: %s", exc)
