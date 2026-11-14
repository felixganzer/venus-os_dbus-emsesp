# Projekt-Map

Stand: 2026-11-14
Projektstatus: Lern-/Initialisierungsstand; Kernservice implementiert, Konfiguration vorhanden, Testbasis für Modell-/Verteilungslauf vorhanden. Automatisierte Qualitätsprüfung wurde in diesem Initialisierungsschritt nicht ausgeführt, da nur Projekt-Dokumentation angelegt wurde.

Verbindliche Lesereihenfolge bei neuen Aufgaben:
1. [AGENT.md](AGENT.md)
2. [Projekt_Map.md](Projekt_Map.md)
3. [Projekt_context.md](Projekt_context.md) nur bei fachlichem, technischem oder architektonischem Kontextbedarf

Verbindliche Architekturentscheidungen (ADR): [docs/architecture_decisions.md](docs/architecture_decisions.md)

## 1. Projektstruktur (Ist-Überblick)

```text
venus-os_dbus-emsesp/
├── AGENT.md                          # verbindliches Regelwerk und Spezifikation (§0–§9)
├── Projekt_Map.md                   # Navigationskarte und Zuständigkeitsüberblick
├── Projekt_context.md               # stabiler fachlicher und technischer Kontext
├── README.md                        # Betriebshandbuch, Installations- und Prüfhinweise
├── config/
│   └── config.json                  # zentrale Laufzeit- und Mapping-Konfiguration
├── dbus_emsesp/
│   ├── main.py                      # Einstiegspunkt, App-Setup, Polling, D-Bus-Start
│   ├── distributor.py               # Leistung auf drei Geräte verteilt
│   ├── dummy.py                     # Dummy-EMS-ESP-Datenquelle
│   ├── emsesp.py                    # EMS-ESP-REST-Client
│   ├── energy.py                    # Zähler-/Energieverwaltung
│   ├── meter_service.py             # D-Bus-Services und Attribute
│   ├── model.py                     # EMS-ESP-Datennormalisierung, HeatPumpState
│   └── source.py                    # REST + Dummy-Fallback-Logik
├── service/
│   └── run                          # Service-Launcher für Venus OS / Systemdienst
├── install.sh                       # Installationsskript
├── setup.sh                         # Setup-Skript
├── uninstall.sh                     # Deinstallationsskript
├── uninstall.py                     # Python-Teil der Deinstallation
├── dummydata.py                     # Dummy-Daten-Ausgabe / Testdatenquelle
├── test_dummy.py                    # Test für Dummy-Daten
├── test_model.py                    # Test für Modell- und Mapping-Logik
├── test_three_devices.py            # Verifiziert Summe der drei Geräte = Gesamtleistung
├── docs/
│   ├── architecture_decisions.md    # ADR-Index
│   ├── domain_glossary.md           # Fachbegriffe
│   ├── wiki/                        # Betriebs- und Endnutzer-Anleitung
│   ├── rollout_exe.md                # Release-/Rollout-Dokumentation
│   └── architecture_decisions/      # ADR-Dateien
└── .gitignore                       # Git-Ignore-Konfiguration
```

## 2. Bereiche und Zuständigkeiten

| Pfad oder Bereich | Zweck | Wichtige Abhängigkeiten | Relevant bei |
|---|---|---|---|
| [dbus_emsesp/main.py](dbus_emsesp/main.py) | Einstiegspunkt, Laufzeit, Polling, D-Bus-Start | `distributor`, `dummy`, `emsesp`, `energy`, `meter_service`, `model`, `source` | Start, Service- und Laufzeitfehler |
| [config/config.json](config/config.json) | Zentrale Konfiguration | alle Laufzeitmodule | Betriebsdaten, Mappings, Geräte-IDs |
| [dbus_emsesp/model.py](dbus_emsesp/model.py) | Normalisierung EMS-ESP → HeatPumpState | `dummy.py`, `emsesp.py`, `distributor.py` | Datenmapping, Zustände, energetische Felder |
| [dbus_emsesp/distributor.py](dbus_emsesp/distributor.py) | Verteilung Gesamtleistung auf 3 Geräte | `model.py` | Zuordnungslogik, Leistungssplit |
| [dbus_emsesp/meter_service.py](dbus_emsesp/meter_service.py) | D-Bus- und Venus OS-Service-API | `main.py`, `energy.py` | Attribut- und Serviceveröffentlichung |
| [dbus_emsesp/source.py](dbus_emsesp/source.py) | Fallback Übergang zwischen REST und Dummy | `dummy.py`, `emsesp.py`, `model.py` | Ausfallverhalten |
| [dbus_emsesp/energy.py](dbus_emsesp/energy.py) | Energie-/Zählerstatus | `main.py` | Laufzeit-/Zählerbetrieb |
| [dbus_emsesp/dummy.py](dbus_emsesp/dummy.py) | Simulationsdaten | `model.py` | Test- und Fallback-Szenarien |
| [dbus_emsesp/emsesp.py](dbus_emsesp/emsesp.py) | EMS-ESP-REST-Client | `source.py`, `main.py` | Echtzeitdaten |
| [service/run](service/run) | Systemdienst-Start | [dbus_emsesp/main.py](dbus_emsesp/main.py) | Service-Deployment |
| [README.md](README.md) | Installations- und Betriebs-Quickstart | Konfiguration und Testskripte | Erststart, Prüfung |
| [test_three_devices.py](test_three_devices.py) | Verifikation: Artikel-/Summe der drei Geräte | `distributor.py`, `dummy.py` | Zuordnungslogik |
| [test_model.py](test_model.py) | Model- und Mapping-Checks | `model.py` | Feldnormalisierung |

## 3. Zentrale Einstiegspunkte

- [dbus_emsesp/main.py](dbus_emsesp/main.py): Hauptprogramm, `main()` startet `Application.load_config()` und `Application.run()`.
- [service/run](service/run): Startpfad für den Venus-OS-/systemd-ähnlichen Prozess.
- [install.sh](install.sh): Installation des Projekts unter dem erwarteten Zielpfad.
- [README.md](README.md): Nutzer- und Administratoren-Quickstart.

## 4. Wichtige Konfigurationsdateien

| Datei | Bedeutung |
|---|---|
| [config/config.json](config/config.json) | Zentrale Laufzeitkonfiguration mit Modus, EMS-ESP-Host, Mappings, Geräte- und Dummy-Einstellungen |
| [service/run](service/run) | Umgebungsvariablen für `EMS_ESP_CONFIG` und `LOG_LEVEL` |
| [.gitignore](.gitignore) | git-ignorierte lokale Artefakte |

## 5. Relevante Datenmodelle und -quellen

- EMS-ESP-REST-Datenquelle: `base_url` + Endpoints aus [config/config.json](config/config.json)
- D-Bus-Geräte:
  - `com.victronenergy.heatpump.emsesp_heating` (DeviceInstance 280)
  - `com.victronenergy.heatpump.emsesp_dhw` (DeviceInstance 281)
  - `com.victronenergy.heatpump.emsesp_aux` (DeviceInstance 282)
- In interne Zustände übersetzt durch `HeatPumpState` in [dbus_emsesp/model.py](dbus_emsesp/model.py)
- Externe Datensätze / Importstatus: kein eigener Import-Analyzer oder Import-Pipeline im Projektbestand; keine Datenbanktabellen oder Migrationsdateien sichtbar

## 6. Externe und interne Schnittstellen

- Extern: EMS-ESP HTTP-API (REST)
- Extern: Victron/Venus OS D-Bus-Services
- Intern: `Application` orchestrates `PowerDistributor`, `DummyEmsEspClient`, `EmsEspClient`, `HeatPumpState` und `HeatPumpMeterService`
- Schnittstellen sind in [AGENT.md](AGENT.md) §5 und [Projekt_context.md](Projekt_context.md) beschrieben.

## 7. Tests und deren Zuordnung

| Test | Fokus |
|---|---|
| [test_three_devices.py](test_three_devices.py) | Verifiziert die Summe aus Heizungs-/DHW-/Zusatzheizer-Leistung gegen Gesamtleistung |
| [test_model.py](test_model.py) | Mapping/Normalisierung/Modellregeln |
| [test_dummy.py](test_dummy.py) | Dummy-Daten und Simulationsfall |

## 8. Wichtige Abhängigkeiten zwischen Modulen

```text
main.py
  ├─> config/config.json
  ├─> source.py
  │    ├─> emsesp.py
  │    ├─> dummy.py
  │    └─> model.py
  ├─> distributor.py
  ├─> energy.py
  └─> meter_service.py
```

## 9. Aufgabenorientierte Zuordnung

| Für Aufgabe | Zuerst prüfen |
|---|---|
| Änderung an Gesamtleistungs-Zuordnung | [dbus_emsesp/distributor.py](dbus_emsesp/distributor.py), [test_three_devices.py](test_three_devices.py), [config/config.json](config/config.json) |
| Änderung am EMS-ESP-Mapping | [dbus_emsesp/model.py](dbus_emsesp/model.py), [config/config.json](config/config.json), [test_model.py](test_model.py) |
| Änderung am Datenfluss / Fallback | [dbus_emsesp/source.py](dbus_emsesp/source.py), [dbus_emsesp/emsesp.py](dbus_emsesp/emsesp.py), [dbus_emsesp/dummy.py](dbus_emsesp/dummy.py) |
| Änderung am Service-Start / D-Bus-Veröffentlichung | [dbus_emsesp/main.py](dbus_emsesp/main.py), [dbus_emsesp/meter_service.py](dbus_emsesp/meter_service.py), [service/run](service/run) |
| Installation / Betrieb | [README.md](README.md), [install.sh](install.sh), [setup.sh](setup.sh), [uninstall.sh](uninstall.sh) |

## 10. Build-, Test- und Startbefehle

| Zweck | Befehl |
|---|---|
| Projekt prüfen | `python3 test_three_devices.py` |
| Modell prüfen | `python3 test_model.py` |
| Dummy prüfen | `python3 test_dummy.py` |
| Dienst starten | `sh install.sh` oder Service-Launcher in [service/run](service/run) |
| DBus-Services prüfen | `dbus -y com.victronenergy.heatpump.emsesp_heating` usw. |

## 11. Bewusst ignorierte Bereiche

- `.git`, `.github`, `.idea`, `.vscode` wurde bei der Initialisierung nicht als projektrelevant betrachtet, sofern hier keine produktiven Projektsettings liegen.
- Generierte Artefakte, Build-Ausgaben, Cache-Verzeichnisse und temporäre Dateien wurden bewusst ignoriert.
- Es gibt keine im Projekt sichtbare Datenbank-, Migration- oder Import-Pipeline; diese Bereiche wurden nicht als relevant für die Kernlogik angenommen.
- Keine externen Node-/JavaScript-/Build-Tools wurden im Repository identifiziert, daher blieb die Analyse auf Python- und Systemservice-Pfade fokussiert.

## 12. Kurzfazit

Das Projekt ist eine kleine, klar abgegrenzte Python-Integration zwischen EMS-ESP und Venus OS, mit einem zentralen Mapping-/Aggregationsmodell, einer Drei-Geräte-Verteilung und einem `rest_with_dummy_fallback`-Betriebsmodell.
