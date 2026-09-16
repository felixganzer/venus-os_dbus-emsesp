#!/bin/sh

set -eu

APP=/data/venus-os_dbus-emsesp

echo "======================================"
echo "Installing venus-os_dbus-emsesp"
echo "======================================"

# Dateien ausführbar setzen
chmod +x "$APP/service/run" 2>/dev/null || true
chmod +x "$APP/install.sh" 2>/dev/null || true
chmod +x "$APP/uninstall.sh" 2>/dev/null || true
chmod +x "$APP/test_dummy.py" 2>/dev/null || true

#
# Service einrichten
#
rm -f /service/dbus-emsesp

ln -s \
    "$APP/service" \
    /service/dbus-emsesp

#
# Nach Firmware-Updates wiederherstellen
#
touch /data/rc.local

if ! grep -q "venus-os_dbus-emsesp" /data/rc.local ; then

cat >> /data/rc.local << 'EOF'

# venus-os_dbus-emsesp
if [ ! -L /service/dbus-emsesp ]; then
    ln -sf \
        /data/venus-os_dbus-emsesp/service \
        /service/dbus-emsesp
fi

EOF

fi

#
# Dienst starten
#
if command -v svc >/dev/null 2>&1 ; then
    svc -u /service/dbus-emsesp || true
fi

sleep 2

#
# Status anzeigen
#
if command -v svstat >/dev/null 2>&1 ; then
    svstat /service/dbus-emsesp || true
fi

echo ""
echo "Installation completed"
echo ""
echo "D-Bus prüfen:"
echo "dbus -y com.victronenergy.heatpump.emsesp"
