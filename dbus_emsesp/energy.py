import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

LOG = logging.getLogger("dbus-emsesp.energy")


class EnergyRuntimeTracker:
    """Persistiert Energie- und Laufzeitzaehler fuer Gesamt, Heizen, WW und Heizstab."""

    CATEGORIES = ("total", "heating", "dhw", "aux_heater")

    def __init__(self, state_file, save_interval_seconds=60, clock=None):
        self.state_file = Path(state_file)
        self.save_interval = max(10, int(save_interval_seconds))
        self.clock = clock or time.time
        now = self.clock()
        self.state = {
            "date": self._local_date(now),
            "last_update_epoch": now,
        }
        for category in self.CATEGORIES:
            self.state[f"energy_{category}_today_kwh"] = 0.0
            self.state[f"energy_{category}_total_kwh"] = 0.0
            self.state[f"runtime_{category}_today_seconds"] = 0.0
            self.state[f"runtime_{category}_total_seconds"] = 0.0
        self._last_save_epoch = 0.0
        self._load()
        # Stillstandszeit waehrend eines Dienstneustarts nicht integrieren.
        self.state["last_update_epoch"] = now

    @staticmethod
    def _local_date(epoch):
        return datetime.fromtimestamp(epoch).date().isoformat()

    @staticmethod
    def _number(value):
        try:
            return max(0.0, float(value or 0.0))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _active(value):
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "on", "yes", "active")
        return bool(value)

    @staticmethod
    def _normalize_mode(value):
        mode = str(value or "unknown").strip().lower()
        aliases = {
            "heat": "heating",
            "heizen": "heating",
            "raumheizung": "heating",
            "hotwater": "dhw",
            "warmwater": "dhw",
            "warmwasser": "dhw",
            "ww": "dhw",
        }
        return aliases.get(mode, mode)

    def _load(self):
        try:
            with self.state_file.open("r", encoding="utf-8") as handle:
                stored = json.load(handle)
            for key in self.state:
                if key in stored:
                    self.state[key] = stored[key]
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError) as exc:
            LOG.warning("Zaehlerstand konnte nicht geladen werden: %s", exc)

    def _roll_day_if_needed(self, now):
        today = self._local_date(now)
        if self.state.get("date") == today:
            return
        self.state["date"] = today
        for key in self.state:
            if "_today_" in key:
                self.state[key] = 0.0
        self._save(now, force=True)

    def _add_energy(self, category, power_w, elapsed_seconds):
        delta_kwh = self._number(power_w) * elapsed_seconds / 3600000.0
        self.state[f"energy_{category}_today_kwh"] += delta_kwh
        self.state[f"energy_{category}_total_kwh"] += delta_kwh

    def _add_runtime(self, category, active, elapsed_seconds):
        if not self._active(active):
            return
        self.state[f"runtime_{category}_today_seconds"] += elapsed_seconds
        self.state[f"runtime_{category}_total_seconds"] += elapsed_seconds

    def update(
        self,
        total_power_w,
        operating_mode,
        compressor_active,
        aux_heater_power_w=0.0,
        aux_heater_active=False,
        now=None,
    ):
        now = self.clock() if now is None else float(now)
        self._roll_day_if_needed(now)
        previous = float(self.state.get("last_update_epoch", now))
        # Begrenzung verhindert grosse Spruenge nach Uhrzeitkorrekturen oder Haengern.
        elapsed = max(0.0, min(now - previous, 300.0))
        self.state["last_update_epoch"] = now

        total_power = self._number(total_power_w)
        aux_power = min(total_power, self._number(aux_heater_power_w))
        mode = self._normalize_mode(operating_mode)
        aux_active = self._active(aux_heater_active) or aux_power > 0.0

        self._add_energy("total", total_power, elapsed)
        self._add_runtime("total", compressor_active, elapsed)

        if mode == "heating":
            self._add_energy("heating", total_power, elapsed)
            self._add_runtime("heating", compressor_active, elapsed)
        elif mode == "dhw":
            self._add_energy("dhw", total_power, elapsed)
            self._add_runtime("dhw", compressor_active, elapsed)

        # Heizstab ist eine Teilmenge des Gesamtverbrauchs und wird separat ausgewiesen.
        self._add_energy("aux_heater", aux_power, elapsed)
        self._add_runtime("aux_heater", aux_active, elapsed)

        self._save(now)
        return self.snapshot()

    def snapshot(self):
        result = {}
        for key, value in self.state.items():
            if key.startswith("energy_"):
                result[key] = round(float(value), 4)
            elif key.startswith("runtime_"):
                result[key] = int(value)
        return result

    def _save(self, now=None, force=False):
        now = self.clock() if now is None else float(now)
        if not force and now - self._last_save_epoch < self.save_interval:
            return
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_file.with_suffix(".tmp")
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(self.state, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state_file)
            self._last_save_epoch = now
        except OSError as exc:
            LOG.warning("Zaehlerstand konnte nicht gespeichert werden: %s", exc)
