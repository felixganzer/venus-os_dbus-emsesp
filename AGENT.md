# AGENT.md

Stand: 2026-11-14

## §0 Verbindliche Arbeitsregeln

1. Bei jeder neuen Aufgabe ist zuerst diese Datei zu lesen, danach [Projekt_Map.md](Projekt_Map.md). [Projekt_context.md](Projekt_context.md) ist nur dann vollständig zu lesen, wenn fachlicher, technischer oder architektonischer Kontext für die konkrete Aufgabe erforderlich ist.
2. Das gesamte Projekt darf nicht automatisch analysiert werden. Die erste Untersuchung ist auf die in [Projekt_Map.md](Projekt_Map.md) als relevant ausgewiesenen Dateien und Module zu begrenzen.
3. Anschließend sind nur direkte Abhängigkeiten, Schnittstellen, Tests und Konfigurationen zu prüfen, die für die Umsetzung benötigt werden. Der Analysebereich ist nur zu erweitern, wenn die vorhandenen Informationen keine verlässliche Umsetzung erlauben.
4. Unbegründete Refactorings außerhalb des geforderten Aufgabenbereichs sind nicht zulässig.
5. Bestehendes Verhalten darf nur verändert werden, wenn dies ausdrücklich verlangt wird oder zur Fehlerbehebung zwingend erforderlich ist.
6. Architektur, Benennung, Formatierung und Projektkonventionen sind einzuhalten. Vor jeder Änderung ist zu prüfen, welche Dateien betroffen sind.
7. Nach der Umsetzung ist kurz zusammenzufassen, welche Dateien geändert wurden und warum.
8. Nach jeder Codeänderung sind die relevanten Tests und der Linter des Projekts auszuführen. Abweichungen sind transparent zu machen; wenn kein Test-/Lint-Setup für den aktuellen Schritt definiert ist, ist dies im Abschluss ausdrücklich zu nennen.
9. Jede grundlegende Architektur- oder Designentscheidung ist vor der Umsetzung als ADR zu dokumentieren; siehe Abschnitt 4.2 in [docs/architecture_decisions.md](docs/architecture_decisions.md).
10. [Projekt_Map.md](Projekt_Map.md) ist zu aktualisieren, wenn Dateien, Verzeichnisse, Module, Abhängigkeiten, Einstiegspunkte oder Zuständigkeiten geändert werden.
11. [Projekt_context.md](Projekt_context.md) ist zu aktualisieren, wenn sich Architektur, Datenmodell, Schnittstellen, Technologien, Konventionen, fachliche Regeln oder wichtige Entscheidungen ändern.
12. Die Endnutzer-Anleitung und das Rollout-Changelog sind bei jedem abgeschlossenen Feature zu aktualisieren, das Bediener oder Betrieb betrifft; siehe Pflege-Matrix in §7.
13. Fachliche Annahmen und Regeln der Spezifikation (§1–n) dürfen nicht stillschweigend geändert werden. Änderungen sind explizit im Abschnitt anzupassen und als ADR zu dokumentieren.
14. Temporäre Vermutungen sind nicht als gesicherte Tatsachen zu dokumentieren.
15. Unsicherheiten und offene fachliche Punkte sind eindeutig als `TODO(domain-review)` zu kennzeichnen; keine geratenen fachlichen Werte dürfen als Tatsachen aufgenommen werden.
16. Passwörter, API-Schlüssel, Tokens oder andere Geheimnisse sind in Dokumentationsdateien niemals zu speichern.
17. Projektbezogene Zusatzeinträge aus der bestehenden Codebasis und den Konfigurationsdateien sind zu berücksichtigen; keine generischen Annahmen aus fremden Projekten sollen den Projektkontext ersetzen.
18. Bei Python-Projekten gilt die im Projekt vorgefundene Konvention: UTF-8, verständliche englische oder deutsche Bezeichner je nach vorhandener Codebasis, keine künstlichen Platzhalter wie `PRODUCT_PLACEHOLDER`, sofern keine gültige konkrete Projektbezeichnung vorliegt.

### Projektbezogene Zusatregeln

- Historische oder produktionsrelevante Datenquellen dürfen nicht ohne begründete Notwendigkeit verändert werden.
- Die Logik für die Verteilung der Gesamtleistung auf die virtuellen Geräte bleibt in der Architektur von [dbus_emsesp/distributor.py](dbus_emsesp/distributor.py) und den zugehörigen Modellen verankert; Änderungen dort sind nur im Rahmen der gewünschten Ursache und mit dokumentierter Begründung zulässig.
- Die Konfiguration liegt in [config/config.json](config/config.json); Änderungen an Konfigurationsschlüsseln sind mit der dokumentierten Wirkung in der Projektdokumentation abzugleichen.
- Bei der Analyse ist die Trennung zwischen Service- und Datenlogik zu respektieren: DBus- und Venus-OS-spezifische Schichten bleiben von der EMS-ESP- und Modellabstraktion getrennt.
- Encoding-Regel: alle Dateien im Projekt sind UTF-8; AGENT.md verwendet ebenfalls UTF-8, weil das Projekt keine ASCII-Umschrift-Konvention zeigt.

## §1 Rolle des Agenten und technischer Rahmen

1. Der Agent arbeitet im Rahmen eines Python-Services, der EMS-ESP-Daten liest und sie als drei virtuelle Victron/ Venus OS `heatpump`-Dienste im D-Bus veröffentlicht. 
2. Technischer Rahmen:
   - Sprache: Python 3
   - Kernmodule: `dbus`, `GLib`, `gi.repository`
   - Konfigurationsformat: JSON in [config/config.json](config/config.json)
   - Hauptprogramm: [dbus_emsesp/main.py](dbus_emsesp/main.py)
   - Service-Launcher: [service/run](service/run)
3. Der Projektumfang ist bewusst auf ein Betriebssystem-/Dienst-Integrationstool für EMS-ESP und Venus OS begrenzt. Es werden keine GUI-Anwendungen, Web-APIs oder Frontends im herkömmlichen Sinne gebaut.
4. Das Projekt ist kein allgemeines EMS-ESP-Client-Framework. Es ist eine speziell auf Victron Venus OS zugeschnittene DBus-Abbildung mit Simulations- und Fallback-Verhalten.
5. Die aus dem Code abgeleiteten Kernbereiche sind:
   - Datenbeschaffung aus EMS-ESP (REST oder Dummy)
   - Normalisierung und Zuordnung in [dbus_emsesp/model.py](dbus_emsesp/model.py)
   - Verteilung der Gesamtleistung auf Heizungs-, Warmwasser- und Heizstab-Geräte in [dbus_emsesp/distributor.py](dbus_emsesp/distributor.py)
   - Veröffentlichung über DBus-Dienste in [dbus_emsesp/meter_service.py](dbus_emsesp/meter_service.py)
   - Orchestrierung der Laufzeit in [dbus_emsesp/main.py](dbus_emsesp/main.py)

## §2 Fachlicher Kontext und Domänenmodell

1. Das Projekt modelliert eine Heizungsanlage als drei virtuelle Geräte, die jeweils unterschiedliche Leistungs- und Energieanteile repräsentieren:
   - `heating`: Verdichter-/Heizungsanteil ohne Warmwasser
   - `dhw`: Warmwasseranteil
   - `aux_heater`: elektrische Zusatzheizung
2. Die Gesamtleistung wird nach Regeln aufgeteilt, damit die Summe der drei virtuellen Geräte der vom EMS-ESP gemeldeten Gesamtleistung entspricht.
3. Warmwasser wird explizit vom Heizungsanteil getrennt. Alle übrigen Verdichteranteile, einschließlich Abtauen und unbekannter Zustände, werden der Heizung zugeordnet.
4. Der Betrieb unterscheidet sich nach Betriebsart:
   - `dummy`: Simulationsmodus mit künstlich erzeugten EMS-ESP-Daten
   - `rest`: Direktes Lesen aus EMS-ESP per REST
   - `rest_with_dummy_fallback`: REST-Hauptpfad mit Dummy-Fallback bei Ausfall
5. Die Systemlogik arbeitet mit einem zentralen Modell (`HeatPumpState`), das Normalisierung, Energiewerte, Betriebszustände und Laufzeiten kapselt.
6. `HeatPumpState` bildet viele EMS-ESP-Felder in ein einheitliches internes Modell ab, damit die anschließende Verteilungs- und DBus-Logik nicht von variierenden API-Strukturen abhängt.

## §3 Datenmodell und Konfiguration

1. Die Konfiguration wird zentral in [config/config.json](config/config.json) gepflegt. Ihre Struktur enthält:
   - Betriebsmodus (`mode`)
   - EMS-ESP-REST-Parameter (`ems_esp`)
   - Fallback-Einstellungen (`fallback`)
   - Dummy-/Simulationskonfiguration (`dummy`)
   - Geräte-Spezifikationen (`devices`)
   - Mapping-Definitionen (`emsesp_mapping`)
   - Telemetrie- und Generic-Input-Defaults
   - Zähler- und State-File-Konfiguration (`counters`)
2. Die Datenquelle wird durch Pfad-/Adressattribute und `minimum_successful_endpoints` modelliert. Ein Binding an ein konkretes EMS-ESP-Backend ist für die Laufzeit ausdrücklich konfigurierbar.
3. Die Projektlogik verwendet vordefinierte `DeviceInstance`-Werte für drei virtuelle Geräte:
   - 280 = Heizung
   - 281 = Warmwasser
   - 282 = Heizstab
4. Die Energie-/Leistungslogik ist als Zustandsmodell dokumentiert; keine Datenbank ist im aktuellen Projektumfang vorgesehen.
5. Keine Abhängigkeit von einer relationalen Datenbank oder einer Migrationsschicht ist im derzeitigen Quellbestand sichtbar.

## §4 Architektur

1. Die Laufzeit bildet ein `Application`-Objekt in [dbus_emsesp/main.py](dbus_emsesp/main.py). Dieses hält:
   - Konfiguration
   - Mapper für EMS-ESP-Daten
   - Dummy- und REST-Clients
   - PowerDistributor
   - EnergyTracker
   - DBus-Service-Instanzen je Kategorie
2. Die Module sind klar abgegrenzt:
   - `source.py`: Auswahl und Fallback zwischen EMS-ESP-REST und Dummy
   - `dummy.py`: Simulationsdaten und Szenario-Logik
   - `emsesp.py`: Zugriffe auf EMS-ESP
   - `model.py`: Normalisierung, `HeatPumpState`, Mapping
   - `distributor.py`: Leistungssplitting
   - `meter_service.py`: DBus- und Venus-OS-Attributveröffentlichung
   - `energy.py`: Zähler-/Energieverwaltung
3. Die Service-Ausgabe erfolgt pro Gerät über die Victron-HEATPUMP-Interfaces. Jede virtuell bereitgestellte Einheit hat eigene Konfigurationsparameter und kann als eigener D-Bus-Service adressiert werden.

## §5 Schnittstellen und Einstiegspunkte

1. Hauptstartpunkt: [dbus_emsesp/main.py](dbus_emsesp/main.py)
2. Service-Launcher: [service/run](service/run)
3. Installationsskripte: [install.sh](install.sh), [setup.sh](setup.sh), [uninstall.sh](uninstall.sh)
4. Externe Schnittstelle: EMS-ESP REST-API über `base_url` + Endpoint-Pfade aus [config/config.json](config/config.json)
5. Interne Schnittstellen:
   - `Application._read_state()`
   - `Application._distribution()`
   - `Application._publish()`
   - `PowerDistributor.distribute()`
   - `HeatPumpState.as_dict()`
6. Die Projekt-API ist keine öffentliche Bibliothek im Paket-Sinn; sie ist primär eine Laufzeitintegration für Venus OS und EMS-ESP.

## §6 Qualitäts- und Testregeln

1. Relevante Testdateien im Repository:
   - [test_dummy.py](test_dummy.py)
   - [test_model.py](test_model.py)
   - [test_three_devices.py](test_three_devices.py)
2. Die Tests sind auf die Logik der Verteilungs- und Modellierungsschicht fokussiert; sie sind der erste Prüfpfad nach jeder Änderung an Power-Distribution, Modellschema oder Mapping-Regeln.
3. Vor einer Änderung ist zu prüfen, ob die betroffene Logik in den Tests adressiert ist. Wenn nicht, ist eine gezielte Reproduktion bzw. ein enger Testfall nach der Arbeitsweise des Projekts zu ergänzen.
4. Ein Lint-Setup ist in diesem Repository nicht als etablierte Konfiguration erkennbar; wenn keine Konfiguration vorliegt, ist die Lint-Prüfung explizit als nicht sinnvoll bzw. nicht durchzuführen zu melden.

## §7 Dokumentations- und Pflegepflichten

1. Regeln und fachliche Spezifikation werden nur hier definiert. Alle anderen Dokumente verweisen auf die betreffenenden Abschnitte statt doppelte Inhalte zu duplizieren.
2. Dokumentation ist in den folgenden Bereichen zu pflegen:
   - [Projekt_Map.md](Projekt_Map.md): Struktur, Zonen und relevante Einstiegspunkte
   - [Projekt_context.md](Projekt_context.md): stabiler fachlicher und technischer Kontext
   - [docs/domain_glossary.md](docs/domain_glossary.md): Fachbegriffe
   - [docs/architecture_decisions.md](docs/architecture_decisions.md): ADR-Index
   - [docs/wiki](docs/wiki): Endnutzer-Anleitung
   - [docs/rollout_exe.md](docs/rollout_exe.md): Betrieb und Release
3. Pflege-Matrix:

| Ereignis | Zu aktualisieren |
|---|---|
| Dateien, Verzeichnisse, Module, Abhängigkeiten, Einstiegspunkte geändert | [Projekt_Map.md](Projekt_Map.md) |
| Architektur, Datenmodell, Schnittstellen, Technologien, fachliche Regeln geändert | [Projekt_context.md](Projekt_context.md), falls erforderlich [AGENT.md](AGENT.md) |
| Grundlegende Architektur-/Designentscheidung | Neue ADR vor Umsetzung |
| Bedienablauf/Oberfläche geändert | [docs/wiki](docs/wiki) |
| Feature-Release (betrifft Bediener oder Betrieb) | [docs/wiki](docs/wiki), [docs/rollout_exe.md](docs/rollout_exe.md) |
| Neuer Fachbegriff | [docs/domain_glossary.md](docs/domain_glossary.md) |
| Nichttrivialer Fehler behoben | [docs/lessons_learned.md](docs/lessons_learned.md), sofern angelegt |

4. Versionsmanagement: das Projekt hat bereits eine Laufzeitversion in [dbus_emsesp/main.py](dbus_emsesp/main.py) (`VERSION = "1.0.0"`). Bei Release-Änderungen ist diese Version mit der jeweiligen Distribution und dem Betriebskontext konsistent zu halten.
5. Encoding-Konvention: UTF-8. Es gibt derzeit keine Projektregel für ASCII-Umschrift; daher ist keine Abweichung anzulegen.

## §8 Offene Punkte und TODO(domain-review)

- `TODO(domain-review): Verifizierung der vollständigen EMS-ESP-API-Varianten für alle Bosch-/EMS-ESP-Modelle, die dieses Projekt betreffen.`
- `TODO(domain-review): Prüfung, ob die Vorgaben für zusätzliche Gerätetypen oder Heizungs-Modelle in den Mappings erweitert werden müssen.`
- `TODO(domain-review): Abgleich der in [config/config.json](config/config.json) definierten Betriebszustände mit allen realen EMS-ESP-Statuswerten der Zielumgebung.`
- `TODO(domain-review): Festlegung, welche Release-/Versionierungsstrategie für Produktivumgebungen und Git-Tags verbindlich gelten soll, wenn das Projekt ausgeliefert wird.`

## §9 Zusammenfassung der verbindlichen Regeln

- Die Spezifikation und Regeln live im Projekt zu pflegen und nur in dieser Datei zu definieren.
- Die übrige Dokumentation ist nach dem Verweisprinzip zu führen.
- Fachliche Entscheidungen sind vor Umsetzung als ADR zu dokumentieren.
- Der in [dbus_emsesp/main.py](dbus_emsesp/main.py) sichtbare Betriebskontext und das Mapping in [config/config.json](config/config.json) sind der maßgebliche Bezugspunkt für Implementierung und Dokumentation.
