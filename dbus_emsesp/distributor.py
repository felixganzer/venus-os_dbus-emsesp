class PowerDistributor:
    """Verteilt die Leistung ohne Doppelzaehlung auf drei virtuelle Geraete."""

    DHW_MODES = {"dhw", "hotwater", "warmwater", "warmwasser", "ww"}

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

    def distribute(self, total_power_w, operating_mode, aux_heater_power_w, aux_heater_active=False):
        total = self._number(total_power_w)
        aux = min(total, self._number(aux_heater_power_w))
        if self._active(aux_heater_active) and aux == 0.0:
            # Aktivsignal ohne Leistungswert darf keine Energie erfinden.
            aux = 0.0
        compressor = max(0.0, total - aux)
        mode = str(operating_mode or "unknown").strip().lower()

        # Warmwasser wird explizit getrennt. Alle anderen Verdichteranteile,
        # inklusive Abtauen und unbekannter Betriebsart, landen bei Heizung.
        if mode in self.DHW_MODES:
            heating, dhw = 0.0, compressor
        else:
            heating, dhw = compressor, 0.0

        return {
            "heating": heating,
            "dhw": dhw,
            "aux_heater": aux,
            "total": total,
            "mode": mode,
        }
