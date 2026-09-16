# Venus OS EMS-ESP Bridge

Ein nativer Venus-OS D-Bus Treiber zur Integration einer Bosch Wärmepumpe über EMS-ESP.

Der Treiber liest Daten über die REST-API von EMS-ESP und veröffentlicht diese als D-Bus-Service auf Venus OS.

Aktuell unterstützt:

- Außentemperatur
- Vorlauftemperatur
- Rücklauftemperatur
- Warmwassertemperatur
- Wärmepumpenstatus
- Verdichterstatus
- Leistungsaufnahme
- COP

Zusätzlich ist ein vollständiger Dummy-Modus vorhanden, um die Entwicklung ohne EMS-ESP Hardware durchführen zu können.

---

## Features

✅ REST-Anbindung an EMS-ESP

✅ Native Venus OS D-Bus Integration

✅ Dummy-Datenmodus

✅ Automatischer Dienststart über daemontools

✅ Konfigurierbares Mapping

✅ Diagnosepfade

✅ Raspberry Pi / Venus OS kompatibel

---

## Projektstruktur

```text
venus-os_dbus-emsesp
│
├── config
│   └── config.json
│
├── dbus_emsesp
│   ├── main.py
│   ├── emsesp.py
│   ├── dummy.py
│   └── mapping.py
│
├── service
│   └── run
│
├── install.sh
├── uninstall.sh
├── test_dummy.py
└── README.md
```

---

## Dummy-Modus

Standardmäßig läuft das Projekt im Dummy-Modus.

In der Datei:

```json
{
  "mode": "dummy"
}
```

werden realistische Wärmepumpendaten simuliert.

Folgende Betriebszustände werden automatisch durchlaufen:

- Defrost
- Heating
- DHW
- Standby

---

## Dummy-Modus testen

Ohne D-Bus:

```bash
python3 test_dummy.py
```

Beispielausgabe:

```json
{
  "heatpump": {
    "status": "heating",
    "power": 1850,
    "cop": 4.2
  }
}
```

---

## Installation auf Venus OS

# Auf Venus OS / Raspberry anmelden
ssh root@IP-DEINES-RASPBERRY

wget -O - https://raw.githubusercontent.com/felixganzer/venus-os_dbus-emsesp/main/setup.sh | sh

---

## D-Bus prüfen

Verfügbare Werte:

```bash
dbus -y com.victronenergy.heatpump.emsesp
```

Beispielsweise:

```text
/Temperatures/Outside
/Temperatures/Flow
/Temperatures/Return
/Temperatures/Dhw

/HeatPump/Power
/HeatPump/Cop
/HeatPump/Status
```

---

## Wechsel auf EMS-ESP

Datei:

```json
config/config.json
```

anpassen:

```json
{
  "mode": "rest",

  "ems_esp": {
    "base_url": "http://192.168.178.50",
    "access_token": ""
  }
}
```

Danach Dienst neu starten:

```bash
sv restart /service/dbus-emsesp
```

---

## Unterstützte Hardware

Getestet für:

- Bosch Compress 5800i
- EMS-ESP v3.x

---

## Lizenz

MIT License