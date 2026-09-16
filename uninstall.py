#!/bin/sh

set -eu

svc -d /service/dbus-emsesp 2>/dev/null || true

rm -f /service/dbus-emsesp

sed -i '/venus-os_dbus-emsesp/,+5d' /data/rc.local 2>/dev/null || true

echo "venus-os_dbus-emsesp removed"