# Rollout / Deployment

Stand: 2026-11-14
Pflege: bei jedem Release oder Betriebsvorfall, der das Deployment, das Systemstart-Verhalten oder die Installation betrifft.

## Ziel

Das Projekt ist als kleiner Python-Service für Venus OS gedacht, der die Daten eines EMS-ESP-Controllers als D-Bus-Teilgeräte bereitstellt.

## Verteilungswege

- Lokale Installation auf dem Zielgerät
- Ausführung mittels [service/run](../service/run)
- Konfiguration über [config/config.json](../config/config.json)

## Erststart

1. Repository auf dem Zielsystem bereitstellen.
2. Berechtigungen setzen: `chmod +x *.sh service/run`.
3. Installation starten: `sh install.sh`.
4. Konfiguration prüfen und ggf. `mode` und `base_url` anpassen.
5. Service neu starten und Endgeräte prüfen.

## Checkliste

- EMS-ESP erreichbar?
- `mode` korrekt gewählt?
- D-Bus-Services vorhanden?
- Drei Geräte erscheinen mit konsistenter Gesamtleistung?
- Keine unzulässige Doppelzählung in `heating`, `dhw`, `aux_heater`?

## Changelog

### Release 2026-11-14

- Initiale Dokumentation für Projektstruktur, Kontexte, ARchitekturentscheidungen und Betrieb eingeführt.
- Verteilungslogik und Betriebskontext in Dokumentation an die tatsächliche Codebasis angepasst.
- Test- und Prüfpfade auf die vorhandenen Projektdateien verwiesen.

## Verweise

- [README.md](../README.md)
- [AGENT.md](../AGENT.md)
- [Projekt_context.md](../Projekt_context.md)
- [docs/wiki/venuos-emsesp-anleitung.md](wiki/venuos-emsesp-anleitung.md)
