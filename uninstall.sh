#!/bin/sh
set -eu
SERVICE=/service/dbus-emsesp
RC=/data/rc.local
BEGIN="# BEGIN venus-os_dbus-emsesp"
END="# END venus-os_dbus-emsesp"
command -v svc >/dev/null 2>&1 && svc -d "$SERVICE" || true
rm -f "$SERVICE"
if [ -f "$RC" ]; then
    awk -v b="$BEGIN" -v e="$END" '$0==b {skip=1; next} $0==e {skip=0; next} !skip {print}' "$RC" > /tmp/rc.local.emsesp
    cp /tmp/rc.local.emsesp "$RC"
    chmod +x "$RC"
fi
echo "Service removed; counters remain under /data/venus-os_dbus-emsesp/state."
