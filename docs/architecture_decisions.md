# Architekturentscheidungen (ADR-Index)

Stand: 2026-11-14
Pflege: vor Umsetzung jeder grundlegenden Architektur- oder Designentscheidung; neue ADRs vor Code-Änderungen.

## ADR-Übersicht

| ADR | Titel | Status | Referenz |
|---|---|---|---|
| ADR-001 | Drei virtuelle Geräte mit sauberer Leistungstrennung | ACCEPTED | [architecture_decisions/ADR-001-three-device-distribution.md](architecture_decisions/ADR-001-three-device-distribution.md) |
| ADR-002 | REST-Hauptpfad mit Dummy-Fallback | ACCEPTED | [architecture_decisions/ADR-002-rest-with-dummy-fallback.md](architecture_decisions/ADR-002-rest-with-dummy-fallback.md) |

## Regel

Eine neue Architekturentscheidung ersetzt eine bestehende nur dann, wenn der Status der älteren auf `SUPERSEDED` gesetzt wird und beide Dokumente den Austausch eindeutig nachvollziehbar machen.

## Verweise

- [AGENT.md](../AGENT.md) §7 und §9
- [Projekt_context.md](../Projekt_context.md)
- [dbus_emsesp/distributor.py](../dbus_emsesp/distributor.py)
- [dbus_emsesp/source.py](../dbus_emsesp/source.py)
