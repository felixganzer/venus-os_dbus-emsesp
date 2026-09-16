# Venus OS EMS-ESP: drei virtuelle Wärmepumpengeräte

Ein Prozess fragt EMS-ESP einmal ab und veröffentlicht drei getrennte `com.victronenergy.heatpump`-Dienste:

- Bosch 5800i Heizung, DeviceInstance 280
- Bosch 5800i Warmwasser, DeviceInstance 281
- Bosch 5800i Heizstab, DeviceInstance 282

Die Leistungen überlappen nicht. Der Heizstab wird von der Gesamtleistung abgezogen, bevor der verbleibende Verdichteranteil Heizung oder Warmwasser zugeordnet wird.

## Installation

```sh
cd /data
git clone https://github.com/felixganzer/venus-os_dbus-emsesp.git
cd venus-os_dbus-emsesp
chmod +x *.sh service/run test_three_devices.py
sh install.sh
```

## Prüfen

```sh
python3 test_three_devices.py
dbus -y com.victronenergy.heatpump.emsesp_heating
dbus -y com.victronenergy.heatpump.emsesp_dhw
dbus -y com.victronenergy.heatpump.emsesp_aux
```

## Dummy und REST

Standard ist `"mode": "dummy"`. Für EMS-ESP in `config/config.json` auf `"rest"` wechseln, URL und optional JWT setzen und danach den Dienst neu starten.

## Zuordnungsregel

Warmwasser-Modi werden dem Warmwassergerät zugeordnet. Alle übrigen Verdichteranteile, einschließlich Abtauen und unbekannter Zustände, landen bei Heizung. Dadurch entspricht die Summe der drei Geräte stets der gemeldeten Gesamtleistung.
