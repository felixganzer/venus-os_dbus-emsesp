# Venus OS EMS-ESP: Endnutzer-Anleitung

Stand: 2026-11-14
Pflege: bei jeder Änderung am Bedienablauf, der Installation, der Oberfläche oder dem Betriebsmodell.

====== Installieren ======

1. Das Repository auf dem Zielsystem klonen und in den gewünschten Ordner ziehen.
2. Die Skripte ausführbar machen:
   - `chmod +x *.sh service/run test_three_devices.py`
3. Das Installationsskript ausführen:
   - `sh install.sh`
4. Die Konfiguration in [config/config.json](../../config/config.json) prüfen.
5. Den Dienst neu starten oder über den service/run-Prozess starten.

====== Erststart ======

- Standardmodus ist `rest_with_dummy_fallback`.
- Für echte Daten muss `mode` in `config/config.json` auf `rest` gesetzt werden.
- `base_url` und optionales `access_token` müssen auf die EMS-ESP-Instanz verweisen.
- Die drei D-Bus-Services werden für Heizung, Warmwasser und Zusatzheizer publiziert.

====== Betrieb ======

- Das Projekt liest EMS-ESP-Daten regelmäßig ab.
- Die Gesamtleistung wird auf drei Geräte verteilt.
- Warmwasser und Heizung werden getrennt ausgewiesen.
- Die Zusatzheizung wird getrennt als eigener Bereich veröffentlicht.

====== Fehlersuche ======

- Wenn keine Daten aus EMS-ESP kommen, prüfe den `mode` in [config/config.json](../../config/config.json).
- Wenn der Fallback aktiviert ist, prüfe die `fallback`-Einstellungen.
- Überprüfe das Log und die EMS-ESP-Endpunkte im JSON-Config.
- Nutze die Testdateien im Repository, um die Verteilungslogik gezielt zu prüfen.

====== Häufige Fragen ======

**Welche drei Geräte werden veröffentlicht?**
Heizung, Warmwasser und Zusatzheizer.

**Warum erscheint Warmwasser separat?**
Weil der Projektkontext die Trennung zwischen Heizungs- und Warmwasseranteil explizit modelliert.

**Warum passt die Summe der Geräte zur Gesamtleistung?**
Weil die Verteilung in [dbus_emsesp/distributor.py](../../dbus_emsesp/distributor.py) keine Doppelzählung zulässt.

====== Änderungsprotokoll ======

- 2026-11-14: Initiale Projekt- und Betriebsdokumentation angelegt.

## Verweise

- [README.md](../../README.md)
- [AGENT.md](../../AGENT.md)
- [Projekt_context.md](../../Projekt_context.md)
