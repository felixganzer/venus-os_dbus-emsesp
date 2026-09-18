from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, Optional


TRUE_VALUES = {"1", "true", "on", "yes", "active", "an", "ein"}
FALSE_VALUES = {"0", "false", "off", "no", "inactive", "aus"}


def unwrap(value):
    if isinstance(value, dict):
        for key in ("value", "v", "raw"):
            if key in value:
                return unwrap(value[key])
    return value


def normalize(value):
    value = unwrap(value)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        low = text.lower()
        if low in TRUE_VALUES:
            return True
        if low in FALSE_VALUES:
            return False
        try:
            return float(text.replace(",", "."))
        except ValueError:
            return text
    return value


def flatten(data, prefix=""):
    result = {}
    if isinstance(data, dict):
        for key, value in data.items():
            path = "{}.{}".format(prefix, key) if prefix else str(key)
            result[path.lower()] = normalize(value)
            if isinstance(value, dict):
                result.update(flatten(value, path))
    return result


def first(flat, candidates, default=None):
    for candidate in candidates:
        key = str(candidate).lower()
        if key in flat and flat[key] not in (None, ""):
            return normalize(flat[key])
    return default


def number(value, default=None):
    value = normalize(value)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def boolean(value, default=False):
    value = normalize(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return default


@dataclass
class HeatPumpState:
    source: str = "unknown"
    mode: str = "standby"
    status_code: int = 0

    outside_temperature_c: Optional[float] = None
    flow_temperature_c: Optional[float] = None
    return_temperature_c: Optional[float] = None
    dhw_temperature_c: Optional[float] = None
    target_flow_temperature_c: Optional[float] = None
    system_pressure_bar: Optional[float] = None
    primary_flow_l_h: Optional[float] = None

    compressor_active: bool = False
    compressor_speed_percent: Optional[float] = None
    heating_active: bool = False
    dhw_active: bool = False
    defrost_active: bool = False
    aux_heater_active: bool = False
    aux_heater_level_percent: float = 0.0

    compressor_electrical_power_w: float = 0.0
    aux_heater_power_w: float = 0.0
    total_electrical_power_w: float = 0.0
    thermal_power_w: Optional[float] = None
    cop: Optional[float] = None

    electrical_energy_total_kwh: Optional[float] = None
    electrical_energy_compressor_kwh: Optional[float] = None
    electrical_energy_aux_heater_kwh: Optional[float] = None
    electrical_energy_heating_kwh: Optional[float] = None
    electrical_energy_dhw_kwh: Optional[float] = None
    electrical_energy_cooling_kwh: Optional[float] = None

    thermal_energy_total_kwh: Optional[float] = None
    thermal_energy_heating_kwh: Optional[float] = None
    thermal_energy_dhw_kwh: Optional[float] = None
    thermal_energy_cooling_kwh: Optional[float] = None

    runtime_total_minutes: Optional[float] = None
    runtime_active_minutes: Optional[float] = None
    runtime_heating_minutes: Optional[float] = None
    runtime_dhw_minutes: Optional[float] = None
    runtime_cooling_minutes: Optional[float] = None
    compressor_starts_total: Optional[float] = None
    compressor_starts_heating: Optional[float] = None
    compressor_starts_dhw: Optional[float] = None
    compressor_starts_cooling: Optional[float] = None

    def as_dict(self):
        return asdict(self)


class EmsEspModelMapper:
    STATUS_CODES = {"standby": 0, "heating": 1, "dhw": 2, "defrost": 3, "cooling": 4}

    def __init__(self, mapping, aux_heater_nominal_power_w=9000.0):
        self.mapping = mapping
        self.aux_nominal = float(aux_heater_nominal_power_w)

    def _get(self, flat, name, default=None):
        return first(flat, self.mapping.get(name, []), default)

    def _mode(self, activity, heating, dhw):
        text = str(activity or "").strip().lower()
        if any(token in text for token in ("abtauen", "defrost")):
            return "defrost"
        if any(token in text for token in ("warmwasser", "dhw", "tapwater")):
            return "dhw"
        if any(token in text for token in ("kühlen", "cooling", "cool")):
            return "cooling"
        if any(token in text for token in ("heizen", "heating", "heat")):
            return "heating"
        if dhw:
            return "dhw"
        if heating:
            return "heating"
        return "standby"

    def map(self, raw, source="rest"):
        flat = flatten(raw)
        heating_active = boolean(self._get(flat, "heating_active"))
        dhw_active = boolean(self._get(flat, "dhw_active"))
        activity = self._get(flat, "activity")
        mode = self._mode(activity, heating_active, dhw_active)
        compressor_active = boolean(self._get(flat, "compressor_active"))
        aux_level = number(self._get(flat, "aux_heater_level_percent"), 0.0) or 0.0
        aux_active = boolean(self._get(flat, "aux_heater_active"), aux_level > 0.0)
        compressor_power = number(self._get(flat, "compressor_electrical_power_w"), 0.0) or 0.0
        aux_power = number(self._get(flat, "aux_heater_power_w"))
        if aux_power is None:
            aux_power = self.aux_nominal * max(0.0, min(100.0, aux_level)) / 100.0
        thermal_kw = number(self._get(flat, "thermal_power_kw"))
        thermal_w = thermal_kw * 1000.0 if thermal_kw is not None else None
        total_power = max(0.0, compressor_power) + max(0.0, aux_power)
        cop = number(self._get(flat, "cop"))
        if cop is None and thermal_w is not None and total_power > 0.0:
            cop = thermal_w / total_power

        def n(name):
            return number(self._get(flat, name))

        return HeatPumpState(
            source=source,
            mode=mode,
            status_code=self.STATUS_CODES.get(mode, 0),
            outside_temperature_c=n("outside_temperature_c"),
            flow_temperature_c=n("flow_temperature_c"),
            return_temperature_c=n("return_temperature_c"),
            dhw_temperature_c=n("dhw_temperature_c"),
            target_flow_temperature_c=n("target_flow_temperature_c"),
            system_pressure_bar=n("system_pressure_bar"),
            primary_flow_l_h=n("primary_flow_l_h"),
            compressor_active=compressor_active,
            compressor_speed_percent=n("compressor_speed_percent"),
            heating_active=heating_active,
            dhw_active=dhw_active,
            defrost_active=mode == "defrost",
            aux_heater_active=aux_active,
            aux_heater_level_percent=aux_level,
            compressor_electrical_power_w=max(0.0, compressor_power),
            aux_heater_power_w=max(0.0, aux_power),
            total_electrical_power_w=total_power,
            thermal_power_w=thermal_w,
            cop=cop,
            electrical_energy_total_kwh=n("electrical_energy_total_kwh"),
            electrical_energy_compressor_kwh=n("electrical_energy_compressor_kwh"),
            electrical_energy_aux_heater_kwh=n("electrical_energy_aux_heater_kwh"),
            electrical_energy_heating_kwh=n("electrical_energy_heating_kwh"),
            electrical_energy_dhw_kwh=n("electrical_energy_dhw_kwh"),
            electrical_energy_cooling_kwh=n("electrical_energy_cooling_kwh"),
            thermal_energy_total_kwh=n("thermal_energy_total_kwh"),
            thermal_energy_heating_kwh=n("thermal_energy_heating_kwh"),
            thermal_energy_dhw_kwh=n("thermal_energy_dhw_kwh"),
            thermal_energy_cooling_kwh=n("thermal_energy_cooling_kwh"),
            runtime_total_minutes=n("runtime_total_minutes"),
            runtime_active_minutes=n("runtime_active_minutes"),
            runtime_heating_minutes=n("runtime_heating_minutes"),
            runtime_dhw_minutes=n("runtime_dhw_minutes"),
            runtime_cooling_minutes=n("runtime_cooling_minutes"),
            compressor_starts_total=n("compressor_starts_total"),
            compressor_starts_heating=n("compressor_starts_heating"),
            compressor_starts_dhw=n("compressor_starts_dhw"),
            compressor_starts_cooling=n("compressor_starts_cooling"),
        )
