# ADR-002: REST-Hauptpfad mit Dummy-Fallback

- Status: ACCEPTED
- Datum: 2026-11-14
- Pflege: vor Änderung des Ausfallverhaltens oder der Betriebsmodi.

## Kontext

Das Projekt muss mit realen EMS-ESP-Instanzen arbeiten, aber auch in Tests, Simulationen und Ausfallphasen lauffähig bleiben. Ein reiner REST-Modus wäre empfindlich gegenüber Netz-/Serviceproblemen; ein reiner Dummy-Modus wäre für reale Anlagen nicht ausreichend.

## Entscheidung

Die Laufzeit verwendet standardmäßig `rest_with_dummy_fallback` als robustes Betriebsmodell:

- Hauptpfad: EMS-ESP REST-Daten
- Fallback: Dummy-Daten, falls die REST-Datenquelle ausfällt oder nicht verlässlich arbeitet
- Weitere Entscheidung: der Fallback kann je nach Simulationseinstellung des Systems aktiv oder deaktiviert werden

Die Entscheidung ist in [dbus_emsesp/source.py](../../dbus_emsesp/source.py) und [dbus_emsesp/main.py](../../dbus_emsesp/main.py) umgesetzt.

## Konsequenzen

- Das System bleibt im Betrieb, auch wenn EMS-ESP kurzzeitig ausfällt.
- Test- und Entwicklungsumgebungen benötigen nicht zwingend eine echte Anlage.
- Die Semantik der Dummy-Daten muss sauber von echten Daten getrennt bleiben, damit keine falschen Zustände als reale Anlage interpretiert werden.
- Fallback- und Simulationseinstellungen müssen mit [config/config.json](../../config/config.json) dokumentiert werden.

## Verweise

- [docs/architecture_decisions.md](../architecture_decisions.md)
- [Projekt_context.md](../../Projekt_context.md)
- [dbus_emsesp/source.py](../../dbus_emsesp/source.py)
- [config/config.json](../../config/config.json)
