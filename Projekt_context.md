# Projekt-Kontext

Stand: 2026-11-14
Projektstatus: Kernfunctionalität implementiert; Projekt umfasst REST-/Dummy-Integration, Drei-Geräte-Verteilung und D-Bus-Veröffentlichung. In diesem Initialisierungsschritt wurden keine automatischen Tests oder Lints ausgeführt; die Testdateien im Repository sind dokumentiert, aber nicht per Runner gestartet.

Verweis auf AGENT.md: [AGENT.md](AGENT.md) enthält die verbindlichen Arbeitsregeln und die nummerierten fachlichen/technischen Spezifikationen.
Verweis auf Projekt_Map.md: [Projekt_Map.md](Projekt_Map.md) gibt die Struktur-, Modul- und Einstiegspunkte-Navigation.
Verbindliche Architekturentscheidungen: [docs/architecture_decisions.md](docs/architecture_decisions.md)

Hinweis: Diese Datei enthält nur gesicherte Erkenntnisse aus dem Quellcode, der Konfiguration und der vorhandenen Projektdokumentation. Unbekanntes steht unter „Offene Punkte“.

## 1. Zweck des Projekts

Das Projekt verbindet eine EMS-ESP-Installation mit Venus OS, indem es Betriebsdaten als drei getrennte virtuelle `heatpump`-Dienste im D-Bus veröffentlicht. Ziel ist es, Standard-EMS-ESP-Messdaten so in die Victron-Welt zu übersetzen, dass eine Heizung, Warmwasser und Zusatzheizung separat und konsistent als Geräte erscheinen.

## 2. Wichtige Anwendungsfälle

- Meldung der Gesamtleistung und der Anteile für Heizung, Warmwasser und Zusatzheizung
- Betrieb mit realem EMS-ESP-Backend im `rest`-Modus
- Nutzung einer simulierten Datenquelle im `dummy`-Modus für Tests oder Ausfallzeiten
- Fallback von REST auf Dummy bei fehlender EMS-ESP-Verfügbarkeit (`rest_with_dummy_fallback`)
- Bereitstellung separater D-Bus-Geräte für die Oberfläche bzw. für Automations- und Monitoring-Szenarien

## 3. Verwendete Technologien, Frameworks und Sprachen

- Python 3
- DBus / `dbus.mainloop.glib`
- `gi.repository.GLib`
- EMS-ESP REST-API
- JSON-Konfiguration
- Venus OS / Victron D-Bus-Umgebung

## 4. Architektur und zentrale Komponenten

Die Architektur ist in [AGENT.md](AGENT.md) §4 definiert und wird im Projekt konkret durch die folgenden Module umgesetzt:

- [dbus_emsesp/main.py](dbus_emsesp/main.py): Orchestrierung, Initialisierung, Polling, Service-Start
- [dbus_emsesp/model.py](dbus_emsesp/model.py): Normalisierung und Mapping von EMS-ESP-Daten in ein einheitliches Zustandsmodell
- [dbus_emsesp/distributor.py](dbus_emsesp/distributor.py): Leistungsverteilung ohne Doppelzählung
- [dbus_emsesp/meter_service.py](dbus_emsesp/meter_service.py): DBus-/Geräte-Veröffentlichung
- [dbus_emsesp/source.py](dbus_emsesp/source.py): Auswahl von REST vs. Dummy mit Fallback
- [dbus_emsesp/energy.py](dbus_emsesp/energy.py): Zähler- und Ressourcenmanagement

Zentrale Idee: Ein EMS-ESP-Status wird zunächst normalisiert, dann logisch auf die drei virtuellen Geräte aufgeteilt und anschließend als D-Bus-Services publiziert.

## 5. Datenmodell und Datenfluss

1. EMS-ESP liefert Rohdaten, typischerweise aus REST-Endpunkten wie `/api/boiler`, `/api/thermostat`, `/api/heatpump`, `/api/system`.
2. Diese Rohdaten werden durch `flatten()` und `first()` aus [dbus_emsesp/model.py](dbus_emsesp/model.py) normalisiert.
3. `EmsEspModelMapper.map()` baut ein `HeatPumpState` auf, das Energie-, Betriebs-, Temperatur- und Laufzeitwerte kapselt.
4. `PowerDistributor.distribute()` übernimmt die Zuordnung der Gesamtleistung auf `heating`, `dhw` und `aux_heater`, so dass die Summe der gemeldeten Einzelwerte zur Gesamtleistung passt.
5. `Application._publish()` überträgt die Werte in die jeweiligen D-Bus-Geräte und aktualisiert die Laufzeit-/Energie-Attribute.

## 6. Externe Systeme, APIs und Bibliotheken

- EMS-ESP HTTP-API
- Venus OS / Victron D-Bus
- `dbus.mainloop.glib`
- `GLib`-Loop
- `config/config.json` des Projekts als zentrale Konfiguration

## 7. Entwicklungs-, Build-, Test- und Startbefehle

- Installieren: `sh install.sh`
- Setup: `sh setup.sh`
- Deinstallation: `sh uninstall.sh`
- Test: `python3 test_three_devices.py`
- Test: `python3 test_model.py`
- Test: `python3 test_dummy.py`
- Service-Start via [service/run](service/run)

## 8. Benennungs-, Formatierungs- und Codekonventionen

- Python-Code in einem überschaubaren, modulären Stil mit klaren Klassen- und Funktionsnamen
- Konfigurationsdateien in JSON
- In der Codebasis werden deutsche Beschreibungen und fachliche Begriffe verwendet, insbesondere im Bereich der Heizungslogik und Zuordnung
- Projektweite Standards und fachliche Regeln sind in [AGENT.md](AGENT.md) verbindlich festgelegt

## 9. Wichtige fachliche Regeln (Kurzfassung)

- Das System modelliert drei virtuelle Geräte mit separaten D-Bus-Services.
- Warmwasser wird vom Heizungsteil getrennt; nicht-Warmwasseranteile landen bei Heizung.
- Die Summe aus `heating` + `dhw` + `aux_heater` muss der Gesamtleistung entsprechen.
- Betrieb ist als `dummy`, `rest` oder `rest_with_dummy_fallback` konfigurierbar.
- Für fachliche und technische Spezialregeln siehe [AGENT.md](AGENT.md) §§1–9.

## 10. Architektur- und Designentscheidungen (ADR)

| ADR | Entscheidung | Begründung | Status |
|---|---|---|---|
| ADR-001 | Drei virtuelle Geräte mit sauberer Leistungstrennung | Verhindert Doppelzählung und bildet Victron-Heatpump-Daten ab | ACCEPTED |
| ADR-002 | REST-Hauptpfad mit Dummy-Fallback | Betrieb resilienter bei EMS-ESP-Ausfall, nützlich für Tests und Übergang | ACCEPTED |

Vollständige Begründung und Volltext: [docs/architecture_decisions.md](docs/architecture_decisions.md)

## 11. Bekannte Einschränkungen

- Das Projekt ist bewusst auf eine konkrete Integration mit EMS-ESP und Venus OS ausgerichtet; es ist kein allgemeines Framework.
- Die Laufzeit hängt von der Struktur der EMS-ESP-REST-API und den Geräte-Mappings ab.
- Es gibt keine sichtbare Datenbank- oder Migrationsschicht im aktuell vorhandenen Projektbestand.

## 12. Bekannte Risiken und technische Schulden

- Abhängigkeit von EMS-ESP-Feldnamen und Ausprägungen je Heizungsmodell; Mappings müssen modellabhängig weiter validiert werden.
- Fallback- und Simulationsbetrieb müssen gegen reale EMS-ESP-Instanzen validiert werden.
- Die reale Verteilung von Betriebszuständen in unbekannten oder komplexen Heizungszuständen muss in der Zielumgebung verifiziert werden.

## 13. Offene Punkte

- `TODO(domain-review): Prüfung der vollständigen EMS-ESP-API-Varianten für alle begrenzten Bosch-/EMS-ESP-Modelle, die das Projekt in der Praxis ansprechen könnte.`
- `TODO(domain-review): Festlegen, ob Mappings für weitere Geräte-/Betriebsmodi explizit ergänzt werden sollen.`
- `TODO(domain-review): Verifikation der stillen Annahmen zu Betriebszuständen wie `defrost`, `cooling`, `standby` in realen Anlagen.`
- `TODO(domain-review): Release-/Versionierungsstrategie für ausgelieferte Umgebungen einschließlich Git-Tags und Produktiv-Checks.`

## 14. Verweis auf zentrale Dokumente

- [AGENT.md](AGENT.md)
- [Projekt_Map.md](Projekt_Map.md)
- [docs/domain_glossary.md](docs/domain_glossary.md)
- [docs/architecture_decisions.md](docs/architecture_decisions.md)
- [README.md](README.md)
