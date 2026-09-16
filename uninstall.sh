#!/bin/sh
set -eu
[ ! -e /service/dbus-emsesp ] || sv down /service/dbus-emsesp || true
rm -f /service/dbus-emsesp
echo "Dienst entfernt. Projektdaten unter /data/venus-os_dbus-emsesp bleiben erhalten."
