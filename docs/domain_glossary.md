# Fachglossar

Stand: 2026-11-14
Pflege: bei jedem neuen Fachbegriff oder bei fachlicher Klarstellung.

## Glossar

| Begriff | Bedeutung | Abgrenzung |
|---|---|---|
| EMS-ESP | Web-basierte Schnittstelle für die Kommunikation mit einer Heizungsanlage, hier als Datenquelle für das Projekt verwendet. | Nicht zu verwechseln mit dem D-Bus-Service im Venus OS. |
| Heatpump-State | Internes, normalisiertes Zustandsmodell der Heizungsanlage, erzeugt aus EMS-ESP-Rohdaten. | Repräsentiert die Logik des Projekts; kein Roh-JSON aus EMS-ESP. |
| D-Bus-Service | Victron/Venus OS-Service, der als Gerät im System sichtbar gemacht wird. | Das Projekt publiziert keine Web-API, sondern D-Bus-Objekte. |
| DeviceInstance | Eindeutige numerische ID für ein virtuelles Gerät im Venus OS-Adressraum. | Unterschiedlich von `service_name`, aber logisch zugeordnet. |
| Dummy-Fallback | Simulierte EMS-ESP-Daten als Ersatz, wenn REST-Daten ausfallen. | Nicht identisch mit dem normalen `dummy`-Betrieb, sondern ein Ausfallmodus. |
| `rest_with_dummy_fallback` | Kombination aus Echtzeit-REST-Betrieb und automatischer Ausweichlogik zu Dummy-Daten. | Führt eine direktere Betriebslogik aus als reiner Dummy- oder REST-Modus. |
| Gesamtleistung | Gesamte vom EMS-ESP gemeldete elektrische Leistung. | Die Summe der drei virtuellen Geräte muss hiermit konsistent sein. |
| Warmwasseranteil | Anteil der Gesamtleistung, der dem Warmwasser zugeordnet wird. | Wird explizit vom Heizungsanteil getrennt. |
| Zusatzheizeranteil | Anteil der elektrischen Zusatzheizung. | Dient als eigenständiges Gerät im D-Bus. |
| Betriebsmodus | Zustandskategorie wie `heating`, `dhw`, `defrost`, `cooling`, `standby`. | Nicht identisch mit einfach nur `on/off`; beschreibt den aktuellen Heizungszustand. |

## Verweise

- [AGENT.md](../AGENT.md) §2 und §3
- [Projekt_context.md](../Projekt_context.md)
- [dbus_emsesp/model.py](../dbus_emsesp/model.py)
- [dbus_emsesp/distributor.py](../dbus_emsesp/distributor.py)
