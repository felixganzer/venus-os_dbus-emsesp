#!/bin/sh
set -eu
APP=/data/venus-os_dbus-emsesp
SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SERVICE=/service/dbus-emsesp
RC=/data/rc.local
BEGIN="# BEGIN venus-os_dbus-emsesp"
END="# END venus-os_dbus-emsesp"

if [ "$SOURCE" != "$APP" ]; then
    SAVED_CONFIG=/tmp/venus-os_dbus-emsesp-config.json
    [ ! -f "$APP/config/config.json" ] || cp "$APP/config/config.json" "$SAVED_CONFIG"
    rm -rf "$APP"
    mkdir -p "$APP"
    cp -R "$SOURCE"/. "$APP"/
    [ ! -f "$SAVED_CONFIG" ] || cp "$SAVED_CONFIG" "$APP/config/config.json"
fi
chmod +x "$APP/service/run" "$APP/install.sh" "$APP/uninstall.sh" "$APP/setup.sh" "$APP/test_three_devices.py"
mkdir -p /service "$APP/state"
rm -f "$SERVICE"
ln -s "$APP/service" "$SERVICE"

# Managed block is written before any existing exit 0.
TMP=/tmp/rc.local.emsesp
{
    echo '#!/bin/sh'
    echo "$BEGIN"
    echo 'mkdir -p /service'
    echo 'if [ ! -L /service/dbus-emsesp ]; then'
    echo '    rm -f /service/dbus-emsesp'
    echo '    ln -s /data/venus-os_dbus-emsesp/service /service/dbus-emsesp'
    echo 'fi'
    echo "$END"
    if [ -f "$RC" ]; then
        awk -v b="$BEGIN" -v e="$END" '
            NR==1 && $0 ~ /^#!/ {next}
            $0==b {skip=1; next}
            $0==e {skip=0; next}
            !skip {print}
        ' "$RC"
    fi
} > "$TMP"
cp "$TMP" "$RC"
chmod +x "$RC"

command -v svc >/dev/null 2>&1 && svc -u "$SERVICE" || true
sleep 2
command -v svstat >/dev/null 2>&1 && svstat "$SERVICE" || true
echo "Installed three devices: instances 280, 281 and 282"
