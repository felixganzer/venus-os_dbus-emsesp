#!/bin/sh
set -eu
APP=/data/venus-os_dbus-emsesp
SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ "$SOURCE" = "$APP" ] || { rm -rf "$APP"; mkdir -p "$APP"; cp -R "$SOURCE"/. "$APP"/; }
chmod +x "$APP/service/run" "$APP/install.sh" "$APP/uninstall.sh"
if ! python3 -c 'import dbus; from gi.repository import GLib' >/dev/null 2>&1; then
  echo "Fehler: Venus-OS-Pythonmodule dbus/gi fehlen." >&2; exit 1
fi
if ! find /opt/victronenergy /data/velib_python "$APP/lib/velib_python" -name vedbus.py -print -quit 2>/dev/null | grep -q .; then
  echo "Fehler: velib_python/vedbus.py nicht gefunden." >&2
  echo "Lege velib_python unter $APP/lib/velib_python ab." >&2
  exit 1
fi
rm -f /service/dbus-emsesp
ln -s "$APP/service" /service/dbus-emsesp
sleep 2
sv status /service/dbus-emsesp || true
echo "Installiert. Konfiguration: $APP/config/config.json"
