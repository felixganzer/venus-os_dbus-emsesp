# Lessons Learned / Fallstricke

Stand: 2026-11-14
Pflege: nach jeder gelösten nichttrivialen Fehlerursache.

## Gültige Erkenntnisse

- Die Gesamtleistung darf nicht doppelt gezählt werden; die Verteilungslogik muss in [dbus_emsesp/distributor.py](../dbus_emsesp/distributor.py) konsistent bleiben.
- Warmwasser und Heizung sind semantisch getrennt; die Logik muss die Betriebsmodi explizit berücksichtigen.
- EMS-ESP-Varianten können unterschiedliche Feldnamen und Strukturen verwenden; deshalb ist die Normalisierung in [dbus_emsesp/model.py](../dbus_emsesp/model.py) entscheidend.
- Fallback- und Simulationsbetrieb sind keine generische Bequemlichkeit, sondern eine gültige Betriebsstrategie für reale Anlagen.

## Typische Fallstricke

- Verwechslung von Gesamtleistung und Einzelgerätleistung
- Mangelhafte Trennung von `dhw` und `heating`
- Annahmen über EMS-ESP-Statusfelder ohne Mapping-Verifikation
- Dienststart ohne Prüfung der Konfiguration in [config/config.json](../config/config.json)

## Verweise

- [AGENT.md](../AGENT.md) §6 und §8
- [Projekt_context.md](../Projekt_context.md)
- [docs/architecture_decisions.md](architecture_decisions.md)
