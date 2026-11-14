# ADR-001: Drei virtuelle Geräte mit sauberer Leistungstrennung

- Status: ACCEPTED
- Datum: 2026-11-14
- Pflege: vor Änderung der Verteilungslogik oder der D-Bus-Geräte-Semantik.

## Kontext

Das Projekt veröffentlicht drei separat adressierbare Geräte für eine Heizungsanlage: Heizung, Warmwasser und Zusatzheizer. Die EMS-ESP-Daten melden eine Gesamtleistung, aber keine intrinsische Trennung in drei semantisch saubere Gerätebereiche. Eine naive Verteilung würde entweder Verdoppelung oder Untererfassung erzeugen.

## Entscheidung

Die Logik in [dbus_emsesp/distributor.py](../../dbus_emsesp/distributor.py) verteilt die Gesamtleistung in drei Geräte gemäß dieser Regel:

- Warmwasser- oder Hotwater-Modi werden dem `dhw`-Gerät zugeordnet.
- Alle übrigen Verdichteranteile, inklusive Abtauen und unbekannter Zustände, werden dem `heating`-Gerät zugeordnet.
- Die Zusatzheizung (`aux_heater`) wird separat als eigener Anteil gemeldet, aber nur soweit sie aus der Gesamtleistung tatsächlich stammt.

## Konsequenzen

- Die Summe aus `heating` + `dhw` + `aux_heater` entspricht der gemeldeten Gesamtleistung.
- Die D-Bus-Semantik ist verständlich und stabil für Venus OS.
- Änderungen an der Zuordnungslogik müssen mit den Testfällen in [test_three_devices.py](../../test_three_devices.py) abgestimmt werden.
- Die Logik ist eng an die von EMS-ESP gemeldeten Betriebszustände gebunden und muss bei weiterem Laufzeitmodell geprüft werden.

## Verweise

- [docs/architecture_decisions.md](../architecture_decisions.md)
- [Projekt_context.md](../../Projekt_context.md)
- [dbus_emsesp/distributor.py](../../dbus_emsesp/distributor.py)
